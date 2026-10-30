---
name: cute-mma
description: Use when the user asks about C++ CuTe MMA, GEMM, cute::gemm, TiledMMA, ThrMMA, MMA_Atom, MMA_Traits, MMA operation structs, WMMA, WGMMA, SM120 block-scaled MMA, warpgroup MMA, MMA fragments, or MMA instruction shapes.
---

# CuTe C++ MMA

Build MMA code in this order: choose an MMA operation, create an `MMA_Atom`, then create a `TiledMMA` when tiled MMA partitioning is needed.

## MMA Operations

An MMA operation describes the instruction family, operand types, accumulator type, instruction shape, and operand interpretation. Treat the MMA operation as an op, not as an atom.

### Universal MMA Operation

- Use `UniversalFMA<D, A, B, C = D>` for the generic per-thread FMA path, not a tensor-core-specific instruction.
- The universal operation has instruction shape `(1,1,1)` and supports scalar FMA types accepted by `cute::fma`.
- Use it for simple tutorials, reference paths, and non-tensor-core fallback logic.

Operation inputs:

- `D`: destination/output value type.
- `A`: A operand value type; defaults to `D`.
- `B`: B operand value type; defaults to `A`.
- `C`: accumulator/source C value type; defaults to `D`.

```c++
using MmaOp = UniversalFMA<float, half_t, half_t>;
auto mma_op = MmaOp{};
```

### Warp-Level MMA Operations

- Use SM70, SM75, SM80, SM89, and SM120 operation structs for synchronous warp-level or quadpair-level MMA instructions.
- The operation struct name encodes architecture, instruction shape, D/A/B/C types, and operand layout or transpose convention.
- Examples include `SM70_8x8x4_F32F16F16F32_NT`, `SM75_16x8x8_F32F16F16F32_TN`, and `SM80_16x8x16_F16F16F16F16_TN`.
- Use architecture-specific operations only when the target architecture, operand element types, operand layouts, and instruction shape match.

Operation inputs:

- Most warp-level operation structs are stateless; construct them with `{}`.
- Select the operation type by matching the encoded instruction shape and operand type/layout suffix.
- For exact names, inspect `include/cute/arch/mma_sm*.hpp` and `include/cute/atom/mma_traits_sm*.hpp` in the local CUTLASS reference.

```c++
using MmaOp = SM80_16x8x16_F16F16F16F16_TN;
auto mma_op = MmaOp{};
```

- Non-block-scaled narrow precision uses `SM120_16x8x32_TN<a_type, b_type, c_type>` for `mma.sync.aligned.kind::f8f6f4` forms.
- Block-scaled MXF8/F6/F4 uses `SM120::BLOCKSCALED::SM120_16x8x32_TN_VS<a_type, b_type, c_type, sf_type, VS>` for `mma.sync.aligned.kind::mxf8f6f4.block_scale.scale_vec::1X` forms.
- FP4 block-scaled variants use `SM120::BLOCKSCALED::SM120_16x8x64_TN_VS<a_type, b_type, c_type, sf_type, VS>`; choose the scale-factor type and `VS` from the local example or helper for the target `mxf4.block_scale` or `mxf4nvf4.block_scale.scale_vec::{2X|4X}` form.
- SM120 narrow and block-scaled CuTe MMA paths are TN-only: A is row-major/K-major and B is column-major/K-major.
- Block-scaled atoms carry scale-factor fragments as part of the operand path. Preserve local zipped data/SF tensor construction and do not pass ordinary A/B fragments without the expected scale-factor layout.

```c++
using MmaOp = SM120_16x8x32_TN<float_e4m3_t, float_e5m2_t, float>;
MMA_Atom<MmaOp> mma_atom;

using BlockScaledMmaOp = SM120::BLOCKSCALED::SM120_16x8x32_TN_VS<
    float_e4m3_t,
    float_e2m1_t,
    float,
    float_ue8m0_t,
    32>;
MMA_Atom<BlockScaledMmaOp> block_scaled_mma_atom;

using Fp4BlockScaledMmaOp = SM120::BLOCKSCALED::SM120_16x8x64_TN_VS<
    float_e2m1_t,
    float_e2m1_t,
    float,
    float_ue4m3_t,
    16>;
MMA_Atom<Fp4BlockScaledMmaOp> fp4_block_scaled_mma_atom;
```

### WGMMA Operations

