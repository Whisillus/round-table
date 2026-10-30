---
name: cutedsl-mma
description: Use when the user asks about CuTe DSL MMA, GEMM, cute.gemm, tiled MMA, WMMA, WGMMA, SM120 block-scaled MMA, warpgroup MMA, MMA atoms, or MMA instruction shapes.
---

# CuTe DSL MMA

Build MMA code in this order: choose an MMA operation descriptor, create an MMA atom, then create a tiled MMA when tiled MMA partitioning is needed.

## MMA Op

An MMA op describes the instruction family, operand types, accumulator type, instruction shape, and op-specific operand interpretation. Treat the MMA operation descriptor as an op, not an atom.

### Universal MMA Op

Use `cute.nvgpu.MmaUniversalOp` for the generic FMA MMA path, not a tensor-core-specific WMMA or WGMMA instruction.

- The universal op has instruction shape `(1, 1, 1)` and supports all architectures.
- A, B, and accumulator types must be the same type: `Float16`, `Float32`, or `Float64`.

Op inputs:

- `cute.nvgpu.MmaUniversalOp(abacc_dtype)`.

```python
assert a_dtype == b_dtype
assert a_dtype == acc_dtype
abacc_dtype = a_dtype

mma_op = cute.nvgpu.MmaUniversalOp(abacc_dtype)
```

### Warp MMA Op

Use `cute.nvgpu.warp` MMA ops for synchronous warp-level MMA instructions.

- All `cute.nvgpu.warp` MMA ops support only A K-major and B K-major operand layouts.
- For non-mixed-precision warp-level MMA ops, assert `a_dtype == b_dtype`, define `ab_type = a_dtype`, and pass `ab_type` to the op constructor.
- Supported architectures:
  - `MmaF16BF16Op`: SM80+.
  - `MmaFP8Op`: SM89+.
  - `MmaMXF4Op`, `MmaMXF4NVF4Op`, `MmaMXF8Op`, and `MmaMXF8F6F4Op`: SM120a/SM120f/SM121a/SM121f.
- Supported instruction shapes:
  - `MmaF16BF16Op`: `(16, 8, 8)` or `(16, 8, 16)`.
  - `MmaFP8Op`: `(16, 8, 16)` or `(16, 8, 32)`.
  - SM120 FP8 block-scaled ops: `(16, 8, 32)`.
  - SM120 FP4 block-scaled ops: `(16, 8, 64)`.

Op inputs:

- `cute.nvgpu.warp.MmaF16BF16Op(ab_type, acc_dtype, mma_inst_shape_mnk)`.
- `cute.nvgpu.warp.MmaFP8Op(ab_type, acc_dtype, mma_inst_shape_mnk)`.

```python
assert a_dtype == b_dtype
ab_type = a_dtype

mma_inst_shape_mnk = (16, 8, 16)
mma_op = cute.nvgpu.warp.MmaF16BF16Op(ab_type, acc_dtype, mma_inst_shape_mnk)
```


Use `cute.nvgpu.warp` SM120 ops for Blackwell GeForce/RTX 50-series block-scaled `mma.sync.aligned.kind::...` instructions.

- These ops are warp-collective and synchronous;
- The accumulator type must be `cutlass.Float32`.
- Operand layout is fixed: A K-major and B K-major.
- `MmaMXF4Op(ab_dtype, acc_dtype, sf_type)` uses `cutlass.Float4E2M1FN` inputs and `cutlass.Float8E8M0FNU` scale factors; the class fixes vector size 32 and shape `(16, 8, 64)`.
- `MmaMXF4NVF4Op(ab_dtype, acc_dtype, sf_type)` uses `cutlass.Float4E2M1FN` inputs and `cutlass.Float8E4M3FN` scale factors; the class fixes vector size 16 and shape `(16, 8, 64)`.
- `MmaMXF8Op(ab_dtype, acc_dtype, sf_type)` uses same-type FP8 inputs (`cutlass.Float8E4M3FN` or `cutlass.Float8E5M2`) and `cutlass.Float8E8M0FNU` scale factors; the class fixes vector size 32 and shape `(16, 8, 32)`.
- `MmaMXF8F6F4Op(a_dtype, b_dtype, acc_dtype, sf_type)` uses independent A/B dtypes. In the local CuTe DSL API, supported mixed pairs are FP4 x FP8 and FP8 x FP4 with `cutlass.Float8E8M0FNU` scale factors; same-type FP4 routes to `MmaMXF4Op` or `MmaMXF4NVF4Op`, and same-type FP8 routes to `MmaMXF8Op`.
- The local CuTe DSL `cute.nvgpu.warp` module exposes SM120 block-scaled warp ops.
- Prefer local helpers such as `make_sm120_blockscaled_mma_op(...)` when present.

