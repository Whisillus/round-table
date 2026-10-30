---
name: cute-copy
description: Use when the user asks about C++ CuTe copy, cute::copy, copy_if, Copy_Atom, Copy_Traits, TiledCopy, ThrCopy, make_tiled_copy, make_cotiled_copy, make_tiled_copy_A/B/C/S/D, partition_S, partition_D, retile_S, retile_D, cp.async, LDSM, or TMA copy setup.
---

# CuTe C++ Copy

Build copy code in this order: choose a copy operation or default copy path, create a `Copy_Atom` when an explicit instruction/access strategy is needed, then create a `TiledCopy` when tiled thread/value partitioning is needed.

## Copy Algorithms

- Use `copy(src, dst)` for generic tensor copies; CuTe dispatches based on tensor type, layout, and memory-space tags.
- Use `copy(copy_atom_or_tiled_copy, src, dst)` when the copy operation must be explicit.
- Use `copy_if(pred, src, dst)` for predicated generic copies.
- Use `copy_if(copy_atom_or_tiled_copy, pred, src, dst)` for predicated explicit copies.
- Copy behavior can be sequential, parallel, vectorized, or asynchronous depending on the selected types; always account for the synchronization required by the chosen operation.
- If a copy writes shared memory cooperatively, synchronize before consumers read it. For non-bulk `cp.async`, use `cp_async_fence()` and `cp_async_wait<N>()` as required, then the appropriate CTA sync before ordinary SMEM consumers read.

```c++
copy(src, dst);
copy_if(pred, src, dst);

copy(tiled_copy, thr_src, thr_dst);
copy_if(tiled_copy, thr_pred, thr_src, thr_dst);
```

### Predicated Copy

- Build predicate tensors from identity/coordinate tensors tiled and partitioned like the data.
- Keep predicate tensor shape congruent with the partitioned copy tensors.
- For `copy_if(tiled_copy, pred, src, dst)`, partition the predicate through the same thread slice as the source or destination.
- Use stride-0 predicate layouts only when intentionally broadcasting a predicate across a mode.

```c++
Tensor coords = make_identity_tensor(shape(S));
Tensor tile_C = local_tile(coords, block_shape, block_coord);
Tensor tC = thr_copy.partition_S(tile_C);
Tensor tP = make_tensor<bool>(shape(tC));

CUTE_UNROLL
for (int i = 0; i < size(tP); ++i) {
  tP(i) = elem_less(tC(i), shape(S));
}

copy_if(tiled_copy, tP, tS, tD);
```

## Copy Operations

Choose the operation family before constructing a `Copy_Atom`, unless the generic `copy(...)` overload is sufficient.

### SIMT Copy Operations

- Use `UniversalCopy<S, D>` for plain assignment/vectorized copy paths where `S` and `D` are the source and destination access types; `UniversalCopy<T>` uses the same access type for both.
- Use `DefaultCopy` when code should not assume pointer alignment or dynamic-stride alignment.
- Use `AutoVectorizingCopy` when local code intentionally asks CuTe to infer vector width from alignment/layout constraints.
- Use `AutoCopyAsync` as an algorithm policy with `copy(AutoCopyAsync{}, src, dst)` or `copy_if(AutoCopyAsync{}, pred, src, dst)`; it is not a `Copy_Atom` operation with `Copy_Traits`.

```c++
auto scalar_op = UniversalCopy<float>{};
auto vector_op = UniversalCopy<uint128_t>{};
auto default_op = DefaultCopy{};
auto vectorizing_op = AutoVectorizingCopy{};
```

### cp.async Copy Operations

- Use `SM80_CP_ASYNC_CACHEALWAYS<T>` for non-bulk asynchronous GMEM-to-SMEM copies that cache at all levels; `T` must be 4, 8, or 16 bytes.
- Use `SM80_CP_ASYNC_CACHEGLOBAL<T>` for non-bulk asynchronous GMEM-to-SMEM copies that cache at global/L2 level; `T` must be 16 bytes.
- Use `SM80_CP_ASYNC_CACHEALWAYS_ZFILL<T>` or `SM80_CP_ASYNC_CACHEGLOBAL_ZFILL<T>` only when the copy path is explicitly designed around zero-fill predication.
- These operations name the access type. The `Copy_Atom` second parameter still names the logical value type.

