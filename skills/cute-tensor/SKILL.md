---
name: cute-tensor
description: Use when the user asks about C++ CuTe Tensor construction, make_tensor, make_gmem_ptr, make_smem_ptr, make_tensor_like, make_fragment_like, make_identity_tensor, recast, domain_offset, tensor slicing, or tensor printing/debugging.
---

# CuTe C++ Tensor

Use this skill for C++ CuTe tensor construction, memory-space tagged tensors, register tensors, fragments, tensor views, coordinate tensors, and tensor debugging.

## Tensor Construction

- Use `make_tensor(iterator, layout)` to pair an engine/iterator with a layout.
- Tag raw global pointers with `make_gmem_ptr(ptr)` and raw shared-memory pointers with `make_smem_ptr(ptr)` before constructing tensors used by CuTe algorithms.
- Define `shape`, `stride`, and `layout` separately for nontrivial tensors.
- Use `make_tensor(ptr, shape)` or `make_tensor(ptr, shape, stride)` only when the shorthand is clear and matches surrounding style.
- In generic functions, pass tensors by reference or const reference when copying an owning tensor would be surprising.
- Use CuTe GEMM mode order consistently: A `(M,K)`, B `(N,K)`, C `(M,N)`.

```c++
auto shape = make_shape(M, K);
auto stride = make_stride(_1{}, ldA);
auto layout = make_layout(shape, stride);

Tensor mA = make_tensor(make_gmem_ptr(A), layout);  // (M,K)
```

## Tensor Fundamentals

- `tensor.data()` returns the iterator or engine held by the tensor.
- `tensor.size()` returns the total logical element count.
- `rank(tensor)`, `depth(tensor)`, `shape(tensor)`, `size(tensor)`, and `layout(tensor)` inspect the whole tensor.
- `rank<I...>(tensor)`, `depth<I...>(tensor)`, `shape<I...>(tensor)`, `size<I...>(tensor)`, and `layout<I...>(tensor)` inspect a selected nested mode.
- `tensor<I...>(tensor)` extracts the subtensor for a selected mode; use it when the mode is known statically.

```c++
auto ptr = t.data();
auto total = t.size();
auto tensor_shape = shape(t);
auto tensor_layout = layout(t);

auto mode0_shape = shape<0>(t);
auto mode0_size = size<0>(t);
auto nested_rank = rank<0>(t);
Tensor mode0 = tensor<0>(t);
```

## Register Tensors And Fragments

- Use `make_tensor<T>(layout_or_shape)` to create an owning register-memory tensor with static shape/storage.
- Use `make_tensor_like<T>(tensor_or_layout)` to create register storage with the same logical shape/order as a source tensor or layout.
- Use `make_tensor_like(tensor)` when the value type should match the source tensor.
- Use `make_fragment_like<T>(tensor_or_layout)` for fragment-shaped register storage, especially after `TiledCopy` or `TiledMMA` partitioning.
- `make_tensor_like(...)` preserves the source shape and tries to preserve stride order; `make_fragment_like(...)` gives special treatment to mode 0, allocating it with `LayoutLeft` because mode 0 commonly represents atom values for copy or MMA fragments.
- Prefer building accumulator and temporary fragment shapes from already partitioned tensors.

```c++
Tensor frag = make_tensor_like(thr_tile_S);
Tensor acc = make_fragment_like<float>(tCgC);

Tensor tCrC = thr_mma.make_fragment_C(tCgC);
Tensor tCrA = thr_mma.make_fragment_A(tCsA);
Tensor tCrB = thr_mma.make_fragment_B(tCsB);
```

## Tensor Views And Reinterpretation

- Use tensor slicing with `tensor(...)`; pass `_` to keep a mode and concrete coordinates to fix modes.
- Use `tensor<I...>(tensor)` to extract a nested subtensor corresponding to a selected mode.
- Use `domain_offset(coord, tensor)` to shift the tensor iterator by the layout offset of `coord` while preserving the layout.
- Use `recast<NewT>(tensor)` to reinterpret storage with a different element type; it adjusts pointer and layout by element-width ratio.
- Treat `recast<NewT>(tensor)` as dangerous: local CuTe does not check dynamic integer divisibility or pointer alignment, so verify element-size divisibility and alignment before using it.
- Use `recast_ptr<NewT>(ptr)` only when pointer-level reinterpretation is needed outside a full tensor recast.

```c++
Tensor tile = tensor(_, rest_coord);
Tensor shifted = domain_offset(make_coord(m_offset, k_offset), tensor);
Tensor as_u128 = recast<uint128_t>(tensor);
```

## Tensor Access And Mutation

- Use `tensor(coord)` or `tensor(coords...)` for logical coordinate access.
- Use `tensor[idx]` for 1-D logical indexing or when local code already follows container-style access.
- Assign through tensor element access for scalar stores.
- Use CuTe algorithms such as `copy`, `copy_if`, `fill`, `clear`, and `axpby` for tensor-wide operations.
- Remember that tensor access uses the tensor layout to map logical coordinates to iterator offsets.

```c++
auto value = tensor(m, n);
tensor(m, n) = value + 1;

Tensor nested = make_tensor<float>(
    Shape<Shape<Int<4>, Int<5>>, Int<13>>{},
    Stride<Stride<_12,_1>, _64>{});

auto nested_coord = make_coord(make_coord(m0, m1), n);
nested(nested_coord) = value;

copy(src, dst);
copy_if(pred, src, dst);
clear(accumulators);
fill(fragment, Element{});
axpby(alpha, x, beta, y);
```

## Coordinate Tensors

- Use `make_identity_tensor(shape)` when a tensor should carry logical coordinates for predication or coordinate transforms.
- Tile and partition coordinate/predicate tensors through the same path as the data tensors they guard.
- For ragged-tile predicates, create the identity tensor from the original logical shape, apply the same `local_tile` and thread partitioning as the data, then test each coordinate with `elem_less(coord, original_shape)`.

```c++
Tensor cC = make_identity_tensor(shape(mC));
Tensor gC = local_tile(mC, cta_tiler, cta_coord, Step<_1,_1, X>{});
Tensor cta_cC = local_tile(cC, cta_tiler, cta_coord, Step<_1,_1, X>{});

Tensor tCgC = local_partition(gC, thread_layout, threadIdx.x);
Tensor tCcC = local_partition(cta_cC, thread_layout, threadIdx.x);

if (elem_less(tCcC(i), shape(mC))) {
  tCgC(i) = value;
}
```

## Tensor Debugging

- Use `print(tensor)`, `print(shape(tensor))`, and `print(layout(tensor))` for structural inspection.
- Use `print_tensor(tensor)` for rank-1 through rank-4 tensor contents when printing values is practical.
- Use `print_layout(layout(tensor))` when debugging a rank-2 coordinate-to-offset mapping.
- On device, guard prints with `thread0()` or `thread(tid, bid)` and remove device prints from performance paths.

```c++
if (thread0()) {
  print("tensor: "); print(tensor); print("\n");
  print_tensor(tensor);
}
```