- Use SM90 GMMA operation aliases for asynchronous warpgroup-level MMA instructions.
- GMMA operation names encode `M`, `N`, `K`, D/A/B/C types, and operand source form.
- `SS` operations consume A and B through SMEM descriptors; `RS` operations consume A from registers and B through an SMEM descriptor.
- GMMA operation template parameters commonly include A and B major modes such as `GMMA::Major::K` or `GMMA::Major::MN`, and optional input scale modes.
- Hopper WGMMA paths require SM90a support and the matching SMEM descriptor or register-fragment setup.

Operation inputs:

- `tnspA`: A operand major mode, usually `GMMA::Major::K` or `GMMA::Major::MN` where supported.
- `tnspB`: B operand major mode, usually `GMMA::Major::K` or `GMMA::Major::MN` where supported.
- Optional scale inputs use `GMMA::ScaleIn` template parameters on operations that expose them.

```c++
using MmaOp = SM90_64x128x16_F32F16F16_SS<
    GMMA::Major::K,
    GMMA::Major::K>;
auto mma_op = MmaOp{};
```

## WGMMA Protocol

- WGMMA paths often consume SMEM descriptors rather than ordinary register A/B fragments; verify operand source form, SMEM layout, and descriptor construction together.
- Use `warpgroup_fence_operand(...)`, `warpgroup_arrive()`, `warpgroup_commit_batch()`, and `warpgroup_wait<N>()` following local SM90 examples when issuing asynchronous warpgroup MMA.
- Call `warpgroup_wait<0>()` before consuming final accumulators produced by outstanding WGMMA groups.
- Keep TMA, mbarrier, and WGMMA pipeline ordering together; do not replace warpgroup waits with a generic CTA barrier.

```c++
warpgroup_fence_operand(tCrC); // accumulator registers are fenced before WGMMA reads
warpgroup_arrive();            // warpgroup reaches the WGMMA issue point

cute::gemm(mma, tCrA(_,_,_,pipe), tCrB(_,_,_,pipe), tCrC); // queues WGMMA for this pipe

warpgroup_commit_batch();      // commits queued WGMMA operations as one group
warpgroup_wait<0>();           // waits until no committed WGMMA groups remain
warpgroup_fence_operand(tCrC); // accumulator registers are safe for later consumers
```

## MMA Trait

- `MMA_Traits<MMAOperation, Args...>` describes logical value types, fragment value types, instruction shape, thread mapping, and operand layouts for an MMA operation.
- `MMA_Atom<MMAOperation>` normalizes through `MMA_Traits<MMAOperation>` before it is used by `gemm(...)` or `make_tiled_mma(...)`.
- Use the operation form, such as `MMA_Atom<SM80_16x8x16_F16F16F16F16_TN>`, for ordinary operations.
- Use explicit `MMA_Traits<...>` only when local code or an architecture-specific path already requires trait-level arguments or state.

Common trait members:

- `ValTypeD`, `ValTypeA`, `ValTypeB`, `ValTypeC`: logical D/A/B/C value types.
- `FrgTypeA`, `FrgTypeB`, `FrgTypeC`: fragment value types when they differ from logical value types.
- `Shape_MNK`: logical instruction shape.
- `ThrID`: logical thread-id layout for the operation.
- `ALayout`, `BLayout`, `CLayout`: `(thread,value) -> operand-coordinate` layouts.
- `ValTypeSF`, `SFVecSize`, `SFALayout`, and `SFBLayout`: scale-factor type, vector size, and scale-factor layouts for SM120 block-scaled operations when exposed by the traits.

```c++
using Traits = MMA_Traits<SM80_16x8x16_F16F16F16F16_TN>;
using Atom = MMA_Atom<Traits>;
```

## MMA Atom

- Create an `MMA_Atom` after choosing the MMA operation.
- `MMA_Atom<MMAOperation>` is the common construction form.
- `MMA_Atom<MMA_Traits<MMAOperation, Args...>>` is available for explicit trait-level construction.
- Treat the operation as an op and the `MMA_Atom` as the checked instruction object used by CuTe algorithms.

```c++
using MmaOp = SM80_16x8x16_F16F16F16F16_TN;
MMA_Atom<MmaOp> mma_atom;

auto fma_atom = MMA_Atom<UniversalFMA<float, half_t, half_t>>{};
```

## Tiled MMA

### Tiled MMA Construction

