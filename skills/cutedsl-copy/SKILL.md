---
name: cutedsl-copy
description: Use when the user asks about CuTe DSL copy, tiled copy, copy atoms, make_tiled_copy_tv, make_layout_tv, partition_S, partition_D, or copy TV layouts.
---

# CuTe DSL Copy

Build copy code in this order: choose a copy operation descriptor, create a copy atom, then create a tiled copy when a tiled TV mapping is needed.

## SIMT Copy Op

Use these ops for thread-level SIMT copies between global, shared, and register storage.

- `cute.nvgpu.CopyUniversalOp`: plain assignment-style copy.
- `cute.nvgpu.CopyG2ROp`: global -> register.
- `cute.nvgpu.CopyR2GOp`: register -> global.
- `cute.nvgpu.CopyS2ROp`: shared -> register.
- `cute.nvgpu.CopyR2SOp`: register -> shared.
- These op constructors take no op-specific arguments in current CuTe DSL; pass copy width, memory ordering, scope, and cache hints to `cute.make_copy_atom(...)`.

Op inputs:

- `cute.nvgpu.CopyUniversalOp()`: no inputs.
- `cute.nvgpu.CopyG2ROp()`: no inputs.
- `cute.nvgpu.CopyR2GOp()`: no inputs.
- `cute.nvgpu.CopyS2ROp()`: no inputs.
- `cute.nvgpu.CopyR2SOp()`: no inputs.

```python
copy_op = cute.nvgpu.CopyUniversalOp()
copy_op = cute.nvgpu.CopyG2ROp()
copy_op = cute.nvgpu.CopyR2GOp()
copy_op = cute.nvgpu.CopyS2ROp()
copy_op = cute.nvgpu.CopyR2SOp()
```

## cp.async Copy Op

Use `cute.nvgpu.cpasync.CopyG2SOp` for non-bulk asynchronous global-to-shared copies.

- `CopyG2SOp` is GMEM -> SMEM only.
- `CopyG2SOp` takes only `cache_mode` as an op constructor argument.
- Pass only `num_bits_per_copy` when creating the copy atom; do not pass `memory_order` or `memory_scope` for non-bulk `cp.async`.
- Use `cute.arch.cp_async_commit_group()` to commit issued `cp.async` copies.
- Use `cute.arch.cp_async_wait_group(n)` to wait until at most `n` committed groups remain in flight; use `cute.arch.cp_async_wait_group(0)` before consuming the copied SMEM data.
- Follow the wait with the CTA, warp, or pipeline synchronization needed by the consumers before they read SMEM through ordinary loads.

Op inputs:

- `cute.nvgpu.cpasync.CopyG2SOp(cache_mode=cute.nvgpu.LoadCacheMode.ALWAYS)`.

### Cache Mode

- Use `cute.nvgpu.LoadCacheMode`, not the deprecated `cute.nvgpu.cpasync.LoadCacheMode`, for new code.
- PTX non-bulk `cp.async` documents `.ca` and `.cg`; prefer `ALWAYS` or `GLOBAL` for `CopyG2SOp` unless the backend behavior of another mode has been verified.
- `cute.nvgpu.LoadCacheMode.ALWAYS`: `.ca`, cache at all levels, including L1 and L2.
- `cute.nvgpu.LoadCacheMode.GLOBAL`: `.cg`, cache only at global/L2 level and bypass L1; common for `cp.async`.
- `cute.nvgpu.LoadCacheMode.STREAMING`: `.cs`, evict-first streaming load hint for data likely used once; generic load mode, not a documented PTX non-bulk `cp.async` cache operator.
- `cute.nvgpu.LoadCacheMode.LAST_USE`: `.lu`, last-use load hint; generic load mode, not a documented PTX non-bulk `cp.async` cache operator.
- `cute.nvgpu.LoadCacheMode.NONE`: no explicit cache operator; use backend/default behavior.

