---
name: cutedsl-pipeline
description: Use when the user asks about CuTe DSL cutlass.pipeline, PipelineAsync, PipelineCpAsync, PipelineTmaAsync, PipelineTmaStore, PipelineState, producer/consumer stages, mbarrier-backed pipelines, or SM90 pipeline usage.
---

# CuTe DSL Pipeline

Use this skill for CuTe DSL pipeline APIs and producer/consumer protocols.


## Pipeline Class

Primary SM90 classes:

- `pipeline.PipelineAsync`: generic staged producer/consumer pipeline where async-thread producers fill stages and async-thread consumers release them.
- `pipeline.PipelineCpAsync`: staged pipeline for non-bulk `cp.async` global-to-shared producers and async-thread consumers.
- `pipeline.PipelineTmaAsync`: staged pipeline for TMA load producers and async-thread consumers; requires a per-stage `tx_count` and uses a transaction barrier for TMA completion.
- `pipeline.PipelineTmaStore`: synchronization wrapper for TMA store paths; it has a producer side only and no normal consumer wait/release path.

Use `PipelineAsync` when both sides are ordinary thread or warp code.

```python
pipe = pipeline.PipelineAsync.create(
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
    barrier_storage=barrier_storage,
)
```

Use `PipelineCpAsync` for non-bulk `cp.async` staged loads.

```python
pipe = pipeline.PipelineCpAsync.create(
    barrier_storage=barrier_storage,
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
)
```

Use `PipelineTmaAsync` for TMA load staged buffers.

```python
pipe = pipeline.PipelineTmaAsync.create(
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
    tx_count=tma_copy_bytes,
    barrier_storage=barrier_storage,
    cta_layout_vmnk=cta_layout_vmnk,
)
```

Use `PipelineTmaStore` for TMA store synchronization.

```python
pipe = pipeline.PipelineTmaStore.create(
    num_stages=num_stages,
    producer_group=producer_group,
)
```

`PipelineOrder` is an ordering helper, not a staged data-movement pipeline. Use it when multiple producer groups must execute in a fixed cyclic order across stages. `depth` is the number of stages per group, `length` is the number of ordered groups, and `group_id` is the current group's position in the order, usually in `[0, length)`. It allocates `depth * length` mbarrier slots from `barrier_storage`. `wait()` waits for this group's barrier at the current stage. `arrive()` signals the next group's barrier, `(group_id + 1) % length`, and advances the internal pipeline state. Prefer `PipelineAsync`, `PipelineCpAsync`, or `PipelineTmaAsync` for ordinary producer/consumer staged buffers.

```python
order = pipeline.PipelineOrder.create(
    barrier_storage=barrier_storage,
    depth=depth,
    length=length,
    group_id=group_id,
    producer_group=producer_group,
)

order.wait()
# do this group's ordered work for the current stage
order.arrive()
```

Other SM90 pipeline helpers:

- `pipeline.PipelineProducer` and `pipeline.PipelineConsumer`: participant helper wrappers around a pipeline object; they are not the usual top-level class-selection choice.

## Pipeline Agent

- `pipeline.Agent` describes the participant unit used for pipeline synchronization.
- Use it as the first argument to `pipeline.CooperativeGroup(...)`.
- Choose the agent that matches the granularity of the producer or consumer code path.

Common agent meanings:

- `pipeline.Agent.Thread`: individual thread granularity.
- `pipeline.Agent.Warp`: warp granularity.
- `pipeline.Agent.ThreadBlock`: CTA/thread-block granularity.
- `pipeline.Agent.ThreadBlockCluster`: CTA-cluster granularity.

```python
producer_agent = pipeline.Agent.Thread
consumer_agent = pipeline.Agent.Warp
```

## CooperativeGroup

- `pipeline.CooperativeGroup(agent, size)` describes how many `agent` units participate in a pipeline producer or consumer role.
- Pipeline constructors use cooperative groups to compute mbarrier arrive counts.
- A cooperative group is a synchronization descriptor; it does not select which kernel threads execute the producer or consumer code.
- Guard producer and consumer code so the actual participating threads match the declared cooperative groups.
- A mismatch can hang the pipeline or release a staged buffer too early.

Size meanings by agent:

