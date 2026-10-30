---
name: cute-layout
description: Use when the user asks about C++ CuTe layouts, Shape, Stride, make_layout, layout algebra, composition, group_modes, zipped_divide, local_tile, local_partition, tile_to_shape, or tensor slicing/partitioning.
---

# CuTe C++ Layout

Use this skill for C++ CuTe layout and tensor algebra.

## Layout Construction

- Define `shape`, `stride`, and `layout` separately before constructing nontrivial layouts.
- Use `make_shape(...)` and `make_stride(...)`; do not hand-roll tuple types unless the surrounding code is already type-level.
- Use `make_layout(shape, stride)` for explicit layouts.
- Use `make_layout(shape)` only when the default `LayoutLeft{}` stride generation is intentionally correct.
- Use `LayoutRight{}` only when that stride generation is the intended mapping; hierarchical shapes can make row/column-major intuition misleading.
- Use CuTe static integer aliases such as `_1`, `_2`, and `_128` when available; use `Int<Val>` consistently when a grouped value includes an unsupported static value.
- Assert shape/stride compatibility with `CUTE_STATIC_ASSERT_V(congruent(shape, stride))` when a kernel depends on it.

```c++
auto shape = make_shape(_128{}, _32{});
auto stride = make_stride(_1{}, _128{});
auto layout = make_layout(shape, stride);

auto row_like = make_layout(shape, LayoutRight{});

CUTE_STATIC_ASSERT_V(congruent(cute::shape(layout), cute::stride(layout)));
```

## Layout Basics

- These structural utilities accept `Layout` or `Tensor` operands unless a bullet says otherwise.
- `rank(x)` returns the number of modes at the selected level; `rank<I...>(x)` descends into a nested mode.
- `depth(x)` returns the nesting depth of the shape or tuple structure.
- `shape(x)` and `shape<I...>(x)` return the shape or a selected subshape.
- `stride(x)` and `stride<I...>(x)` return stride information for layouts or tensor layouts.
- `size(x)` returns logical element count; `size<I...>(x)` returns the size of a selected mode.
- `cosize(layout)` returns the storage span implied by the layout, not necessarily the logical element count.
- `get<I...>(x)` extracts nested tuple or layout components.
- `layout<I...>(tensor)` and `tensor<I...>(tensor)` extract tensor layout or subtensor components.
- `compatible(a, b)` checks whether coordinates of one layout can be used with another; `congruent(a, b)` checks matching tuple profiles.
- `weakly_congruent(a, b)` checks weaker profile compatibility where scalar leaves in `a` may match nested structure in `b`.
- `flatten(x)` removes nested tuple structure from a shape, layout, or tensor view.
- `slice(coord, layout)` returns a layout subview. `layout(coord)` returns a layout subview only when `coord` contains `_`; otherwise it maps the coordinate to a linear index.

```c++
auto total = size(layout);
auto m_size = size<0>(layout);
auto span = cosize(layout);
auto s0 = shape<0>(layout);
auto d0 = stride<0>(layout);
```

```c++
auto layout = make_layout(
    make_shape(make_shape(_2{}, _3{}), _4{}),
    make_stride(make_stride(_16{}, _4{}), _1{}));

auto total = size(layout);                  // 24
auto mode_size = size<0>(layout);           // 6
auto outer_rank = rank(layout);             // 2
auto nested_depth = depth(layout);          // 2
auto layout_shape = shape(layout);          // ((_2,_3),_4)
auto mode_shape = shape<0>(layout);         // (_2,_3)
auto storage_span = cosize(layout);         // 28

auto flat_layout = flatten(layout);         // shape: (_2,_3,_4), stride: (_16,_4,_1)
auto sliced_layout = layout(make_coord(make_coord(_,_), 1));
// shape: (_2,_3), stride: (_16,_4)

auto same_profile = congruent(
    make_shape(_2{}, make_shape(_3{}, _4{})),
    make_shape(_5{}, make_shape(_6{}, _7{}))); // true
auto weak_profile = weakly_congruent(
    make_shape(_1{}, _1{}),
    make_shape(_5{}, make_shape(_6{}, _7{}))); // true
auto compatible_profile = compatible(
    make_shape(_2{}, _3{}),
    make_shape(_2{}, _3{})); // true
```

## Layout Algebra