```c++
auto cp_async_ca = SM80_CP_ASYNC_CACHEALWAYS<uint128_t>{};
auto cp_async_cg = SM80_CP_ASYNC_CACHEGLOBAL<uint128_t>{};
auto cp_async_zfill = SM80_CP_ASYNC_CACHEALWAYS_ZFILL<uint128_t>{};
```

### SM90 Bulk Copy Operations

- Use `SM90_BULK_COPY_G2S` for byte-bulk GMEM-to-SMEM copies that use an mbarrier completion mechanism.
- Use `SM90_BULK_COPY_S2G` for byte-bulk SMEM-to-GMEM copies that use the bulk-group commit/wait mechanism.
- Use `SM90_BULK_COPY_AUTO` when the code should dispatch to G2S or S2G from the source and destination memory spaces.
- Bulk copy traits carry the transaction width as a static bit count, and G2S bulk loads require `.with(mbarrier)` before use.

```c++
using BulkG2S = Copy_Atom<Copy_Traits<SM90_BULK_COPY_G2S, _128>, half_t>;
using BulkS2G = Copy_Atom<Copy_Traits<SM90_BULK_COPY_S2G, _128>, half_t>;

auto bulk_auto = Copy_Traits<SM90_BULK_COPY_AUTO>{};
auto bulk_auto_with_mbar = Copy_Traits<SM90_BULK_COPY_AUTO>{}.with(bulk_mbar);
```

### TMA Copy Operations

- Use `SM90_TMA_LOAD` for descriptor-based bulk tensor GMEM-to-SMEM loads.
- Use `SM90_TMA_LOAD_MULTICAST` for multicast TMA loads when the cluster mapping requires it.
- Use `SM90_TMA_STORE` for descriptor-based bulk tensor SMEM-to-GMEM stores.
- Use `SM90_TMA_LOAD_IM2COL`, `SM90_TMA_LOAD_IM2COL_MULTICAST`, or `SM90_TMA_STORE_IM2COL` for im2col TMA paths.
- Build executable TMA atoms with `make_tma_atom(...)`; do not pass TMA operation structs directly to plain `Copy_Atom<...>` construction.

```c++
auto tma_load = SM90_TMA_LOAD{};
auto tma_mcast = SM90_TMA_LOAD_MULTICAST{};
auto tma_store = SM90_TMA_STORE{};
auto tma_im2col = SM90_TMA_LOAD_IM2COL{};
```

### Warp Matrix Copy Operations

- Use LDSM operations for shared-to-register matrix-fragment loads that feed MMA operands.
- Common normal-layout forms are `SM75_U32x1_LDSM_N`, `SM75_U32x2_LDSM_N`, and `SM75_U32x4_LDSM_N`.
- Common transpose forms are `SM75_U16x2_LDSM_T`, `SM75_U16x4_LDSM_T`, and `SM75_U16x8_LDSM_T`.
- Use `SM75_U32x1_MOVM_T` only for the specific move-matrix transpose path it represents.

```c++
auto ldsm_x4 = SM75_U32x4_LDSM_N{};
auto ldsm_t = SM75_U16x4_LDSM_T{};
```

## Copy Traits

- `Copy_Traits<CopyOperation, Args...>` describes how a copy operation maps logical threads and values to source, destination, and reference bit layouts.
- `Copy_Atom<CopyOperation, CopyInternalType>` normalizes through `Copy_Traits<CopyOperation>` before recasting those bit layouts into `CopyInternalType` values.
- Use the operation form, such as `Copy_Atom<UniversalCopy<uint128_t>, half_t>`, for ordinary stateless operations.
- Use explicit `Copy_Traits<...>` when the operation needs extra static or runtime arguments, such as SM90 bulk-copy bit width, TMA descriptors, barriers, predicates, or multicast masks.
- Traits may provide `.with(...)` to attach runtime support state and return a new traits or atom object ready for the copy call.

Common trait members:

- `ThrID`: logical thread-id layout for the copy operation.
- `SrcLayout`: source `(thread,value) -> bit` layout.
- `DstLayout`: destination `(thread,value) -> bit` layout.
- `RefLayout`: reference `(thread,value) -> bit` layout used by `Copy_Atom`.