- `pipeline.Agent.Thread`: `size` individual threads participate.
- `pipeline.Agent.Warp`: `size` warps participate, so the thread arrive count is `size * 32`.
- `pipeline.Agent.ThreadBlock`: `size` CTAs participate, so the arrive count is based on block dimensions.
- `pipeline.Agent.ThreadBlockCluster`: `size` CTA clusters participate, so the arrive count is based on cluster and block dimensions.

```python
producer_group = pipeline.CooperativeGroup(pipeline.Agent.Thread, 1)
consumer_group = pipeline.CooperativeGroup(pipeline.Agent.Warp, 4)
```

## Pipeline Construction

- Create pipeline objects with `.create(...)`; pass arguments by keyword.
- Define `num_stages` separately and keep it consistent with staged SMEM layouts.
- Allocate or pass barrier storage as a shared-memory pointer when the selected pipeline class requires it.
- Define producer and consumer cooperative groups separately.
- Use meaningful `name=` values when debugging barrier behavior.

```python
num_stages = 4
producer_group = pipeline.CooperativeGroup(pipeline.Agent.Warp, 1)
consumer_group = pipeline.CooperativeGroup(pipeline.Agent.Warp, 1)

pipe = pipeline.PipelineAsync.create(
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
    barrier_storage=barrier_storage,
    name="mainloop",
)
```

## Pipeline State

- Treat pipeline state as the circular-buffer cursor for a staged pipeline buffer.
- `state.index` selects the physical SMEM pipeline stage.
- `state.count` tracks how many logical tiles or stages this state has advanced through.
- `state.phase` is the mbarrier phase bit used to distinguish repeated reuse of the same physical stage.
- `state.stages` is the number of stages in the circular buffer.
- Create separate states for producer and consumer flows when they advance independently.
- Advance state after the corresponding pipeline operation, not before, unless the local example deliberately uses an acquire-and-advance helper.
- Use the stage index from the state to select the SMEM pipeline stage.
- Use `state.count` to select the logical tile when the logical tile index differs from the physical stage index.
- `state.advance()` increments `index` and `count`; when `index` wraps back to zero, it flips `phase`.
- Use `pipeline.PipelineUserType.Producer`, `Consumer`, or `ProducerConsumer` only as the initializer selector for `pipeline.make_pipeline_state(...)`.
- `Producer` initializes the state as `count=0`, `index=0`, `phase=1`.
- `Consumer` initializes the state as `count=0`, `index=0`, `phase=0`.

```python
producer_state = pipeline.make_pipeline_state(pipeline.PipelineUserType.Producer, num_stages)
consumer_state = pipeline.make_pipeline_state(pipeline.PipelineUserType.Consumer, num_stages)

gmem_tile = gmem_tiles[(None, producer_state.count)]
smem_tile = smem_tiles[(None, producer_state.index)]
```

## Pipeline Usage

### Producer Consumer Protocol

- Pipeline classes share the staged-resource idea, but their producer and consumer methods are class-dependent.
- For `PipelineAsync`, the producer flow is acquire, write, commit; the consumer flow is wait, read/compute, release.
- For `PipelineCpAsync`, use the same high-level acquire/commit and wait/release shape, but remember the producer commit path maps to `cp.async` mbarrier arrival semantics.
- For `PipelineTmaAsync`, use the same consumer wait/release shape, but the producer side arms a transaction barrier and TMA completion fills it.
- `PipelineTmaStore` is producer-only; do not call consumer wait/release on it.
- `PipelineOrder` uses `wait()` and `arrive()` for ordered group execution rather than staged producer/consumer data movement.
- Do not consume a stage before the matching consumer wait, and do not overwrite a stage before the matching producer acquire says it is empty.

```python
producer_state = pipeline.make_pipeline_state(
    pipeline.PipelineUserType.Producer,
    num_stages,
)
consumer_state = pipeline.make_pipeline_state(
    pipeline.PipelineUserType.Consumer,
    num_stages,
)

pipe.producer_acquire(producer_state)

producer_stage = producer_state.index
producer_tile = smem_tiles[(None, producer_stage)]
# issue writes or async copies into producer_tile

pipe.producer_commit(producer_state)
producer_state.advance()

pipe.consumer_wait(consumer_state)

consumer_stage = consumer_state.index
consumer_tile = smem_tiles[(None, consumer_stage)]
# consume consumer_tile

pipe.consumer_release(consumer_state)
consumer_state.advance()
```

### Initialization And Synchronization