```python
mma_op = cute.nvgpu.warp.MmaMXF4Op(
    cutlass.Float4E2M1FN,
    cutlass.Float32,
    cutlass.Float8E8M0FNU,
)

mixed_mma_op = cute.nvgpu.warp.MmaMXF8F6F4Op(
    cutlass.Float4E2M1FN,
    cutlass.Float8E5M2,
    cutlass.Float32,
    cutlass.Float8E8M0FNU,
)
```

### WGMMA Op

Use `cute.nvgpu.warpgroup` MMA ops for asynchronous warpgroup-level MMA instructions.

- 16-bit WGMMA uses the same A/B type.
- 8-bit WGMMA uses independent A/B types.
- Supported architecture: `MmaF16BF16Op`, `MmaF8Op`, and `MmaI8Op` require `sm_90a`.
- Supported instruction shapes:
  - `MmaF16BF16Op`: `(64, N, 16)`, where `8 <= N <= 256` and `N % 8 == 0`.
  - `MmaF8Op`: `(64, N, 32)`, where `8 <= N <= 256` and `N % 8 == 0`.
  - `MmaI8Op`: `(64, N, 32)`, where `N in {8, 24}` or `N % 16 == 0`, with `8 <= N <= 256`.
- WGMMA major-mode legality depends on the op and A operand source:
  - `MmaF16BF16Op` with `a_src = OperandSource.SMEM`: A and B may be `OperandMajorMode.K` or `OperandMajorMode.MN`.
  - `MmaF16BF16Op` with `a_src = OperandSource.RMEM`: keep A `OperandMajorMode.K`; B may be `OperandMajorMode.K` or `OperandMajorMode.MN`.
  - `MmaF8Op` and `MmaI8Op`: A and B must both be `OperandMajorMode.K`.

Op inputs:

- `cute.nvgpu.warpgroup.MmaF16BF16Op(ab_type, acc_dtype, mma_inst_shape_mnk, a_src, a_major_mode, b_major_mode)`.
- `cute.nvgpu.warpgroup.MmaF8Op(a_dtype, b_dtype, acc_dtype, mma_inst_shape_mnk, a_src, a_major_mode, b_major_mode)`.
- `cute.nvgpu.warpgroup.MmaI8Op(a_dtype, b_dtype, acc_dtype, mma_inst_shape_mnk, a_src, a_major_mode, b_major_mode)`.

```python
assert a_dtype == b_dtype
ab_type = a_dtype

mma_inst_shape_mnk = (64, 128, 16)
a_src = cute.nvgpu.warpgroup.OperandSource.SMEM
a_major_mode = cute.nvgpu.OperandMajorMode.K
b_major_mode = cute.nvgpu.OperandMajorMode.K
mma_op = cute.nvgpu.warpgroup.MmaF16BF16Op(
    ab_type,
    acc_dtype,
    mma_inst_shape_mnk,
    a_src,
    a_major_mode,
    b_major_mode,
)
```

```python
mma_inst_shape_mnk = (64, 128, 32)
a_src = cute.nvgpu.warpgroup.OperandSource.SMEM
a_major_mode = cute.nvgpu.OperandMajorMode.K
b_major_mode = cute.nvgpu.OperandMajorMode.K
mma_op = cute.nvgpu.warpgroup.MmaF8Op(
    a_dtype,
    b_dtype,
    acc_dtype,
    mma_inst_shape_mnk,
    a_src,
    a_major_mode,
    b_major_mode,
)
```

## WGMMA Protocol

- `cute.nvgpu.warpgroup.fence()` orders prior fragment/register setup before WGMMA issue.
- `cute.nvgpu.warpgroup.commit_group()` publishes queued WGMMA instructions as an async completion group.
- `cute.nvgpu.warpgroup.wait_group(n)` waits until at most `n` committed WGMMA groups remain in flight; use `wait_group(0)` before consuming final accumulators.
- Issue WGMMA through `cute.gemm(...)` warpgroup-uniformly across the participating four contiguous warps.

```python
cute.nvgpu.warpgroup.fence()        # orders prior fragment/register writes before WGMMA reads
cute.gemm(tiled_mma, acc, tCrA[tile_crd], tCrB[tile_crd], acc)  # queues WGMMA for tile_crd
cute.nvgpu.warpgroup.commit_group() # commits queued WGMMA operations as one group
cute.nvgpu.warpgroup.wait_group(1)  # waits until at most one committed group remains
# ... pipeline continues ...
cute.nvgpu.warpgroup.wait_group(0)  # waits until no committed WGMMA groups remain
```

## MMA Atom

- Treat the MMA operation descriptor as an op, not an atom.
- Create the MMA atom with `mma_atom = cute.make_mma_atom(mma_op)` after choosing the MMA op.
- `cute.make_mma_atom(...)` has one normal user input: `mma_op`. Optional `loc`, `ip`, and internal `**kwargs` exist in the API, but current Universal MMA, warp MMA, SM120 block-scaled warp MMA, and WGMMA ops do not need op-specific kwargs.