```python
copy_op = cute.nvgpu.cpasync.CopyG2SOp(cache_mode=cute.nvgpu.LoadCacheMode.GLOBAL)
copy_atom = cute.make_copy_atom(copy_op, dtype, num_bits_per_copy=128)
```

## cp.async Bulk Copy Op

Use byte bulk cp.async ops for SM90+ bulk asynchronous copies that are not tensor-descriptor TMA atoms.

- `cute.nvgpu.cpasync.CopyBulkG2SOp`: byte bulk GMEM -> SMEM copy.
- `cute.nvgpu.cpasync.CopyBulkG2SMulticastOp`: byte bulk GMEM -> SMEM multicast copy.
- `cute.nvgpu.cpasync.CopyBulkS2GOp`: byte bulk SMEM -> GMEM copy.
- `cute.nvgpu.cpasync.CopyBulkS2GByteMaskOp`: byte bulk SMEM -> GMEM copy with a 16-bit byte mask; SM100+.
- `cute.nvgpu.cpasync.CopyBulkS2SOp`: byte bulk CTA SMEM -> cluster SMEM copy.
- `cute.nvgpu.cpasync.CopyDsmemStoreOp`: asynchronous RMEM -> DSMEM store.
- These ops take no op constructor inputs.

```python
copy_op = cute.nvgpu.cpasync.CopyBulkG2SOp()
copy_atom = cute.make_copy_atom(copy_op, dtype, num_bits_per_copy=0)

copy_op = cute.nvgpu.cpasync.CopyBulkS2GOp()
copy_atom = cute.make_copy_atom(copy_op, dtype, num_bits_per_copy=0)

copy_op = cute.nvgpu.cpasync.CopyBulkS2SOp()
copy_atom = cute.make_copy_atom(copy_op, dtype, num_bits_per_copy=0)

copy_op = cute.nvgpu.cpasync.CopyDsmemStoreOp()
copy_atom = cute.make_copy_atom(copy_op, dtype, num_bits_per_copy=0)
```

## TMA Op

Use TMA copy ops for descriptor-based bulk tensor copies between GMEM and SMEM.

- `cute.nvgpu.cpasync.CopyBulkTensorTileG2SOp`: tiled bulk tensor GMEM -> SMEM load.
- `cute.nvgpu.cpasync.CopyBulkTensorTileG2SMulticastOp`: tiled bulk tensor GMEM -> SMEM multicast load.
- `cute.nvgpu.cpasync.CopyBulkTensorIm2ColG2SOp`: im2col bulk tensor GMEM -> SMEM load.
- `cute.nvgpu.cpasync.CopyBulkTensorIm2ColG2SMulticastOp`: im2col bulk tensor GMEM -> SMEM multicast load.
- `cute.nvgpu.cpasync.CopyBulkTensorTileS2GOp`: tiled bulk tensor SMEM -> GMEM store.
- `cute.nvgpu.cpasync.CopyReduceBulkTensorTileS2GOp`: tiled bulk tensor SMEM -> GMEM reduction store.
- `cute.nvgpu.cpasync.CopyBulkTensorIm2ColS2GOp`: im2col bulk tensor SMEM -> GMEM store.
- Tensor TMA ops require SM90+.
- TMA tensor copy ops are copy-operation descriptors, but they do not use plain `cute.make_copy_atom(...)` atom construction.
- TMA load ops take `cta_group`, which selects the TMA instruction issue form. Use `CtaGroup.ONE` for the one-CTA issue form or `CtaGroup.TWO` for the two-CTA issue form. Prefer `CtaGroup.ONE` unless the kernel is intentionally built around two-CTA TMA; `CtaGroup.TWO` requires SM100+.
- `CopyReduceBulkTensorTileS2GOp` takes `reduction_kind`, which selects the hardware reduction performed while storing from SMEM to GMEM. Use `cute.ReductionKind.ADD`, `MIN`, `MAX`, `INC`, `DEC`, `AND`, `OR`, or `XOR`; `ADD` is the default.
- Plain TMA store ops do not take op constructor inputs.