- `coalesce(x)` simplifies a layout or tensor view without changing its 1-D coordinate mapping.
- `coalesce(x, profile)` coalesces within the requested profile.
- `composition(a, b)` builds `a o b`; use it when changing the coordinate domain of a layout or tensor.
- When `composition(...)`, `coalesce(...)`, `filter(...)`, or `filter_zeros(...)` receives a `Tensor`, the result is a tensor view with the same data iterator and transformed layout.
- `complement(layout, cotarget)` builds the repetition/rest layout used by divide/product operations.
- `filter(x)` and `filter_zeros(x)` simplify layout or tensor structure with static-1 or zero-stride modes.
- `group<B,E>(layout)` groups layout modes in `[B, E)`, while `group_modes<B,E>(tensor)` applies that grouping to a tensor view.
- `right_inverse(layout)` and `left_inverse(layout)` are layout-only inverse helpers.

```c++
auto compact = coalesce(layout);
auto projected = composition(layout, tile_layout);
auto grouped_layout = group<0,2>(layout);
auto grouped_tensor = group_modes<0,2>(tensor);
auto inv = right_inverse(layout);
```

```c++
auto coalesce_input = make_layout(
    make_shape(_2{}, make_shape(_1{}, _6{})),
    make_stride(_1{}, make_stride(_6{}, _2{})));
auto coalesced = coalesce(coalesce_input);                  // shape: _12, stride: _1
auto coalesced_by_mode = coalesce(coalesce_input, Step<_1,_1>{});
// shape: (_2,_6), stride: (_1,_2)

auto zero_stride = make_layout(
    make_shape(_2{}, _3{}, _4{}),
    make_stride(_12{}, _0{}, _1{}));
auto without_zeros = filter_zeros(zero_stride); // shape: (_2,_1,_4), stride: (_12,_0,_1)
auto filtered = filter(zero_stride);            // shape: (_2,_4), stride: (_12,_1)

auto plain_layout = make_layout(
    make_shape(_2{}, _3{}, _4{}),
    make_stride(_12{}, _4{}, _1{}));
auto grouped_layout = group<0,2>(plain_layout); // shape: ((_2,_3),_4)

auto linear = make_layout(Int<20>{}, Int<2>{});
auto matrix_coords = make_layout(
    make_shape(Int<5>{}, Int<4>{}),
    make_stride(Int<4>{}, Int<1>{}));
auto matrix_view = composition(linear, matrix_coords); // shape: (5,4), stride: (8,2)

auto rest = complement(make_layout(_4{}), _24{}); // _6:_4

auto bijective = make_layout(make_shape(_2{}, _3{}), make_stride(_3{}, _1{}));
auto left_inv = left_inverse(bijective);
auto right_inv = right_inverse(bijective);
auto domain_identity = composition(left_inv, bijective);     // coordinates round-trip
auto codomain_identity = composition(bijective, right_inv);  // offsets round-trip
```

## Tensor/Layout Tiling And Partitioning

### Divide

- Divide functions split a `Layout` or `Tensor` by a tiler and return the same kind of object.
- For `Tensor` overloads, divide functions keep the tensor data iterator and transform the tensor layout.
- Use `logical_divide(target, tiler)` for direct logical partitioning by a tiler.
- Use `zipped_divide(target, tiler)` for the standard `(Tile, Rest)` view used by many tiled flows.
- Use `tiled_divide(target, tiler)` when the tiler structure should remain explicit in the result.
- Use `flat_divide(target, tiler)` when the tiled result should be flattened.
- For `target` shape `(M, N, L, ...)` and tiler shape `(TileM, TileN)`, result mode structures are:
  - `logical_divide`: `((TileM, RestM), (TileN, RestN), L, ...)`
  - `zipped_divide`: `((TileM, TileN), (RestM, RestN, L, ...))`
  - `tiled_divide`: `((TileM, TileN), RestM, RestN, L, ...)`
  - `flat_divide`: `(TileM, TileN, RestM, RestN, L, ...)`

```c++
Tensor tensor = make_tensor<float>(Shape<_8,_24>{});
auto tile_shape = Shape<_4,_8>{};

auto logical = logical_divide(tensor, tile_shape); // shape: ((_4,_2),(_8,_3))
auto zipped = zipped_divide(tensor, tile_shape);   // shape: ((_4,_8),(_2,_3))
auto tiled = tiled_divide(tensor, tile_shape);     // shape: ((_4,_8),_2,_3)
auto flat = flat_divide(tensor, tile_shape);       // shape: (_4,_8,_2,_3)

auto layout_target = make_layout(make_shape(_8{}, _24{}));
auto layout_zipped = zipped_divide(layout_target, tile_shape); // shape: ((_4,_8),(_2,_3))
```

### Product