- Pipeline constructors initialize their mbarrier storage and synchronize participating agents unless `defer_sync=True` is used.
- Use `defer_sync=True` only when the kernel performs an explicit initialization synchronization after constructing the pipeline.
- For single-CTA pipelines, the constructor's default sync path uses CTA-level agent synchronization.
- For cluster or TMA multicast pipelines, follow local examples that split initialization with `pipeline.pipeline_init_arrive(...)` and `pipeline.pipeline_init_wait(...)`.
- Treat initialization synchronization as separate from the per-stage protocol; producer acquire/commit and consumer wait/release are still required.
- Do not replace pipeline waits with `cute.arch.barrier()` or generic fences

```python
pipe = pipeline.PipelineAsync.create(
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
    barrier_storage=barrier_storage,
)
```

```python
pipe = pipeline.PipelineTmaAsync.create(
    num_stages=num_stages,
    producer_group=producer_group,
    consumer_group=consumer_group,
    tx_count=tma_copy_bytes,
    barrier_storage=barrier_storage,
    cta_layout_vmnk=cta_layout_vmnk,
    defer_sync=True,
)

pipeline.pipeline_init_arrive(
    cluster_shape_mn=cluster_shape_mn,
    is_relaxed=True,
)

# Create staged tensors and per-CTA views here if needed.

pipeline.pipeline_init_wait(cluster_shape_mn=cluster_shape_mn)
```

### Agent Sync

- `pipeline.agent_sync(group, is_relaxed=False)` synchronizes all threads in a supported `pipeline.Agent` group.
- Use it after explicit pipeline or mbarrier initialization when participating agents must see initialized synchronization state before the staged protocol starts.
- `pipeline.agent_sync(pipeline.Agent.ThreadBlock)` maps to CTA/thread-block synchronization.
- `pipeline.agent_sync(pipeline.Agent.ThreadBlockCluster)` maps to cluster arrive plus cluster wait.
- `pipeline.agent_sync(pipeline.Agent.ThreadBlockCluster, is_relaxed=True)` uses relaxed cluster arrive plus cluster wait.
- `pipeline.Agent.Thread` is not supported for `agent_sync(...)`.
- `pipeline.Agent.Warp` is not supported by `agent_sync(...)`; use the appropriate barrier or warp-level primitive for that case.
- `agent_sync(...)` is an initialization or explicit rendezvous helper; it does not replace `producer_acquire`, `producer_commit`, `consumer_wait`, or `consumer_release`.

```python
pipeline.agent_sync(pipeline.Agent.ThreadBlock)
```

```python
pipeline.agent_sync(
    pipeline.Agent.ThreadBlockCluster,
    is_relaxed=True,
)
```

### TMA Pipeline Notes

- Use `PipelineTmaAsync` when a TMA load is the producer side of the staged data path.
- The TMA byte count and mbarrier transaction count must match the staged data being produced.
- On the producer side, call `producer_acquire(producer_state)` before issuing TMA; this waits for the stage to be empty and arms the transaction barrier for the stage.
- Pass `tma_bar_ptr=pipe.producer_get_barrier(producer_state)` to the TMA `cute.copy(...)` so the TMA operation completes against the current stage barrier.
- `PipelineTmaAsync.producer_commit(producer_state)` is a no-op because the TMA instruction updates the transaction barrier; keep the call to preserve the producer protocol shape.
- On the consumer side, call `consumer_wait(consumer_state)` before consuming the SMEM stage, then `consumer_release(consumer_state)` after the stage is safe for reuse.
- Pair TMA issue, consumer wait, and consumer release consistently with the SMEM stage selected by the pipeline state.

```python
producer_state = pipeline.make_pipeline_state(
    pipeline.PipelineUserType.Producer,
    num_stages,
)
consumer_state = pipeline.make_pipeline_state(
    pipeline.PipelineUserType.Consumer,
    num_stages,
)

pipe.producer_acquire(producer_state)

gmem_tile = gmem_tiles[(None, producer_state.count)]
smem_tile = smem_tiles[(None, producer_state.index)]

cute.copy(
    tma_atom,
    gmem_tile,
    smem_tile,
    tma_bar_ptr=pipe.producer_get_barrier(producer_state),
)

pipe.producer_commit(producer_state)
producer_state.advance()

pipe.consumer_wait(consumer_state)

consumer_tile = smem_tiles[(None, consumer_state.index)]
# consume consumer_tile after the TMA transaction completes

pipe.consumer_release(consumer_state)
consumer_state.advance()
```
