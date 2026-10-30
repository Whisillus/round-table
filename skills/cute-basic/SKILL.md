---
name: cute-basic
description: Use whenever writing, reviewing, or debugging C++ CuTe code; covers headers, namespaces, static integers, GEMM terminology, tensor and partitioned tensor naming conventions, predication, elem_less/elem_leq/elem_gtr/elem_geq comparisons, shared storage, debug workflow, and routing to related C++ CuTe skills.
---

# CuTe C++ Basic

## Related Skills

- Treat this as the entry-point skill for C++ CuTe coding tasks; load it before applying more specialized C++ CuTe skills.
- Also use `cute-tensor` when the task involves `cute::Tensor`, `make_tensor`, memory-space tagged pointers, register tensors, fragments, tensor slicing, or tensor printing.
- Also use `cute-layout` when the task involves `cute::Layout`, shapes, strides, layout algebra, `local_tile`, `local_partition`, `composition`, or tilers.
- Also use `cute-copy` when the task involves `cute::copy`, `copy_if`, `Copy_Atom`, `TiledCopy`, `ThrCopy`, `cp.async`, LDSM, or TMA copy setup.
- Also use `cute-mma` when the task involves `MMA_Atom`, `TiledMMA`, `ThrMMA`, `cute::gemm`, MMA fragments, WMMA, WGMMA, or MMA instruction shapes.
- Also use `cute-pipeline` when the task involves C++ CUTLASS pipeline classes such as `cutlass::PipelineAsync`, `PipelineTmaAsync`, `PipelineTmaStore`, `PipelineState`, mbarrier-backed producer/consumer protocols, or SM90 pipeline usage.
- Also use the CUDA skills when the question involves CUDA architecture, PTX, synchronization, memory ordering, tensor cores, TMA, WGMMA, or other low-level GPU semantics.

## Headers And Namespaces

- CuTe is a C++ CUDA header-only library; assume C++17 and CUDA compilation.
- Include the narrowest local header when editing existing code; examples often use `<cute/tensor.hpp>` as the broad CuTe entry point.
- Use `using namespace cute;` in small examples and kernels that already follow CUTLASS tutorial style; in library headers prefer explicit `cute::` names unless the local file already imports the namespace.
- Use C++ CuTe API names directly: `make_layout`, `make_shape`, `Tensor`, `Copy_Atom`, `MMA_Atom`, `TiledCopy`, and `TiledMMA`.

```c++
#include <cute/tensor.hpp>

using namespace cute;
```

## Static Values And Type Checks

- Use CuTe static integer aliases such as `_1`, `_2`, and `_128` instead of `Int<N>` when an alias exists.
- In value positions, instantiate aliases with braces, for example `_128{}`; in type positions, write the alias directly, for example `Shape<_128,_64>`.
- If a grouped type or value contains a static integer with no alias or an expression-based value, use `Int<Val>` consistently across that group, for example `Shape<Int<1>, Int<33>>` instead of `Shape<_1, Int<33>>`.
- Use ordinary C++ integers for runtime problem sizes and leading dimensions.
- Use `make_shape(...)`, `make_stride(...)`, and `make_coord(...)` for shape, stride, and coordinate values.
- Use `_` to keep a tensor mode when slicing, and use `X` in `Step<...>` projections to drop a mode from a projected tiler or coordinate.
- Use `CUTE_STATIC_ASSERT_V(...)` for CuTe value/type predicates such as `rank(...) == _3{}` or `congruent(shape, stride)`.
- Use `static_assert(is_static<T>::value)` when a layout or object must be fully static, such as a shared-memory layout used for static allocation.
- Use `CUTE_UNROLL` for small static loops that should be unrolled in kernels.

```c++
auto problem_shape = make_shape(M, N, K);
auto cta_tiler = make_shape(_128{}, _128{}, _32{});
auto cta_coord = make_coord(blockIdx.x, blockIdx.y, _);

CUTE_STATIC_ASSERT_V(rank(problem_shape) == _3{});
CUTE_STATIC_ASSERT_V(congruent(select<0,2>(problem_shape), stride_A));
```

## Major Terminology

