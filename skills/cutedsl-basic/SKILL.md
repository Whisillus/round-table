---
name: cutedsl-basic
description: Use whenever writing, reviewing, or debugging CuTe DSL code; covers default imports, JIT/runtime, control flow, dtypes, terminology, tensor and partitioned tensor naming conventions, tensor access, predication, cute.elem_less, shared storage, arch wrappers, debug workflow, and routing to related CuTe DSL skills.
---

# CuTe DSL Basic

## Related Skills

- Treat this as the entry-point skill for CuTe DSL coding tasks; load it before applying more specialized CuTe DSL skills.
- Also use `cutedsl-tensor` when the task involves tensor construction, register tensors, fragments, tensor views, TensorSSA helpers, tensor reinterpretation, or tensor printing.
- Also use `cutedsl-layout` when the task involves layouts, layout algebra, tensor tiling, local partitioning, or thread-value layouts.
- Also use `cutedsl-copy` when the task involves copy operation descriptors, copy atoms, tiled copies, TMA copy setup, bulk copy, or warp matrix copy.
- Also use `cutedsl-mma` when the task involves MMA ops/atoms, tiled MMA, GEMM mainloops, WMMA, or WGMMA.
- Also use `cutedsl-pipeline` when the task involves `cutlass.pipeline`, staged producer/consumer protocols, pipeline state, mbarriers, `cp.async` pipelines, or TMA pipelines.
- Also use the CUDA skills when the question involves CUDA architecture, PTX, synchronization, memory ordering, tensor cores, TMA, WGMMA, or other low-level GPU semantics.

## Imports

- Use these default CuTe DSL imports.
- Do not add other `cutlass` module imports unless the user explicitly requests them.

```python
import cutlass
import cutlass.cute as cute
import cutlass.pipeline as pipeline
```

## JIT and Runtime

- Use `@cute.jit` for host-side JIT functions, launchers, and reusable compile-time helpers.
- Use `@cute.kernel` for GPU kernel bodies. A `@cute.kernel` body cannot call another `@cute.kernel`.
- JIT function arguments are dynamic by default; annotate compile-time values with `cutlass.Constexpr`.
- Use type annotations for DSL objects passed into kernels when they clarify the ABI, such as `cute.Tensor`, `cute.CopyAtom`, `cute.MmaAtom`, `cute.TiledCopy`, and `cute.TiledMma`.
- Use `kernel(...).launch(...)` from a `@cute.jit` launcher for normal kernel launches.
- Call `cute.compile(...)` from ordinary Python on a host `@cute.jit` launcher when an explicit compiled callable is needed, such as for inspecting generated artifacts or integrating with external launch paths.

```python
@cute.kernel
def kernel(
    tensor: cute.Tensor,
    tile_m: cutlass.Constexpr,
    tile_n: cutlass.Constexpr,
):
    ...

@cute.jit
def launch(
    tensor: cute.Tensor,
    tile_m: cutlass.Constexpr,
    tile_n: cutlass.Constexpr,
):
    grid = (1, 1, 1)
    block = (128, 1, 1)
    kernel(tensor, tile_m, tile_n).launch(grid=grid, block=block)

def compile_kernel(tensor: cute.Tensor, tile_m: int, tile_n: int):
    return cute.compile(launch, tensor, tile_m, tile_n)
```

## Control Flow

- Use `cutlass.range(...)` for loops that should lower to dynamic device IR; bounds can be Python integers or DSL integer values.
- Use `cutlass.range_constexpr(...)` for loops that should execute at JIT trace time with compile-time bounds.
- Use `cutlass.const_expr(expr)` only when a branch condition must be a Python compile-time value; remove `const_expr(...)` when a dynamic branch should be emitted.
- Dynamic `if`, `for`, and `while` regions must preserve value type and structure across region boundaries. Do not change a variable from one dtype, tuple structure, or object shape to another inside dynamic control flow.
- Loop attributes such as `unroll`, `unroll_full`, and `prefetch_stages` must be Python compile-time values.
- Use `cutlass.Constexpr` for tile sizes, layout choices, dtype/config flags, and loop attributes that must be known while tracing.
- Avoid deprecated `cutlass.range_dynamic(...)` and `cutlass.dynamic_expr(...)` in new code.

```python
for k_tile in cutlass.range(0, k_tiles, 1, unroll=4):
    ...

for stage in cutlass.range_constexpr(num_stages):
    ...

if cutlass.const_expr(use_tma):
    ...
else:
    ...

while remaining > 0:
    ...
```

## Dtypes

