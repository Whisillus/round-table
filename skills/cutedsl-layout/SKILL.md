---
name: cutedsl-layout
description: Use when the user asks about CuTe DSL layouts, tensors, layout algebra, local_tile, local_partition, zipped_divide, composition, group_modes, make_layout_tv, or tensor slicing/partitioning.
---

# CuTe DSL Layout

Use this skill for CuTe DSL layout and tensor algebra.

## Layout Construction

- Define `shape` and `stride` separately before calling `cute.make_layout(...)`.
- Use `cute.make_layout(shape, stride=stride)`; `stride` is keyword-only.
- Do not rely on the default stride when constructing layouts for kernels.
- Do not use `cute.make_shape(...)`; CuTe DSL uses tuples for shapes.
- Use `cute.make_layout_tv(thr_layout, val_layout)` when constructing a thread-value layout and you need both `tiler_mn` and `layout_tv` explicitly.

```python
shape = (block_m, block_k)
stride = (block_k, 1)
layout = cute.make_layout(shape, stride=stride)

thr_layout = cute.make_layout(thr_shape, stride=thr_stride)
val_layout = cute.make_layout(val_shape, stride=val_stride)
tiler_mn, layout_tv = cute.make_layout_tv(thr_layout, val_layout)
```

## Layout Basic

- The structural utilities in this section accept a `Layout` or `Tensor` unless a bullet says otherwise.
- `cute.size(x)` returns the number of logical elements in the domain; `cute.size(x, mode=[i])` returns the size of a selected mode.
- `cute.rank(x)` returns the number of modes at the selected level.
- `cute.depth(x)` returns the nesting depth of the shape or tuple structure.
- `cute.shape(x)` returns the shape tuple; `cute.shape(x, mode=i)` returns one selected mode of that shape.
- `cute.cosize(x)` returns the codomain extent needed to address all elements, usually the storage span implied by the layout.
- `cute.coalesce(x)` merges adjacent compatible modes and simplifies the layout or tensor view without changing logical elements.
- `cute.flatten(x)` removes nested tuple structure from a shape, layout, or tensor view.
- `cute.filter(x)` applies CuTe filtering rules to simplify layout or tensor structure.
- `cute.filter_zeros(x)` removes zero-stride dimensions from a layout or tensor view.
- `cute.slice_(x, coord)` selects a subview: `None` keeps a mode, while a concrete coordinate fixes and removes that mode.
- `cute.group_modes(x, begin, end)` collapses top-level modes in `[begin, end)` into one grouped mode.
- `cute.composition(lhs, rhs)` builds `lhs(rhs(coord))`; use it to transform the coordinate domain of a layout or tensor.
- `cute.is_congruent(a, b)` checks whether two shape/profile structures have the same nested tuple structure.
- `cute.is_weakly_congruent(a, b)` checks compatibility where scalar leaves may match nested structure.
- `cute.left_inverse(layout)` and `cute.right_inverse(layout)` are `Layout`-only inverse helpers for layout algebra.

```python
x = layout_or_tensor

total = cute.size(x)
m_size = cute.size(x, mode=[0])
x_rank = cute.rank(x)
x_depth = cute.depth(x)
x_shape = cute.shape(x)
x_cosize = cute.cosize(x)

compact_x = cute.coalesce(x)
flat_x = cute.flatten(x)
filtered_x = cute.filter(x)
nonzero_x = cute.filter_zeros(x)
sliced_x = cute.slice_(x, (None, rest_coord))
grouped_x = cute.group_modes(x, 0, 2)

same_profile = cute.is_congruent(cute.shape(x), cute.shape(other_x))
```