```python
mma_atom = cute.make_mma_atom(mma_op)
```

## Tiled MMA

- Always create the MMA atom first with `mma_atom = cute.make_mma_atom(mma_op)`, then pass `mma_atom` to `cute.make_tiled_mma(...)`.
- Do not pass `mma_op` directly to `cute.make_tiled_mma(...)`.
- Define `atom_shape_mnk`, `atom_stride_mnk`, and `atom_layout_mnk` separately before constructing the tiled MMA.
- `permutation_mnk` is optional; define it separately only when needed, otherwise omit it.

```python
mma_op = cute.nvgpu.MmaUniversalOp(abacc_dtype)  # atom instruction shape: (1, 1, 1)
mma_atom = cute.make_mma_atom(mma_op)            # MMA atom for the universal op

atom_shape_mnk = (16, 16, 1)                    # 16x16x1 atom replicas across M/N/K
atom_stride_mnk = (16, 1, 1)                    # N-major atom layout, K singleton
atom_layout_mnk = cute.make_layout(atom_shape_mnk, stride=atom_stride_mnk)  # shape: (16, 16, 1)

tiled_mma = cute.make_tiled_mma(mma_atom, atom_layout_mnk)  # tiled MMA shape: (16, 16, 1)
```

### Thread MMA And Partitions

- Use `tiled_mma.get_slice(tidx)` to get the current thread's `ThrMma`.
- Use `thr_mma.partition_A(tensor)`, `partition_B(tensor)`, and `partition_C(tensor)` to create operand and accumulator partitions.
- Use `tiled_mma.make_fragment_A(...)`, `make_fragment_B(...)`, and `make_fragment_C(...)` to allocate or view fragments shaped for the tiled MMA.
- Prefer building accumulator and temporary fragment shapes from already partitioned tensors.
- When a tensor carries extra K-tile or pipeline-stage modes, pass the per-K or per-stage slice consumed by one MMA issue to fragment construction and `cute.gemm(...)`.
- Keep partition comments in `(MMA, MMA_M, MMA_K)`, `(MMA, MMA_N, MMA_K)`, and `(MMA, MMA_M, MMA_N)` form.

```python
tidx, _, _ = cute.arch.thread_idx()

thr_mma = tiled_mma.get_slice(tidx)

tCsA = thr_mma.partition_A(sA)  # (MMA, MMA_M, MMA_K, ...)
tCsB = thr_mma.partition_B(sB)  # (MMA, MMA_N, MMA_K, ...)
tCgC = thr_mma.partition_C(gC)  # (MMA, MMA_M, MMA_N)

tCrA = tiled_mma.make_fragment_A(tCsA)
tCrB = tiled_mma.make_fragment_B(tCsB)
tCrC = tiled_mma.make_fragment_C(tCgC)
tCrC.fill(0.0)
```

### Retiling With Copy

- Use `cute.make_tiled_copy_A(copy_atom, tiled_mma)` and `cute.make_tiled_copy_B(copy_atom, tiled_mma)` when a copy path must match the tiled MMA operand layout.
- Retile copy destinations into existing MMA fragments with `ThrCopy.retile(...)` for shared-to-register paths.
- Verify the tiled copy and tiled MMA are built for the same logical thread count when they are expected to cooperate on one operand path.

```python
s2r_copy_a = cute.make_tiled_copy_A(s2r_atom_a, tiled_mma)
s2r_thr_copy_a = s2r_copy_a.get_slice(tidx)

tXsA = s2r_thr_copy_a.partition_S(sA)  # source SMEM A partition for this thread
tXrA = s2r_thr_copy_a.retile(tCrA)     # destination view retiled like the MMA A fragment
```

## MMA Algorithms

- Use `cute.gemm(tiled_mma, acc, A, B, acc)` for tiled MMA execution.
- CuTe GEMM operand convention is A `(M,K)`, B `(N,K)`, C `(M,N)`.
- K appears in the second mode of both A and B; do not rewrite B as `(K,N)` in CuTe DSL code.
- Loop over the K tile or K block mode outside `cute.gemm(...)` when the partitioned operand tensors still carry an explicit K tile dimension.
- For WGMMA, keep the `cute.gemm(...)` issue warpgroup-uniform and pair it with the WGMMA commit/wait protocol above.

```python
num_k_blocks = cute.size(tCrA, mode=[2])
for k_block in cutlass.range_constexpr(num_k_blocks):
    cute.gemm(
        tiled_mma,
        tCrC,
        tCrA[(None, None, k_block)],
        tCrB[(None, None, k_block)],
        tCrC,
    )
```