- Always choose the operation and atom first, then build a `TiledMMA` when thread/value tiling is needed.
- Use `make_tiled_mma(mma_atom, thr_layout, permutations)` for explicit atom construction.
- C++ CuTe also provides `make_tiled_mma(mma_op, ...)`, which wraps the operation in `MMA_Atom<...>` and forwards to the atom overload; use the atom form when explaining or validating the flow.
- Define `thr_layout` separately before constructing the tiled MMA.
- `thr_layout` is the layout of atom replicas across logical M/N/K modes; it defaults to `Layout<Shape<_1,_1,_1>>{}`.
- `permutations` is optional; define it separately only when the tiled MMA intentionally needs a non-default M/N/K tiler or permutation.
- The tile size implied by the operation, thread layout, and permutations must match the surrounding CTA tile and operand partitions.

```c++
using MmaOp = SM80_16x8x16_F16F16F16F16_TN; // atom instruction shape: (_16,_8,_16)
MMA_Atom<MmaOp> mma_atom;                    // atom TV layouts from MMA_Traits<MmaOp>

auto mma_thr_layout = Layout<Shape<_2,_2,_1>>{}; // 2x2x1 atom replicas across M/N/K

TiledMMA mma = make_tiled_mma(mma_atom, mma_thr_layout); // tile: (_32,_16,_16), threads: 128
```

### Thread MMA And Partitions

- Use `mma.get_slice(threadIdx.x)` or `mma.get_thread_slice(threadIdx.x)` to get the current thread's `ThrMMA`.
- Use `thr_mma.partition_A(tensor)`, `partition_B(tensor)`, and `partition_C(tensor)` to create operand and accumulator partitions.
- Use `thr_mma.make_fragment_A(...)`, `make_fragment_B(...)`, and `make_fragment_C(...)` to allocate or view fragments for already-partitioned tensors.
- Use `thr_mma.partition_fragment_A(...)` and `partition_fragment_B(...)` for register fragments shaped from source tensors when local examples use that style.
- Keep partition comments in `(MMA,MMA_M,MMA_K)`, `(MMA,MMA_N,MMA_K)`, and `(MMA,MMA_M,MMA_N)` form; this makes shape mismatches easier to catch.

```c++
ThrMMA thr_mma = mma.get_slice(threadIdx.x);

Tensor tCsA = thr_mma.partition_A(sA);  // (MMA,MMA_M,MMA_K,...)
Tensor tCsB = thr_mma.partition_B(sB);  // (MMA,MMA_N,MMA_K,...)
Tensor tCgC = thr_mma.partition_C(gC);  // (MMA,MMA_M,MMA_N)

Tensor tCrA = thr_mma.make_fragment_A(tCsA);
Tensor tCrB = thr_mma.make_fragment_B(tCsB);
Tensor tCrC = thr_mma.make_fragment_C(tCgC);
clear(tCrC);
```

### Retiling With Copy

- Use `make_tiled_copy_A(copy_atom, mma)`, `make_tiled_copy_B(copy_atom, mma)`, and `make_tiled_copy_C(copy_atom, mma)` when a copy path must match a `TiledMMA` operand or accumulator layout.
- Retile destinations into existing MMA fragments with `ThrCopy::retile_D(...)` for shared-to-register paths.
- Verify `size(copy) == size(mma)` when the copy and MMA are expected to use the same thread count.

```c++
CUTE_STATIC_ASSERT_V(size(copy_a) == size(mma)); // copy and MMA use the same logical thread count

TiledCopy s2r_copy_a = make_tiled_copy_A(s2r_atom_a, mma); // copy TV layout matches MMA A
ThrCopy s2r_thr_copy_a = s2r_copy_a.get_slice(threadIdx.x); // current thread's A-copy slice

Tensor tXsA = s2r_thr_copy_a.partition_S(sA);  // source SMEM A partition for this thread
Tensor tXrA = s2r_thr_copy_a.retile_D(tCrA);   // destination view retiled like the MMA A fragment
```

## MMA Algorithms

- Use `cute::gemm(mma, A, B, C)` for tiled MMA execution when an explicit `TiledMMA` is selected.
- Use `gemm(A, B, C)` only for generic/default dispatch paths where the surrounding tutorial or algorithm intentionally relies on default selection.
- CuTe GEMM operand convention is A `(M,K)`, B `(N,K)`, C `(M,N)`.
- K appears in the second mode of both A and B; do not rewrite B as `(K,N)` in CuTe code.
- Loop over the K tile or K block mode outside `cute::gemm(...)` when the partitioned operand tensors still carry an explicit K tile dimension.

```c++
CUTE_UNROLL
for (int k_block = 0; k_block < size<2>(tCrA); ++k_block) {
  gemm(mma, tCrA(_,_,k_block), tCrB(_,_,k_block), tCrC);
}
```
