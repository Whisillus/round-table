---
name: cutedsl-tensor
description: Use when the user asks about CuTe DSL tensor construction, tensor.load, tensor.store, cute.make_tensor, make_identity_tensor, make_rmem_tensor, make_rmem_tensor_like, make_fragment_like, recast_tensor, domain_offset, TensorSSA helpers, or tensor printing/debugging.
---

# CuTe DSL Tensor

Use this skill for CuTe DSL tensor construction, register-memory tensors, fragments, tensor views, tensor loads/stores, and TensorSSA helper values.

## Tensor Construction

- Use `cute.make_tensor(iterator, layout)` to pair an engine with a layout.
- `iterator` can be a `cute.Pointer`, an integer or integer tuple for coordinate tensors, or a supported MLIR iterator value such as an SMEM descriptor.
- `layout` can be a shape tuple, `cute.Layout`, or normal `cute.ComposedLayout`; avoid composed layouts with custom inner functions.
- Define `shape`, `stride`, and `layout` separately before constructing tensors.
- Use `cute.make_identity_tensor(shape)` when the tensor should carry logical coordinates for predication or coordinate transforms.

```python
shape = (m, n)
stride = (n, 1)
layout = cute.make_layout(shape, stride=stride)
tensor = cute.make_tensor(ptr, layout)

coord_shape = (m, n)
coord_tensor = cute.make_identity_tensor(coord_shape)
```

## Register Tensors And Fragments

- Use `cute.make_rmem_tensor(shape_or_layout, dtype)` to allocate register-memory tensor storage.
- Use `cute.make_rmem_tensor_like(src, dtype=None)` when register storage should mirror a tensor, TensorSSA, layout, or composed layout.
- Pass `dtype` when the source is a layout or coordinate tensor; otherwise the source tensor element type can be inferred.
- Use `cute.make_fragment_like(src, dtype=None)` when the local convention expects fragment-shaped storage; with a tensor input it returns register-memory storage, and with a layout input it returns a fragment layout unless `dtype` is supplied.
- Prefer constructing accumulator or temporary fragment shapes from existing partitioned tensor shapes.

```python
acc_dtype = cutlass.Float32

acc = cute.make_rmem_tensor(acc_shape, acc_dtype)
tmp = cute.make_rmem_tensor_like(tensor_view, acc_dtype)

fragment_layout = cute.make_fragment_like(tensor_view.layout)
fragment = cute.make_fragment_like(tensor_view, acc_dtype)
```

## Tensor Views And Reinterpretation

- Use `cute.recast_tensor(tensor, dtype)` to reinterpret the same storage with a different element type; it adjusts the iterator and layout by element-width ratio.
- Use `cute.domain_offset(coord, tensor)` to shift the tensor iterator by the layout offset of `coord` while preserving the layout.
- Use `tensor.iterator.align(bytes)` before rebuilding a tensor when an example or copy path requires stronger pointer alignment.
- Use direct tensor indexing with inline coordinates for subviews.

```python
raw_tensor = cute.recast_tensor(tensor, raw_dtype)
offset_tensor = cute.domain_offset((m_offset, n_offset), tensor)

aligned_tensor = cute.make_tensor(tensor.iterator.align(16), tensor.layout)
tile = tensor[(None, rest_coord)]
```

## Tensor Loads And Stores

- Use `tensor.load(mask=None, pass_thru=None)` to load a memory-backed `cute.Tensor` into a `TensorSSA`; the tensor shape must be static.
- Use `tensor.store(data, mask=None)` to store a `TensorSSA` back to a memory-backed tensor; `data.shape` must match the destination tensor shape.
- `mask` and `pass_thru` are TensorSSA values with compatible shape. On masked loads, `pass_thru` supplies values for masked-off elements; on masked stores, masked-off elements are not written.
- Use `tensor[coord]` to load a scalar element when `coord` has no `None` entries and the element type supports scalar dereference.
- Use `tensor[coord] = value` to store a scalar element, or assign a matching TensorSSA to a slice coordinate that contains `None`.
- Use `tensor.fill(value)` to write one scalar value to every element of a static-size tensor.

```python
values = tensor.load()                    # TensorSSA with tensor.shape
scaled = values * 2.0

first = tensor[(0, 0)]                    # scalar load
tensor[(0, 0)] = scaled[(0, 0)]           # scalar store

tile = tensor[(None, rest_coord)]         # tensor subview
tile.store(scaled[(None, rest_coord)])

tensor.store(scaled)
tensor.fill(0.0)
```

## TensorSSA Helpers