```c++
using DirectAtom = Copy_Atom<UniversalCopy<uint128_t>, half_t>;

using BulkTraits = Copy_Traits<SM90_BULK_COPY_G2S, _128>;
using BulkAtom = Copy_Atom<BulkTraits, half_t>;

auto executable_bulk_atom = BulkAtom{}.with(bulk_mbar);
```

## Copy Atom Construction

`Copy_Atom<CopyOperation, CopyInternalType>` always takes:

- `CopyOperation`: the copy operation or `Copy_Traits<...>`, such as `UniversalCopy<uint128_t>`, `SM80_CP_ASYNC_CACHEALWAYS<uint128_t>`, `SM75_U32x4_LDSM_N`, or `Copy_Traits<SM90_BULK_COPY_G2S, _128>`.
- `CopyInternalType`: the logical value type used as `ValType` when recasting the operation's bit layouts, such as `half_t`, `float`, or a kernel element type alias.

Construction notes:

- Use empty construction for stateless copy operations and traits.
- Use `.with(...)` when the traits require runtime support arguments such as a zero-fill predicate, TMA barrier, bulk-copy mbarrier, or multicast mask.
- The operation can name a vector/access type such as `uint128_t`; the atom's second parameter still names the logical value type.
- Match the operation's access type, tensor alignment, and partition shape. A mismatch often fails at compile time, but alignment mistakes can become runtime memory faults.

```c++
using Atom = Copy_Atom<UniversalCopy<uint128_t>, half_t>;

Copy_Atom<SM80_CP_ASYNC_CACHEALWAYS<uint128_t>, half_t> g2s_atom;
Copy_Atom<SM75_U32x4_LDSM_N, half_t> s2r_atom;

using BulkTraits = Copy_Traits<SM90_BULK_COPY_G2S, _128>;
auto bulk_atom = Copy_Atom<BulkTraits, half_t>{}.with(bulk_mbar);
```

## Tiled Copy

Use tiled copy construction after choosing or constructing the copy atom.

### Tiled Copy Construction

- Always create the `Copy_Atom` first, then pass the atom to tiled-copy construction.
- Do not pass a copy operation such as `UniversalCopy<uint128_t>{}` or `SM75_U32x4_LDSM_N{}` directly to `make_tiled_copy(...)`, `make_tiled_copy_A(...)`, `make_tiled_copy_B(...)`, or `make_tiled_copy_C(...)`.
- Use `make_tiled_copy(copy_atom, thr_layout, val_layout)` when assigning copy work across a thread layout and per-thread value layout.
- `thr_layout` maps tile coordinates to thread indices, for example `(m,n) -> thr_idx`.
- `val_layout` maps tile coordinates to per-thread value indices, for example `(m,n) -> val_idx`; it defaults to `Layout<_1>{}`.
- `make_tiled_copy(...)` uses a raked product of `thr_layout` and `val_layout` to form the thread/value mapping and tiler.
- Use `make_cotiled_copy(copy_atom, atom_tv_layout, data_layout)` when the atom thread/value layout is expressed as offsets into a target data layout.
- Use `make_tiled_copy_A/B/C(copy_atom, tiled_mma)` when a copy must match a `TiledMMA` operand or accumulator thread/value layout.
- Use `make_tiled_copy_S/D(copy_atom, existing_tiled_copy)` when a new atom must reuse an existing tiled copy's source or destination TV layout.

```c++
using Atom = Copy_Atom<UniversalCopy<uint128_t>, half_t>; // 128-bit access, logical half_t values

Layout thr_layout = make_layout(make_shape(_32{}, _8{})); // shape: (_32,_8), 256 thread slots
Layout val_layout = make_layout(make_shape(_8{}, _1{}));  // shape: (_8,_1), 8 half_t values per thread

TiledCopy tiled_copy = make_tiled_copy(Atom{}, thr_layout, val_layout); // tile: (_256,_8), TV shape: (_256,(_8,_1))
TiledCopy tiled_copy_A = make_tiled_copy_A(Atom{}, tiled_mma);          // TV layout matches tiled_mma A
```

### Thread Copy Slices