- Define operand and accumulator dtypes as separate variables: `a_dtype`, `b_dtype`, and `acc_dtype`.
- Use separate `a_dtype` and `b_dtype` names even when an API expects a shared A/B dtype.

```python
a_dtype = ...
b_dtype = ...
acc_dtype = ...
```

## Major Terminology

- Use only MN-major and K-major terminology for CuTe DSL operand layouts.
- Do not use row-major or column-major terminology when discussing CuTe DSL major modes.
- Prefer `cute.nvgpu.OperandMajorMode.MN` and `cute.nvgpu.OperandMajorMode.K` for operands.
- Prefer `cute.nvgpu.OutputMajorMode.M` and `cute.nvgpu.OutputMajorMode.N` for outputs when an output-major enum is needed.

## Tensor Naming

- Read common CuTe/CUTLASS base tensor names as `yZ`: tensor kind or storage `y` holding logical tensor or operand `Z`.
- Common first letters are `m` for the original logical matrix/tensor, `g` for global memory, `s` for shared memory, `r` for register fragment, `c` for coordinate/identity tensor, and `p` for predicate tensor.

```python
mA = cute.make_tensor(a_ptr, a_layout)  # logical matrix A
gA = cute.local_tile(mA, cta_tiler, cta_coord)  # CTA tile of global A
sA = storage.smem.get_tensor(smem_layout)  # shared-memory A
cA = cute.make_identity_tensor(mA.shape)  # coordinate tensor for A
```

## Partitioned Tensor Naming

- Read common CuTe/CUTLASS partitioned tensor names as `tXyZ`: each thread's slice or view of tensor `yZ` for the `X` path.
- The first `t` means a per-thread view produced by a partitioning path such as `cute.local_partition`, `thr_copy.partition_*`, or `thr_mma.partition_*`.
- The second letter `X` names the path or role, not necessarily the final operand: `A` and `B` are usually load/copy paths, `C` is usually the compute/MMA or accumulator path, `D` is usually an output/epilogue path, and `Q`, `K`, `V`, or `O` are common attention paths.
- The third letter `y` names the tensor kind or storage: `g` global memory, `s` shared memory, `r` register fragment, `c` coordinate/identity tensor, `p` predicate tensor, and sometimes `m` for the original logical matrix or tensor.
- The final letter or suffix `Z` names the logical tensor or operand being viewed, such as `A`, `B`, `C`, `D`, `Q`, `K`, `V`, `O`, `Aux`, `Acc`, `SFA`, or `SFB`.
- Prefer this user-facing explanation over the formal phrase "partitioning pattern `tX` applied to tensor `yZ`" unless discussing CuTe layout mechanics directly.

```python
tAgA = thr_copy_a.partition_S(gA)  # each thread's slice of global A for the A load/copy path
tAsA = thr_copy_a.partition_D(sA)  # each thread's slice of shared A for the A load/copy path

tCsA = thr_mma.partition_A(sA)     # each thread's slice of shared A for the C compute/MMA path
tCsB = thr_mma.partition_B(sB)     # each thread's slice of shared B for the C compute/MMA path
tCrC = tiled_mma.make_fragment_C(tCgC)  # each thread's register C fragment for the C compute/MMA path
```

## Tensor Access

- When indexing tensors, write the coordinate inline instead of defining a separate coordinate variable.

```python
tile = tensor[(None, rest_coord)]
```

## Predication And Comparisons

- Build ragged-tile predicates from coordinates, not from ad hoc boundary arithmetic detached from the tiled tensors.
- Use `cute.make_identity_tensor(shape)` to carry logical coordinates through the same tiling and partitioning path as the data.
- Use `cute.elem_less(coord, limit_shape)` for coordinate-wise in-bounds checks.
- `cute.elem_less(lhs, rhs)` compares coordinates or shapes component by component and returns true only when every component of `lhs` is strictly less than the corresponding component of `rhs`.
- Use `cute.elem_less(coord, problem_shape)` as the normal ragged-tile in-bounds predicate.
- For Tensor loads/stores, use the `mask=` and `pass_thru=` arguments documented in `cutedsl-tensor`.
- For copy-atom and tiled-copy partitioned flows, pass a predicate tensor with `cute.copy(copy_atom, src, dst, pred=pred_tensor)`; keep the predicate layout compatible with the partitioned source and destination tensors.
- Keep dynamic predicates as DSL Boolean or TensorSSA values. Do not force them through Python `bool(...)` or `cutlass.const_expr(...)`.

```python
coord_tensor = cute.make_identity_tensor(problem_shape)
coord_tile = cute.local_tile(coord_tensor, tile_shape, tile_coord)

coord = coord_tile[(m, n)]
valid = cute.elem_less(coord, problem_shape)
```