- `TensorSSA` helpers construct or transform value tensors, not memory-backed tensor views.
- `cute.full(shape, fill_value, dtype)` returns a TensorSSA with every element set to `fill_value`; `shape` must be static and `fill_value` is converted to `dtype`.
- `cute.full_like(x, fill_value, dtype=None)` returns a TensorSSA with `x.shape`; it uses `x.dtype` unless `dtype` overrides it.
- `cute.zeros_like(x, dtype=None)` is `full_like(x, 0, dtype)` and returns a zero TensorSSA with `x.shape`.
- `cute.ones_like(x, dtype=None)` is `full_like(x, 1, dtype)` and returns a one-filled TensorSSA with `x.shape`.
- `cute.empty_like(x, dtype=None)` returns a TensorSSA with `x.shape` and selected dtype; current local source constructs it through `full_like(x, 0, dtype)`.
- `cute.where(cond, x, y)` selects elements from `x` or `y`; `cond` must be Boolean TensorSSA, at least one of `x` or `y` must be TensorSSA, and `x` and `y` must have the same dtype after scalar promotion.
- `cute.any_(x)` reduces TensorSSA `x` to a Boolean that is true when any element is nonzero.
- `cute.all_(x)` reduces TensorSSA `x` to a Boolean that is true when all elements are nonzero.

```python
shape = (2, 4)
values = cute.full(shape, 3.0, cutlass.Float32)  # TensorSSA, shape: (2, 4)

zeros = cute.zeros_like(values)                  # TensorSSA, shape: (2, 4)
ones = cute.ones_like(values)                    # TensorSSA, shape: (2, 4)
scratch = cute.empty_like(values)                # TensorSSA, shape: (2, 4)
half_values = cute.full_like(values, 0.5)        # TensorSSA, dtype from values

positive = values > zeros                        # Boolean TensorSSA
masked = cute.where(positive, values, zeros)     # TensorSSA, shape: (2, 4)

has_value = cute.any_(masked)                    # Boolean
all_nonzero = cute.all_(masked)                  # Boolean
```

## TensorSSA Operations

- Use TensorSSA indexing for scalar extraction or value-tensor slicing. A coordinate without `None` returns a scalar element; a coordinate with `None` returns a TensorSSA slice.
- Use normal Python operators for elementwise TensorSSA math: `+`, `-`, `*`, `/`, `//`, `%`, `**`, comparisons, unary `-`, `abs(...)`, and bitwise `&`, `|`, `^` where the dtype supports them.
- Binary TensorSSA operations broadcast compatible shapes and promote scalar operands automatically.
- Use `value.broadcast_to(target_shape)` when a broadcasted TensorSSA should be explicit before later operations.
- Use `value.reshape(shape)` only when the total element count is unchanged.
- Use `value.to(dtype)` for numeric conversion with the same shape.
- Use `value.bitcast(dtype)` for bit reinterpretation; total bit width is preserved and the result shape is flattened.
- Use `value.reduce(cute.ReductionOp.ADD|MUL|MAX|MIN, init_val, reduction_profile)` for local reductions. `None` in `reduction_profile` keeps a mode; concrete entries reduce that mode.
- Use `TensorSSA.from_vector(...)` and `value.to_vector(...)` only for explicit low-level vector interop.

```python
values = cute.full((2, 4), 1.0, cutlass.Float32)
zeros = cute.zeros_like(values)

positive = values > zeros                 # Boolean TensorSSA
clamped = cute.where(positive, values, zeros)
scaled = clamped * 2.0 + 1.0

first = scaled[(0, 0)]                    # scalar element
row = scaled[(None, 0)]                   # TensorSSA slice

broadcasted = row.broadcast_to(scaled.shape)
reshaped = scaled.reshape((8,))
as_f16 = scaled.to(cutlass.Float16)
as_i32_bits = scaled.bitcast(cutlass.Int32)

sum_by_row = scaled.reduce(
    cute.ReductionOp.ADD,
    0.0,
    (None, 1),
)  # shape: (2,)
```

## Tensor Debugging

- Use `cute.print_tensor(tensor, verbose=False)` for runtime-readable tensor contents when the tensor supports direct printing.
- Use `print(tensor.layout)`, `print(tensor.shape)`, or `print(tensor.element_type)` for compile-time/JIT-trace inspection.
- Use `cute.print_tensor(..., verbose=True)` only when extra metadata is needed.

```python
print("tensor shape:", tensor.shape)
print("tensor layout:", tensor.layout)
cute.print_tensor(tensor)
```