- Product functions build larger layout structures from a layout block and tiler; use them with layouts, not tensors.
- Use `logical_product(block, tiler)` for direct logical product composition.
- Use `zipped_product(block, tiler)` when the result should group block modes and tiler modes together.
- Use `tiled_product(block, tiler)` when the tiler layout should remain explicit in the result.
- Use `flat_product(block, tiler)` when the product should be flattened.
- Use `blocked_product(block, tiler)` or `raked_product(block, tiler)` when that blocked or raked ordering is required by a thread/value mapping.
- For a rank-2 block layout with shape `(M, N)` and a rank-2 tiler layout with shape `(TileM, TileN)`, common result mode structures are:
  - `logical_product`: `((M, N), (TileM, TileN))`
  - `zipped_product`: `((M, N), (TileM, TileN))`
  - `tiled_product`: `((M, N), TileM, TileN)`
  - `flat_product`: `(M, N, TileM, TileN)`
- `blocked_product` and `raked_product` are rank-sensitive product variants that reassociate like modes after the product.
- Prefer a layout tiler for these layout-product examples; tuple/shape tilers apply products mode by mode and can produce a different hierarchy.
- `make_tiled_copy(...)` uses a raked-product style combination of thread and value layouts; make thread/value layouts explicit when copy ownership matters.

```c++
auto block_layout = make_layout(make_shape(_2{}, _3{}));
auto tiler_shape = make_shape(_4{}, _5{});
auto tiler_layout = make_layout(tiler_shape);

auto logical = logical_product(block_layout, tiler_layout); // shape: ((_2,_3),(_4,_5))
auto zipped = zipped_product(block_layout, tiler_layout);   // shape: ((_2,_3),(_4,_5))
auto tiled = tiled_product(block_layout, tiler_layout);     // shape: ((_2,_3),_4,_5)
auto flat = flat_product(block_layout, tiler_layout);       // shape: (_2,_3,_4,_5)
auto blocked = blocked_product(block_layout, tiler_layout); // shape: ((_2,_4),(_3,_5))
auto raked = raked_product(block_layout, tiler_layout);     // shape: ((_4,_2),(_5,_3))

auto thr_layout = make_layout(make_shape(_32{}, _8{}));     // threads: (_32,_8)
auto val_layout = make_layout(make_shape(_4{}, _1{}));      // values: (_4,_1)

auto tv_source = raked_product(thr_layout, val_layout);     // layout for thread/value ownership
```

### Helper

- Use `tile_to_shape(atom, target_shape, order)` to repeat or fit a layout atom to a target shape.
- `tile_to_shape(...)` can preserve atom/rest hierarchy in the returned shape; do not assume `shape(result)` is the flat target shape.
- Use `local_tile(tensor, tiler, coord, Step<...>{})` to extract one tiled tensor view; it is equivalent to a zipped divide followed by rest-coordinate selection.
- Use `local_partition(tensor, thread_layout, thread_idx, Step<...>{})` to partition a tensor across a thread layout.
- Use `inner_partition(...)` or `outer_partition(...)` directly only when the code needs that exact slice form; prefer `local_tile(...)` and `local_partition(...)` for common CTA and thread partitioning patterns.
- Use `Step<_1, X, _1>{}` style projections to select the modes of a higher-rank tiler or coordinate.
- When slicing tensors directly, use `_` inline to keep modes.

```c++
auto atom = make_layout(make_shape(_2{}, _2{}), make_stride(_2{}, _1{}));
auto tiled_layout = tile_to_shape(atom, make_shape(_4{}, _6{})); // shape: ((_2,_2),(_2,_3))

Tensor tensor = make_tensor<float>(Shape<_8,_24>{});
auto tile_shape = Shape<_4,_8>{};
auto tiled = zipped_divide(tensor, tile_shape); // shape: ((_4,_8),(_2,_3))

Tensor tile = local_tile(tensor, tile_shape, make_coord(0, 1)); // shape: (_4,_8)

auto partition_layout = make_layout(tile_shape, make_stride(_8{}, _1{}));
Tensor partition = local_partition(tensor, partition_layout, threadIdx.x);
// shape: (_2,_3)

auto cta_coord = make_coord(blockIdx.x, blockIdx.y, _);

Tensor gA = local_tile(mA, cta_tiler, cta_coord, Step<_1, X,_1>{});
Tensor gB = local_tile(mB, cta_tiler, cta_coord, Step< X,_1,_1>{});
Tensor gC = local_tile(mC, cta_tiler, cta_coord, Step<_1,_1, X>{});

Tensor tAgA = local_partition(gA, thread_layout, threadIdx.x);
Tensor subview = tensor(_, rest_coord);
```

## Static And Dynamic Layouts

- Static layouts give more compile-time information, stronger validation, and better code generation.
- Dynamic layouts are appropriate for runtime problem shapes and leading dimensions.
- Keep CTA tile shapes, SMEM layouts, MMA layouts, and copy thread/value layouts static unless the surrounding API requires runtime values.
- Shared-memory owning tensors and `cute::ArrayEngine` allocations require static storage sizes.