```python
tma_op = cute.nvgpu.cpasync.CopyBulkTensorTileG2SOp(cta_group=cta_group)
tma_op = cute.nvgpu.cpasync.CopyBulkTensorTileS2GOp()
tma_op = cute.nvgpu.cpasync.CopyReduceBulkTensorTileS2GOp(
    reduction_kind=cute.ReductionKind.ADD
)
tma_op = cute.nvgpu.cpasync.CopyBulkTensorIm2ColS2GOp()
```

## TMA Atom

Use TMA atom helpers to build descriptor-backed TMA atoms from TMA copy ops.

- Create tiled TMA tensor atoms with `cute.nvgpu.cpasync.make_tiled_tma_atom(...)`.
- Create im2col TMA tensor atoms with `cute.nvgpu.cpasync.make_im2col_tma_atom(...)`.
- Do not pass TMA tensor copy ops directly to `cute.make_copy_atom(...)`; construct TMA atoms with TMA-specific helper APIs.
- `make_tiled_tma_atom(...)` and `make_im2col_tma_atom(...)` return `TmaInfo`, which can be unpacked as `tma_atom, tma_tensor`; it also carries `smem_layout`.
- `internal_type` optionally selects an internal TMA data format when the tensor element type does not directly match the TMA copy format.
- `tma_atom` is the TMA copy atom produced from the TMA op, GMEM tensor, SMEM layout, and CTA tiler.
- `tma_tensor` is the descriptor-coordinate tensor returned with the atom; it maps logical GMEM coordinates to coordinates the TMA unit can consume.

Tiled helper inputs:

- `cute.nvgpu.cpasync.make_tiled_tma_atom(op, gmem_tensor, smem_layout, cta_tiler, num_multicast=1, *, internal_type=None)`.
- `op`: TMA copy op descriptor.
- `gmem_tensor`: GMEM tensor used to build the TMA descriptor and returned TMA tensor.
- `smem_layout`: SMEM layout used to construct the TMA atom; may be non-staged or staged.
- `cta_tiler`: CTA-level tiler used to map tensor coordinates into TMA descriptor coordinates.
- `num_multicast`: multicast factor; use `1` for non-multicast G2S ops.
- `internal_type`: optional internal TMA data type.

```python
tma_op = cute.nvgpu.cpasync.CopyBulkTensorTileG2SOp(cta_group=cta_group)
smem_layout = ...
cta_tiler = ...
tma_info = cute.nvgpu.cpasync.make_tiled_tma_atom(
    tma_op,
    gmem_tensor,
    smem_layout,
    cta_tiler,
    num_multicast=num_multicast,
    internal_type=internal_type,
)
tma_atom, tma_tensor = tma_info
```

```python
tma_op = cute.nvgpu.cpasync.CopyBulkTensorTileS2GOp()
smem_layout = ...
cta_tiler = ...
tma_info = cute.nvgpu.cpasync.make_tiled_tma_atom(
    tma_op,
    gmem_tensor,
    smem_layout,
    cta_tiler,
    internal_type=internal_type,
)
tma_atom, tma_tensor = tma_info
```

### TMA Im2Col

Use `cute.nvgpu.cpasync.make_im2col_tma_atom(...)` for im2col TMA atoms.