- For CuTe GEMM code, use M-major, N-major, and K-major terminology when describing which semantic mode has stride 1.
- Use CuTe's GEMM convention: A is `(M,K)`, B is `(N,K)`, and C is `(M,N)`.
- Do not casually rewrite B as `(K,N)` in CuTe comments or examples; the K mode is the reduction mode and stays in the second mode for both A and B.
- Row-major and column-major wording is acceptable only when discussing generic 2-D layouts such as `LayoutLeft` and `LayoutRight`, not as a substitute for CuTe GEMM operand major modes.

```c++
Tensor mA = make_tensor(make_gmem_ptr(A), select<0,2>(shape_MNK), dA);  // (M,K)
Tensor mB = make_tensor(make_gmem_ptr(B), select<1,2>(shape_MNK), dB);  // (N,K)
Tensor mC = make_tensor(make_gmem_ptr(C), select<0,1>(shape_MNK), dC);  // (M,N)
```

## Tensor Naming

- Read common CuTe/CUTLASS base tensor names as `yZ`: tensor kind or storage `y` holding logical tensor or operand `Z`.
- Common first letters are `m` for the original logical matrix/tensor, `g` for global memory, `s` for shared memory, `r` for register fragment, `c` for coordinate/identity tensor, and `p` for predicate tensor.

```c++
Tensor mA = make_tensor(make_gmem_ptr(A), select<0,2>(shape_MNK), dA); // logical matrix A
Tensor gA = local_tile(mA, cta_tiler, cta_coord, Step<_1, X,_1>{});    // CTA tile of global A
Tensor sA = make_tensor(make_smem_ptr(storage.A.begin()), SmemLayoutA{}); // shared-memory A
Tensor cA = make_identity_tensor(shape(mA));                           // coordinate tensor for A
```

## Partitioned Tensor Naming

- Read common CuTe/CUTLASS partitioned tensor names as `tXyZ`: each thread's slice or view of tensor `yZ` for the `X` path.
- The first `t` means a per-thread view produced by a partitioning path such as `local_partition`, `ThrCopy::partition_*`, or `ThrMMA::partition_*`.
- The second letter `X` names the path or role, not necessarily the final operand: `A` and `B` are usually load/copy paths, `C` is usually the compute/MMA or accumulator path, `D` is usually an output/epilogue path, and `Q`, `K`, `V`, or `O` are common attention paths.
- The third letter `y` names the tensor kind or storage: `g` global memory, `s` shared memory, `r` register fragment, `c` coordinate/identity tensor, `p` predicate tensor, and sometimes `m` for the original logical matrix or tensor.
- The final letter or suffix `Z` names the logical tensor or operand being viewed, such as `A`, `B`, `C`, `D`, `Q`, `K`, `V`, `O`, `Aux`, `Acc`, `SFA`, or `SFB`.
- Prefer this user-facing explanation over the formal phrase "partitioning pattern `tX` applied to tensor `yZ`" unless discussing CuTe layout mechanics directly.

```c++
Tensor tAgA = thr_copy_a.partition_S(gA); // each thread's slice of global A for the A load/copy path
Tensor tAsA = thr_copy_a.partition_D(sA); // each thread's slice of shared A for the A load/copy path

Tensor tCsA = thr_mma.partition_A(sA);    // each thread's slice of shared A for the C compute/MMA path
Tensor tCsB = thr_mma.partition_B(sB);    // each thread's slice of shared B for the C compute/MMA path
Tensor tCrC = thr_mma.make_fragment_C(tCgC); // each thread's register C fragment for the C compute/MMA path
```

## Predication And Comparisons