- Use `tiled_copy.get_slice(threadIdx.x)` or `get_thread_slice(threadIdx.x)` to get a `ThrCopy` for the current thread.
- Use `thr_copy.partition_S(src)` and `thr_copy.partition_D(dst)` to create source and destination thread partitions.
- Use `thr_copy.retile_S(tensor)` and `thr_copy.retile_D(tensor)` when retile views are needed, commonly for shared-to-register copy paths aligned to an MMA partition.

```c++
ThrCopy thr_copy = tiled_copy.get_slice(threadIdx.x); // one thread's slice of tiled_copy

Tensor tS = thr_copy.partition_S(tile_S); // source partition owned by this thread
Tensor tD = thr_copy.partition_D(tile_D); // destination partition owned by this thread

copy(tiled_copy, tS, tD); // issues the tiled copy over all thread/value partitions
```

## Operation-Specific Usage

Use these sections for synchronization, descriptor setup, and retile details after selecting the operation and atom.

### cp.async Copy Protocol

- End a group of issued non-bulk `cp.async` operations with `cp_async_fence()`.
- Use `cp_async_wait<N>()` to wait until at most `N` groups remain in flight; use `cp_async_wait<0>()` before consuming final copied data.
- Follow `cp_async_wait<N>()` with the CTA synchronization needed for all consumer threads to observe SMEM writes.

```c++
copy(copy_a, tAgA(_,_,_,k_tile), tAsA(_,_,_,pipe));
copy(copy_b, tBgB(_,_,_,k_tile), tBsB(_,_,_,pipe));
cp_async_fence();

cp_async_wait<0>();
__syncthreads();
```

### TMA Atom And Copy

- TMA is descriptor- and coordinate-based. A TMA instruction consumes a descriptor pointer, an SMEM pointer, and coordinates into the descriptor's GMEM tensor; it does not consume ordinary GMEM pointers in the kernel.
- Construct a TMA atom on the host side with `make_tma_atom(copy_op, gtensor, smem_layout, cta_tiler, cluster_size)`.
- Inside the kernel, use `tma_atom.get_tma_tensor(shape)` to create the descriptor-coordinate tensor.
- Use `tma_partition(tma_atom, cta_coord, cta_layout, smem_tensor, gmem_tma_tensor)` for custom multicast/CTA layouts, or the shorter overload when no multicast mapping is needed.
- Issue TMA copies with the barrier-bound atom, for example `copy(tma_atom.with(barrier), tma_gmem_tile, tma_smem_tile)`.
- Compute and set transaction bytes correctly before issuing TMA loads; missing or wrong transaction byte counts can hang consumers.

```c++
auto tma_atom = make_tma_atom(SM90_TMA_LOAD{}, mA, sA_layout, cta_tiler);

Tensor mA_tma = tma_atom.get_tma_tensor(make_shape(M, K));
Tensor gA = local_tile(mA_tma, cta_tiler, cta_coord, Step<_1, X,_1>{});

auto [tAgA, tAsA] = tma_partition(
    tma_atom,
    _0{},
    Layout<_1>{},
    group_modes<0,2>(sA),
    group_modes<0,2>(gA));

copy(tma_atom.with(producer_barrier), tAgA(_, k_tile), tAsA(_, pipe));
```

### Warp Matrix Copy Usage

- Use LDSM copy atoms for shared-to-register matrix-fragment loads that feed MMA operands.
- Retile LDSM destinations to existing MMA fragments with `retile_D(...)` when the copy path is tied to a `TiledMMA` operand layout.
- Verify source SMEM layout, swizzle, alignment, and MMA operand expectation together; LDSM legality is layout-dependent.

```c++
Copy_Atom<SM75_U32x4_LDSM_N, half_t> s2r_atom_A;
TiledCopy s2r_copy_A = make_tiled_copy_A(s2r_atom_A, mma);

ThrCopy s2r_thr_copy_A = s2r_copy_A.get_slice(threadIdx.x);
Tensor tXsA = s2r_thr_copy_A.partition_S(sA);
Tensor tXrA = s2r_thr_copy_A.retile_D(tCrA);

copy(s2r_copy_A, tXsA(_,_,_,pipe), tXrA);
```