- `cute.nvgpu.cpasync.make_im2col_tma_atom(op, gmem_tensor, smem_layout, cta_tiler, lower_corner_whd=None, upper_corner_whd=None, lower_padding_whd=None, upper_padding_whd=None, stride_whd=None, lower_srt=None, stride_srt=None, num_multicast=1, *, internal_type=None)`.
- For im2col G2S loads, provide all im2col descriptor tuples: `lower_corner_whd`, `upper_corner_whd`, `lower_padding_whd`, `upper_padding_whd`, `stride_whd`, `lower_srt`, and `stride_srt`.
- Im2col S2G stores do not need the im2col descriptor tuples.
- `lower_corner_whd` and `upper_corner_whd` define the W/H/D input window used by the im2col load.
- `lower_padding_whd` and `upper_padding_whd` define the W/H/D padding region around that input window.
- `stride_whd` defines the convolution stride in W/H/D coordinates.
- `lower_srt` defines the lower S/R/T filter-coordinate corner used by the im2col mapping.
- `stride_srt` defines the S/R/T dilation stride used by the im2col mapping.

```python
tma_op = cute.nvgpu.cpasync.CopyBulkTensorIm2ColG2SOp(cta_group=cta_group)
smem_layout = ...
cta_tiler = ...
tma_info = cute.nvgpu.cpasync.make_im2col_tma_atom(
    tma_op,
    gmem_tensor,
    smem_layout,
    cta_tiler,
    lower_corner_whd=lower_corner_whd,
    upper_corner_whd=upper_corner_whd,
    lower_padding_whd=lower_padding_whd,
    upper_padding_whd=upper_padding_whd,
    stride_whd=stride_whd,
    lower_srt=lower_srt,
    stride_srt=stride_srt,
    num_multicast=num_multicast,
    internal_type=internal_type,
)
tma_atom, tma_tensor = tma_info
```

```python
tma_op = cute.nvgpu.cpasync.CopyBulkTensorIm2ColS2GOp()
smem_layout = ...
cta_tiler = ...
tma_info = cute.nvgpu.cpasync.make_im2col_tma_atom(
    tma_op,
    gmem_tensor,
    smem_layout,
    cta_tiler,
    internal_type=internal_type,
)
tma_atom, tma_tensor = tma_info
```

## Warp Matrix Copy Op

Use these ops for warp-level matrix-fragment copies between shared memory and registers.

- Load family: shared -> register.
  - `cute.nvgpu.warp.LdMatrix8x8x16bOp`: SM75+.
  - `cute.nvgpu.warp.LdMatrix8x16x8bOp`: SM100+.
  - `cute.nvgpu.warp.LdMatrix16x8x8bOp`: SM100+.
  - `cute.nvgpu.warp.LdMatrix16x16x8bOp`: SM100+.
- Store family: register -> shared.
  - `cute.nvgpu.warp.StMatrix8x8x16bOp`: SM90+.
  - `cute.nvgpu.warp.StMatrix16x8x8bOp`: SM100+.

Op inputs:

- `LdMatrix8x8x16bOp(transpose=False, num_matrices=1, unpack_bits=None)`.
- `LdMatrix8x16x8bOp(transpose=False, num_matrices=1, unpack_bits=None)`.
- `LdMatrix16x8x8bOp(transpose=True, num_matrices=2, unpack_bits=None)`.
- `LdMatrix16x16x8bOp(transpose=True, num_matrices=1, unpack_bits=None)`.
- `StMatrix8x8x16bOp(transpose=False, num_matrices=1, unpack_bits=None)`.
- `StMatrix16x8x8bOp(transpose=True, num_matrices=1, unpack_bits=None)`.
- `transpose` is a `bool`.
- `num_matrices` is an `int`; valid values are listed below.
- `unpack_bits` is `None`, `4`, or `6` where supported; store ops and `LdMatrix8x8x16bOp` require `None`.

Valid `num_matrices` values in CuTe DSL:

- `LdMatrix8x8x16bOp`: `1`, `2`, `4`.
- `LdMatrix8x16x8bOp`: `1`, `2`, `4`.
- `LdMatrix16x8x8bOp`: `2`, `4`.
- `LdMatrix16x16x8bOp`: `1`, `2`.
- `StMatrix8x8x16bOp`: `1`, `2`, `4`.
- `StMatrix16x8x8bOp`: `1`, `2`, `4`.

Transpose support in CuTe DSL:

- `LdMatrix8x8x16bOp`: `transpose` is optional.
- `LdMatrix8x16x8bOp`: `transpose` is not supported.
- `LdMatrix16x8x8bOp`: `transpose=True` is required.
- `LdMatrix16x16x8bOp`: `transpose=True` is required.
- `StMatrix8x8x16bOp`: `transpose` is optional.
- `StMatrix16x8x8bOp`: `transpose=True` is required.

```python
load_op = cute.nvgpu.warp.LdMatrix8x8x16bOp(transpose=False, num_matrices=4)
store_op = cute.nvgpu.warp.StMatrix8x8x16bOp(transpose=False, num_matrices=4)
```

## Copy Atom Construction

`cute.make_copy_atom(copy_op, copy_internal_type, **kwargs)` always takes:

- `copy_op`: the copy operation descriptor.
- `copy_internal_type`: the data type used to construct copy TV layouts in units of tensor elements.
- Optional compiler plumbing: `loc`, `ip`; omit in normal code.

Op-specific `cute.make_copy_atom(...)` kwargs for copy ops in this skill:

- `CopyUniversalOp`: `num_bits_per_copy=0`; non-negative `int`; `0` lets the compiler choose best-effort vectorization.
- `CopyG2ROp`: `num_bits_per_copy=0`, `memory_order=MemoryOrder.WEAK`, `memory_scope=MemoryScope.CTA`, `l2_prefetch_size=L2PrefetchSize.NONE`, `l1c_evict_priority=CacheEvictionPriority.EVICT_NORMAL`, `load_cache_mode=LoadCacheMode.ALWAYS`, `shared_space=SharedSpace.CTA`, `invariant=False`.
- `CopyR2GOp`: `num_bits_per_copy=0`, `memory_order=MemoryOrder.WEAK`, `memory_scope=MemoryScope.CTA`, `l1c_evict_priority=CacheEvictionPriority.EVICT_NORMAL`, `store_cache_mode=StoreCacheMode.WRITE_BACK`, `shared_space=SharedSpace.CTA`.
- `CopyS2ROp`: `num_bits_per_copy=0`, `memory_order=MemoryOrder.WEAK`, `memory_scope=MemoryScope.CTA`, `shared_space=SharedSpace.CTA`; rejects other kwargs.
- `CopyR2SOp`: `num_bits_per_copy=0`, `memory_order=MemoryOrder.WEAK`, `memory_scope=MemoryScope.CTA`, `shared_space=SharedSpace.CTA`; rejects other kwargs.
- `cpasync.CopyG2SOp`: requires positive `num_bits_per_copy`; no `memory_order` or `memory_scope`.
- `cpasync.CopyBulkG2SOp`, `cpasync.CopyBulkG2SMulticastOp`, `cpasync.CopyBulkS2GOp`, `cpasync.CopyBulkS2GByteMaskOp`, and `cpasync.CopyBulkS2SOp`: `num_bits_per_copy=0`; non-negative `int`.
- `cpasync.CopyDsmemStoreOp`: `num_bits_per_copy=0`; valid values are `0`, `32`, `64`, and `128`.
- Warp Matrix Copy ops: no op-specific atom kwargs beyond `copy_internal_type`; `transpose`, `num_matrices`, and `unpack_bits` are op constructor inputs.