- Build ragged-tile predicates from identity or coordinate tensors that go through the same tiling and partitioning path as the data.
- Use `make_identity_tensor(shape)` to create a coordinate tensor with the same logical shape as the original tensor.
- Use `elem_less(coord, shape)` to test whether a coordinate is inside the original logical bounds.
- `elem_less(a, b)` compares tuples component by component and returns true only when every component of `a` is strictly less than the corresponding component of `b`. This is the normal helper for in-bounds coordinate predicates.
- `elem_leq(a, b)` is implemented as `!elem_less(b, a)`: it is true unless `b` is strictly less than `a` in every component.
- `elem_gtr(a, b)` is `elem_less(b, a)`: every component of `a` is strictly greater than the corresponding component of `b`.
- `elem_geq(a, b)` is implemented as `!elem_less(a, b)`: it is true unless `a` is strictly less than `b` in every component.
- `lex_less(a, b)` compares lexicographically from the first coordinate to the last coordinate.
- `lex_leq(a, b)` is implemented as `!lex_less(b, a)`: lexicographic `a <= b`.
- `lex_gtr(a, b)` is `lex_less(b, a)`: lexicographic `a > b`.
- `lex_geq(a, b)` is implemented as `!lex_less(a, b)`: lexicographic `a >= b`.
- `colex_less(a, b)` compares colexicographically from the last coordinate to the first coordinate.
- `colex_leq(a, b)` is implemented as `!colex_less(b, a)`: colexicographic `a <= b`.
- `colex_gtr(a, b)` is `colex_less(b, a)`: colexicographic `a > b`.
- `colex_geq(a, b)` is implemented as `!colex_less(a, b)`: colexicographic `a >= b`.
- Use normal tuple `==` and `!=` for equality; there are no `elem_eq` or `elem_equal` helpers in the local C++ CuTe headers.
- Use `copy_if(...)` for predicated copies; see `cute-copy` for the copy-specific forms.
- Keep predicates congruent with the partitioned tensors they guard. Avoid detached boundary arithmetic that does not follow the same `local_tile`, `local_partition`, `TiledCopy`, or `TiledMMA` path.

```c++
auto in_bounds = elem_less(make_coord(m, n), make_shape(M, N));

auto all_lt = elem_less(make_coord(1, 9), make_coord(2, 10));    // true
auto all_gt = elem_gtr(make_coord(3, 4), make_coord(2, 1));      // true

auto lex = lex_less(make_coord(1, 9), make_coord(2, 0));         // true: 1 < 2
auto colex = colex_less(make_coord(9, 1), make_coord(0, 2));     // true: 1 < 2
```

```c++
Tensor cC = make_identity_tensor(shape(mC));

Tensor cta_cC = local_tile(cC, cta_tiler, cta_coord, Step<_1,_1, X>{});
Tensor tCcC = thr_mma.partition_C(cta_cC);

if (elem_less(tCcC(i), shape(mC))) {
  tCgC(i) = alpha * tCrC(i) + beta * tCgC(i);
}
```

## Shared Storage

- Use static CuTe layouts for shared-memory tensors whenever possible; the SMEM allocation size often comes from `cosize_v<Layout>` or `decltype(cosize(layout))::value`.
- Tag shared-memory pointers with `make_smem_ptr(...)` before constructing SMEM tensors.
- Use a `SharedStorage` struct when a kernel has multiple SMEM arrays, barriers, or aligned buffers.
- Use `alignas(...)` on shared-storage fields used by TMA, vectorized copies, or architecture-specific descriptors when local examples require it.
- Keep shared-storage structs and SMEM tensor layouts consistent; mismatched layout cosize or alignment can compile but corrupt data.

```c++
template <class ElementA, class ElementB, class SmemLayoutA, class SmemLayoutB>
struct SharedStorage {
  alignas(128) cute::ArrayEngine<ElementA, cute::cosize_v<SmemLayoutA>> A;
  alignas(128) cute::ArrayEngine<ElementB, cute::cosize_v<SmemLayoutB>> B;
};

extern __shared__ char shared_memory[];
using Storage = SharedStorage<TA, TB, SmemLayoutA, SmemLayoutB>;
Storage& storage = *reinterpret_cast<Storage*>(shared_memory);

Tensor sA = make_tensor(make_smem_ptr(storage.A.begin()), SmemLayoutA{});
```

## Debug

- Use `print(...)` for CuTe objects such as shapes, strides, layouts, tensors, atoms, and tiled objects.
- Use `print_layout(...)` to inspect rank-2 layout coordinate-to-offset mappings.
- Use `print_tensor(...)` for rank-1 through rank-4 tensor values when the tensor supports printing.
- Use `print_latex(...)` for layouts, `TiledCopy`, or `TiledMMA` when visualizing thread/value layouts.
- On device, guard prints with `thread0()` or `thread(tid, bid)` and remove device printing from performance paths after debugging.
- Use `compute-sanitizer` for memory and race debugging when kernels fault or produce invalid results.

```c++
if (thread0()) {
  print("gA: "); print(gA); print("\n");
  print_layout(layout(gA));
}
```