```python
# layout shape: ((2, 3), 4), with padding between outer rows
shape = ((2, 3), 4)
stride = ((16, 4), 1)
layout = cute.make_layout(shape, stride=stride)

total = cute.size(layout)                 # 24
mode_size = cute.size(layout, mode=[0])   # 6
outer_rank = cute.rank(layout)            # 2
nested_depth = cute.depth(layout)         # 2
layout_shape = cute.shape(layout)         # ((2, 3), 4)
mode_shape = cute.shape(layout, mode=0)   # (2, 3)
storage_span = cute.cosize(layout)        # 28

flat_layout = cute.flatten(layout)        # shape: (2, 3, 4)
sliced_layout = cute.slice_(layout, ((None, None), 1))  # shape: (2, 3)

plain_shape = (2, 3, 4)
plain_stride = (12, 4, 1)
plain_layout = cute.make_layout(plain_shape, stride=plain_stride)
grouped_layout = cute.group_modes(plain_layout, 0, 2)  # shape: ((2, 3), 4)

coalesce_shape = (2, (1, 6))
coalesce_stride = (1, (6, 2))
coalesce_input = cute.make_layout(coalesce_shape, stride=coalesce_stride)
coalesced = cute.coalesce(coalesce_input)  # shape: 12, stride: 1

zero_shape = (2, 3, 4)
zero_stride_value = (12, 0, 1)
zero_stride = cute.make_layout(zero_shape, stride=zero_stride_value)
without_zeros = cute.filter_zeros(zero_stride)  # shape: (2, 1, 4)
filtered = cute.filter(zero_stride)             # shape: (2, 4)

linear_shape = 20
linear_stride = 2
linear = cute.make_layout(linear_shape, stride=linear_stride)
matrix_shape = (5, 4)
matrix_stride = (4, 1)
matrix_coords = cute.make_layout(matrix_shape, stride=matrix_stride)
matrix_view = cute.composition(linear, matrix_coords)  # shape: (5, 4), stride: (8, 2)

same_profile = cute.is_congruent((2, (3, 4)), (5, (6, 7)))  # True
weak_profile = cute.is_weakly_congruent((1, 1), (5, (6, 7)))  # True

bijective_shape = (2, 3)
bijective_stride = (3, 1)
bijective = cute.make_layout(bijective_shape, stride=bijective_stride)
left_inv = cute.left_inverse(bijective)
right_inv = cute.right_inverse(bijective)
domain_identity = cute.composition(left_inv, bijective)     # coordinates round-trip
codomain_identity = cute.composition(bijective, right_inv)  # offsets round-trip
```

## Tensor Tiling And Partitioning

### Divide

- Divide functions split a `Layout` or `Tensor` by a tiler and return the same kind of object.
- Use `cute.logical_divide(target, tiler)` for the direct logical partitioning by a tiler.
- Use `cute.zipped_divide(target, tiler)` for the standard `(Tile, Rest)` view used by many tiled tensor flows.
- Use `cute.tiled_divide(target, tiler)` when the tiler structure should remain tiled rather than gathered into `(Tile, Rest)` form.
- Use `cute.flat_divide(target, tiler)` when the tiled result should be flattened.
- For `target` shape `(M, N, L, ...)` and tiler shape `(TileM, TileN)`, the result mode structures are:
  - `logical_divide`: `((TileM, RestM), (TileN, RestN), L, ...)`
  - `zipped_divide`: `((TileM, TileN), (RestM, RestN, L, ...))`
  - `tiled_divide`: `((TileM, TileN), RestM, RestN, L, ...)`
  - `flat_divide`: `(TileM, TileN, RestM, RestN, L, ...)`

```python
# tensor shape: (8, 24)
tile_shape = (4, 8)

logical = cute.logical_divide(tensor, tile_shape)  # ((4, 2), (8, 3))
zipped = cute.zipped_divide(tensor, tile_shape)    # ((4, 8), (2, 3))
tiled = cute.tiled_divide(tensor, tile_shape)      # ((4, 8), 2, 3)
flat = cute.flat_divide(tensor, tile_shape)        # (4, 8, 2, 3)
```

### Product