```python
copy_op = cute.nvgpu.CopyG2ROp()
copy_atom = cute.make_copy_atom(
    copy_op,
    dtype,
    num_bits_per_copy=0,
    memory_order=cute.nvgpu.MemoryOrder.WEAK,
    memory_scope=cute.nvgpu.MemoryScope.CTA,
    l2_prefetch_size=cute.nvgpu.L2PrefetchSize.NONE,
    l1c_evict_priority=cute.nvgpu.CacheEvictionPriority.EVICT_NORMAL,
    load_cache_mode=cute.nvgpu.LoadCacheMode.ALWAYS,
    shared_space=cute.nvgpu.SharedSpace.CTA,
    invariant=False,
)

copy_op = cute.nvgpu.CopyR2GOp()
copy_atom = cute.make_copy_atom(
    copy_op,
    dtype,
    num_bits_per_copy=0,
    memory_order=cute.nvgpu.MemoryOrder.WEAK,
    memory_scope=cute.nvgpu.MemoryScope.CTA,
    l1c_evict_priority=cute.nvgpu.CacheEvictionPriority.EVICT_NORMAL,
    store_cache_mode=cute.nvgpu.StoreCacheMode.WRITE_BACK,
    shared_space=cute.nvgpu.SharedSpace.CTA,
)
```

### Memory Order

- `memory_order` is a `cute.make_copy_atom(...)` kwarg, not a copy-op constructor argument.
- It applies to `CopyG2ROp`, `CopyR2GOp`, `CopyS2ROp`, and `CopyR2SOp` atom construction.
- It does not apply to `CopyUniversalOp` or non-bulk `cp.async` `CopyG2SOp`; `CopyG2SOp` uses `cache_mode` on the op and `num_bits_per_copy` on the atom.
- `memory_order` controls synchronization semantics on supported specialized SIMT copy atoms.
- PTX loads support `.weak`, `.relaxed.scope`, and `.acquire.scope`; stores support `.weak`, `.relaxed.scope`, and `.release.scope`.
- Use `cute.nvgpu.MemoryOrder.WEAK` when ordering is established by another synchronization mechanism.
- Use `cute.nvgpu.MemoryOrder.RELAXED` for atomic/strong memory operations without acquire or release ordering.
- Use `cute.nvgpu.MemoryOrder.ACQUIRE` for load-side acquire ordering.
- Use `cute.nvgpu.MemoryOrder.RELEASE` for store-side release ordering.
- `ACQ_REL`, `SC`, `MMIO`, `CONSTANT`, and `VOLATILE` are exposed enum values; verify the target op and PTX support before using them.

### Memory Scope

- `memory_scope` is a `cute.make_copy_atom(...)` kwarg, not a copy-op constructor argument.
- It applies to `CopyG2ROp`, `CopyR2GOp`, `CopyS2ROp`, and `CopyR2SOp` atom construction.
- It does not apply to `CopyUniversalOp` or non-bulk `cp.async` `CopyG2SOp`; `CopyG2SOp` uses `cache_mode` on the op and `num_bits_per_copy` on the atom.
- `memory_scope` controls which threads can participate in the synchronization semantics requested by `memory_order`.
- `cute.nvgpu.MemoryScope.CTA`: block/CTA scope.
- `cute.nvgpu.MemoryScope.CLUSTER`: cluster scope; requires cluster-capable target support.
- `cute.nvgpu.MemoryScope.GPU`: device scope.
- `cute.nvgpu.MemoryScope.SYS`: system scope.

### L2 Prefetch

- `l2_prefetch_size` is an L2 cache prefetch-size hint for the generated global load; it does not change the actual load width.
- Valid values: `NONE`, `RESERVED`, `SIZE_64B`, `SIZE_128B`, and `SIZE_256B`.
- Prefer `NONE` unless tuning shows an L2 prefetch hint improves the target kernel.

### L1 Eviction Priority

- `l1c_evict_priority` is an L1 cache eviction-priority hint for generated global loads or stores; it does not change the copied value.
- Valid values: `EVICT_NORMAL`, `EVICT_FIRST`, `EVICT_LAST`, `EVICT_UNCHANGED`, and `NO_ALLOCATE`.
- `EVICT_FIRST`: prefer evicting this line earlier.
- `EVICT_LAST`: prefer keeping this line longer.
- `NO_ALLOCATE`: avoid allocating the line in L1.
- `EVICT_UNCHANGED`: preserve the existing cache eviction priority when possible.
- Prefer `EVICT_NORMAL` unless profiling or a known access pattern justifies another hint.