```python
coord_tensor = cute.make_identity_tensor(problem_shape)
coord_tile = cute.local_tile(coord_tensor, tile_shape, tile_coord)
data_tile = cute.local_tile(data_tensor, tile_shape, tile_coord)

coord = coord_tile[(m, n)]
mask = cute.elem_less(coord, problem_shape)
if mask:
    value = data_tile[(m, n)]
    # Consume value here, inside the guarded branch.
```

## Shared Storage And Structs

- Use `cutlass.utils.SmemAllocator()` inside kernels when allocating shared-memory storage.
- `SmemAllocator` computes the kernel shared-memory usage; do not manually pass a dynamic shared-memory byte count unless the surrounding launch path explicitly requires it.
- `SmemAllocator.allocate_tensor(dtype, layout, byte_alignment=..., swizzle=...)` returns a shared-memory `cute.Tensor`; the layout must be static.
- Use `@cute.struct` for named shared-storage aggregates.
- Struct fields should be DSL scalar types, `cute.struct.MemRange[dtype, size]`, nested `@cute.struct` types, or `cute.struct.Align[T, alignment]` wrappers.
- Use `cute.struct.Align[...]` for fields that need explicit alignment, especially shared-memory buffers used by vectorized copies, MMA, or TMA paths.
- Use `MemRange.get_tensor(layout, dtype=None, swizzle=None)` to turn a struct buffer field into a tensor view.
- Assign scalar struct fields directly with `storage.field = value`; use `storage.field.ptr` only when a pointer is needed.

```python
@cute.struct
class SharedStorage:
    smem: cute.struct.Align[
        cute.struct.MemRange[cutlass.Float32, smem_elems],
        16,
    ]
    flag: cutlass.Int32

allocator = cutlass.utils.SmemAllocator()
storage = allocator.allocate(SharedStorage, byte_alignment=16)

smem_tensor = storage.smem.get_tensor(smem_layout)
storage.flag = 0
```

## Arch Wrappers

- Use `cute.arch.thread_idx()`, `block_idx()`, `block_dim()`, and `grid_dim()` for CTA and grid indexing.
- Use `cute.arch.lane_idx()` and `cute.arch.warp_idx()` for warp-local control and partitioning.
- Use `cute.arch.WARP_SIZE` instead of spelling `32` when the code depends on warp width.
- Use `cute.arch.sync_threads()` for CTA-wide synchronization and `cute.arch.sync_warp(mask)` for warp synchronization.
- Use `cute.arch.barrier(...)` and `cute.arch.barrier_arrive(...)` only for named CTA barrier patterns where the participating thread count and divergence behavior are explicit.
- Use `pipeline` APIs for staged producer/consumer synchronization and the CUDA synchronization skills for low-level memory-order reasoning.

```python
tid_x, tid_y, tid_z = cute.arch.thread_idx()
bid_x, bid_y, bid_z = cute.arch.block_idx()
lane = cute.arch.lane_idx()
warp = cute.arch.warp_idx()

if lane < 16:
    ...

cute.arch.sync_threads()
```

## Debug

- Use Python `print(...)` for compile-time/static information such as layouts and shapes known during JIT tracing.
- Use `cute.printf(...)` for runtime GPU-side diagnostics; remove it from performance paths after debugging.
- Use `CUTE_DSL_LINEINFO=1` or `GenerateLineInfo` when correlating generated code with Python source.
- Use `CUTE_DSL_KEEP=ir`, `ir-debug`, `ptx`, `cubin`, `llvm`, or `all` to dump generated artifacts.
- Use `CUTE_DSL_PRINT_IR=1` to print generated IR without writing files.
- Use `CUTE_DSL_DUMP_DIR` to redirect dumped artifacts to a known directory.
- Compiled callables can expose generated artifacts such as `__ptx__`, `__cubin__`, and `__mlir__`.
- Use `compute-sanitizer python ...` for memory/race debugging when a kernel produces invalid results or faults.

```python
def compile_for_debug(tensor: cute.Tensor, tile_m: int, tile_n: int):
    kernel.set_name_prefix("debug_kernel")

    debug_options = (
        cute.OptLevel(1),
        cute.EnableAssertions,
        cute.GenerateLineInfo,
        cute.KeepPTX,
        cute.KeepCUBIN,
    )
    compiled = cute.compile[debug_options](launch, tensor, tile_m, tile_n)

    print(compiled.__mlir__)
    print(compiled.__ptx__)
    return compiled
```