- Product functions build larger layout structures from a layout block and tiler; use them with `Layout` or `ComposedLayout` values, not tensors.
- Use `cute.logical_product(block, tiler)` for direct logical product composition.
- Use `cute.zipped_product(block, tiler)` when the result should group tiler modes and block modes together.
- Use `cute.tiled_product(block, tiler)` when the tiler layout should remain explicit in the result.
- Use `cute.flat_product(block, tiler)` when the product should be flattened.
- Use `cute.raked_product(block, tiler)` or `cute.blocked_product(block, tiler)` when a raked or blocked product layout is required by the surrounding algorithm.
- For a rank-2 block layout with shape `(M, N)` and a rank-2 tiler layout with shape `(TileM, TileN)`, common result mode structures are:
  - `logical_product`: `((M, N), (TileM, TileN))`
  - `zipped_product`: `((M, N), (TileM, TileN))`
  - `tiled_product`: `((M, N), TileM, TileN)`
  - `flat_product`: `(M, N, TileM, TileN)`
- `blocked_product` and `raked_product` are rank-sensitive product variants that reassociate like modes after the product; use them only when that blocked or raked ordering is required.

```python
# block shape: (2, 3), tiler shape: (4, 5)
block_shape = (2, 3)
block_stride = (3, 1)
block_layout = cute.make_layout(block_shape, stride=block_stride)

tiler_shape = (4, 5)
tiler_stride = (5, 1)
tiler_layout = cute.make_layout(tiler_shape, stride=tiler_stride)

logical = cute.logical_product(block_layout, tiler_layout)  # ((2, 3), (4, 5))
zipped = cute.zipped_product(block_layout, tiler_layout)    # ((2, 3), (4, 5))
tiled = cute.tiled_product(block_layout, tiler_layout)      # ((2, 3), 4, 5)
flat = cute.flat_product(block_layout, tiler_layout)        # (2, 3, 4, 5)
blocked = cute.blocked_product(block_layout, tiler_layout)  # shape: ((2, 4), (3, 5))
raked = cute.raked_product(block_layout, tiler_layout)      # shape: ((4, 2), (5, 3))
```

### Helper

- Use `cute.tile_to_shape(atom, trg_shape, order)` to repeat or fit a layout atom to a target shape.
- Use `cute.local_tile(tensor, tiler, coord, proj=...)` to extract one tiled tensor view; it is equivalent to a zipped divide followed by rest-coordinate selection.
- Use `cute.local_partition(tensor, tiler, index, proj=...)` when building an indexed partition from a tensor and tiler.
- For `atom` shape `(AtomM, AtomN)` and target shape `(M, N)`, `cute.tile_to_shape(atom, (M, N), order)` returns a layout with logical extents `(M, N)` but may preserve atom/rest hierarchy in `cute.shape(result)`.
- For `tensor` shape `(8, 24)` and tiler shape `(4, 8)`, `cute.zipped_divide(tensor, tiler)` has mode structure `((4, 8), (2, 3))`.
- `cute.local_tile(tensor, tiler, rest_coord)` slices the rest mode and keeps the tile mode, so the result shape is `(4, 8)`.
- `cute.local_partition(tensor, tiler_layout, index)` slices the tile mode and keeps the rest mode, so the result shape is `(2, 3)` for one selected tile coordinate.
- When indexing tensors, write coordinates inline rather than defining a separate coordinate variable unless the coordinate is reused.

```python
atom_shape = (2, 2)
atom_stride = (2, 1)
atom = cute.make_layout(atom_shape, stride=atom_stride)
tiled_layout = cute.tile_to_shape(atom, (4, 6), (0, 1))  # shape: ((2, 2), (2, 3))

tile_shape = (4, 8)
tiled = cute.zipped_divide(tensor, tile_shape)  # ((4, 8), (2, 3))

tile = cute.local_tile(tensor, tile_shape, (0, 1))  # (4, 8)

partition_stride = (8, 1)
partition_layout = cute.make_layout(tile_shape, stride=partition_stride)
partition = cute.local_partition(tensor, partition_layout, tidx)  # (2, 3)

subview = tensor[(None, rest_coord)]
```

## Static And Dynamic Layouts

- Static layouts give more compile-time information and may generate separate compiled kernels for different shapes.
- Dynamic layouts can reuse a compiled function across compatible runtime shapes.
- Use `cutlass.Constexpr` for compile-time tile sizes and configuration values.
- When framework tensors are passed directly, CuTe DSL may infer dynamic layout behavior; when using DLPack conversion explicitly, verify whether the resulting layout is static or dynamic before assuming cache reuse.