### Generic SIMT Cache Mode

- `load_cache_mode` and `store_cache_mode` are parallel cache-mode hints, but they use separate enums and apply to different copy directions.
- `CopyG2ROp` accepts `load_cache_mode` when creating the copy atom.
- `CopyR2GOp` accepts `store_cache_mode` when creating the copy atom.
- `CopyS2ROp` and `CopyR2SOp` do not accept cache-mode kwargs.
- `cute.nvgpu.LoadCacheMode.ALWAYS`: `.ca`, cache at all levels, including L1 and L2.
- `cute.nvgpu.LoadCacheMode.GLOBAL`: `.cg`, cache only at global/L2 level and bypass L1.
- `cute.nvgpu.LoadCacheMode.STREAMING`: `.cs`, evict-first streaming load hint for data likely used once.
- `cute.nvgpu.LoadCacheMode.LAST_USE`: `.lu`, last-use load hint.
- `cute.nvgpu.LoadCacheMode.NONE`: no explicit load cache operator; use backend/default behavior.
- `cute.nvgpu.StoreCacheMode.WRITE_BACK`: `.wb`, cache write-back at coherent levels.
- `cute.nvgpu.StoreCacheMode.GLOBAL`: `.cg`, cache only at global/L2 level and bypass L1.
- `cute.nvgpu.StoreCacheMode.STREAMING`: `.cs`, evict-first streaming store hint.
- `cute.nvgpu.StoreCacheMode.WRITE_THROUGH`: `.wt`, write-through system-level store behavior.
- `cute.nvgpu.StoreCacheMode.NONE`: no explicit store cache operator; use backend/default behavior.

### Shared Space

- `shared_space` selects the shared-memory address space used by the generated copy instruction.
- It applies to `CopyG2ROp`, `CopyR2GOp`, `CopyS2ROp`, and `CopyR2SOp` atom construction.
- `cute.nvgpu.SharedSpace.CTA`: shared memory is addressed within a CTA.
- `cute.nvgpu.SharedSpace.CLUSTER`: shared memory is addressed in cluster shared-memory space; use only when targeting cluster-capable kernels and instructions.
- Prefer `CTA` unless the copy intentionally uses cluster shared-memory addressing.

### Invariant

- `invariant` marks a global load as reading data that does not change for the relevant execution.
- It applies only to `CopyG2ROp` atom construction.
- Use `invariant=True` only when the loaded global memory value is known not to change for the relevant execution; otherwise leave it as `False`.

## Tiled Copy Construction

- Always create the copy atom first with `copy_atom = cute.make_copy_atom(copy_op, dtype)`, then pass `copy_atom` to tiled-copy construction.
- Do not pass `copy_op` directly to `cute.make_tiled_copy(...)`, `cute.make_tiled_copy_tv(...)`, `cute.make_tiled_copy_A(...)`, or `cute.make_tiled_copy_B(...)`.
- In most cases, use `cute.make_tiled_copy_tv(copy_atom, thr_layout, val_layout)` instead of `cute.make_tiled_copy`.
- Define `thr_layout` and `val_layout` as separate values before constructing the tiled copy.
- Define `tiler_mn` and `layout_tv` with `cute.make_layout_tv(thr_layout, val_layout)` when the tile shape or TV mapping is needed for tensor tiling, inspection, or explanation.
- For MMA operand retiling, use `cute.make_tiled_copy_A(copy_atom, tiled_mma)` or `cute.make_tiled_copy_B(copy_atom, tiled_mma)` after atom construction.

```python
copy_op = cute.nvgpu.CopyUniversalOp()              # plain assignment-style copy op
copy_atom = cute.make_copy_atom(copy_op, dtype)     # copy atom over dtype values

thr_layout = cute.make_layout((2, 3), stride=(3, 1))  # shape: (2, 3), 6 thread slots
val_layout = cute.make_layout((2, 2), stride=(2, 1))  # shape: (2, 2), 4 values per thread
tiler_mn, layout_tv = cute.make_layout_tv(thr_layout, val_layout)  # tiler_mn: (4, 6), TV shape: ((3, 2), (2, 2))
tiled_copy = cute.make_tiled_copy_tv(copy_atom, thr_layout, val_layout)  # tile: (4, 6), TV layout matches layout_tv
```

```python
copy_op = cute.nvgpu.CopyUniversalOp()           # plain assignment-style copy op
copy_atom = cute.make_copy_atom(copy_op, dtype)  # copy atom over dtype values
tiled_copy = cute.make_tiled_copy_A(copy_atom, tiled_mma)  # TV layout matches tiled_mma A
```

## Thread Copy Slices

- Use `tiled_copy.get_slice(tidx)` to get the current thread's `ThrCopy`.
- Use `thr_copy.partition_S(src)` and `thr_copy.partition_D(dst)` to create source and destination partitions for that thread.
- Use `tiled_copy.retile(tensor)` or `thr_copy.retile(tensor)` when a copy path must view an existing tensor through the tiled copy's TV layout.
- For tiled-copy flows, issue the copy with the copy atom and the partitioned tensors returned by the thread slice.
- Keep partition shape comments in copy-value and tiled-mode form, for example `(CPY, CPY_M, CPY_N)`.

```python
tidx, _, _ = cute.arch.thread_idx()

thr_copy = tiled_copy.get_slice(tidx)

tS = thr_copy.partition_S(tile_S)  # (CPY, CPY_M, CPY_N)
tD = thr_copy.partition_D(tile_D)  # (CPY, CPY_M, CPY_N)

cute.copy(copy_atom, tS, tD)
```

## Predicated Tiled Copy

- Build predicate tensors from identity or coordinate tensors tiled and partitioned through the same path as the data.
- Partition the coordinate or predicate tensor with the same `ThrCopy` slice used for the guarded data tensor.
- Store predicates in a register-memory Boolean tensor with the same shape as the partitioned copy tensors.
- Pass the predicate with `pred=pred_tensor` to `cute.copy(...)`.
- Use stride-0 predicate layouts only when intentionally broadcasting a predicate across a mode.

```python
coord_tensor = cute.make_identity_tensor(problem_shape)

coord_tile = cute.local_tile(coord_tensor, tile_shape, tile_coord)
src_tile = cute.local_tile(src_tensor, tile_shape, tile_coord)
dst_tile = cute.local_tile(dst_tensor, tile_shape, tile_coord)

thr_copy = tiled_copy.get_slice(tidx)
tC = thr_copy.partition_S(coord_tile)
tS = thr_copy.partition_S(src_tile)
tD = thr_copy.partition_D(dst_tile)

pred = cute.make_rmem_tensor(tC.shape, cutlass.Boolean)
for i in cutlass.range_constexpr(cute.size(pred)):
    pred[i] = cute.elem_less(tC[i], problem_shape)

cute.copy(copy_atom, tS, tD, pred=pred)
```

## Copy Usage Notes

- Use `cute.copy(copy_atom, src, dst)` for explicit copy atoms and already-partitioned tiled-copy tensors.
- Use `cute.copy(copy_atom, src, dst, pred=pred)` for predicated explicit copies.
- Use `cute.autovec_copy(src, dst)` only when the local code intentionally delegates vector width selection to CuTe DSL.
- If a copy writes shared memory cooperatively, synchronize before consumers read it. For non-bulk `cp.async`, commit the group, wait for the needed number of groups, then perform the consumer-visible synchronization.

```python
cute.copy(copy_atom, tS, tD)
cute.copy(copy_atom, tS, tD, pred=pred)

cute.arch.cp_async_commit_group()
cute.arch.cp_async_wait_group(0)
cute.arch.sync_threads()
```
