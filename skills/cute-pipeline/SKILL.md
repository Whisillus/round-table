---
name: cute-pipeline
description: Use when the user asks about C++ CuTe/CUTLASS pipelines, cutlass::PipelineAsync, PipelineTmaAsync, PipelineTmaStore, PipelineTransactionAsync, PipelineState, producer/consumer stages, mbarrier-backed pipelines, or SM90 pipeline usage.
---

# CuTe C++ Pipeline

Use this skill for C++ CUTLASS pipeline APIs used by CuTe kernels. The C++ classes live in the `cutlass::` namespace and headers under `cutlass/pipeline/`.

## Pipeline Class

Primary C++ classes:

- `cutlass::PipelineAsync<Stages>`: generic staged producer/consumer pipeline for ordinary async-thread producer/consumer code.
- `cutlass::PipelineTmaAsync<Stages>`: staged pipeline for TMA load producers and async consumers; transaction bytes and transaction barriers are central to correctness.
- `cutlass::PipelineTmaStore<Stages>`: producer-side synchronization wrapper for TMA store paths.
- `cutlass::PipelineTransactionAsync<Stages>`: staged transaction-counted pipeline for asynchronous producer transactions.
- `cutlass::OrderedSequenceBarrier<SequenceDepth, SequenceLength>`: ordered group sequencing helper, not a normal staged resource pipeline.

```c++
#include "cutlass/pipeline/sm90_pipeline.hpp"

static constexpr int Stages = 4;
using MainloopPipeline = cutlass::PipelineAsync<Stages>;
using PipelineState = cutlass::PipelineState<Stages>;
```

## Pipeline State

- `cutlass::PipelineState<Stages>` is the circular-buffer cursor for a staged resource.
- `state.index()` selects the physical stage.
- `state.phase()` selects the mbarrier phase for repeated stage reuse.
- `state.count()` tracks how many logical stages/tiles the state has advanced.
- Advance with `++state` or `state.advance(n)` after the matching pipeline operation.
- Use `cutlass::make_producer_start_state<Pipeline>()` when the producer state should begin in a phase where initial acquire succeeds.
- Maintain separate producer and consumer states when producer and consumer progress independently.

```c++
PipelineState write_state = cutlass::make_producer_start_state<MainloopPipeline>();
PipelineState read_state;

auto stage = write_state.index();
++write_state;
```

## Pipeline Construction

- Allocate pipeline shared storage in the kernel's shared storage struct when the selected pipeline class requires it.
- Fill the pipeline `Params` object explicitly; arrive counts must match the actual participating producer and consumer threads.
- For `PipelineAsync` and `PipelineTransactionAsync`, set `params.role` for each participant path before calling producer or consumer APIs.
- For `PipelineTmaAsync`, set `params.role`, `params.is_leader`, `params.num_consumers`, `params.num_producers`, and `params.transaction_bytes`; the leader arms the transaction barrier during producer acquire.
- Construct pipeline objects after shared storage is available and before producer/consumer protocol use.
- For cluster or TMA pipelines, follow local examples for cluster shape, barrier initialization, and synchronization.
- A mismatch between `producer_arv_count`, `consumer_arv_count`, elected producer threads, and guarded code paths can hang the kernel.

```c++
typename MainloopPipeline::Params params;
params.role = MainloopPipeline::ThreadCategory::ProducerConsumer;
params.producer_arv_count = 1;
params.consumer_arv_count = 128;

MainloopPipeline pipeline(shared_storage.pipeline_storage, params);
```

## Producer Consumer Protocol

- For `PipelineAsync`, producer flow is acquire, write, commit, advance; consumer flow is wait, read/compute, release, advance.
- For `PipelineTmaAsync`, producer code must arrange expected transaction bytes and stage completion against the producer barrier; consumer wait/release remains the gate before reading and after consuming.
- For `PipelineTmaStore`, do not invent a consumer wait/release path; it is producer-side store synchronization.
- Do not overwrite a stage before producer acquire succeeds.
- Do not consume a stage before consumer wait succeeds.
- Do not replace pipeline wait/release operations with only `__syncthreads()` or generic fences.

```c++
pipeline.producer_acquire(write_state);

auto write_stage = write_state.index();
// issue producer work for write_stage

pipeline.producer_commit(write_state);
++write_state;

pipeline.consumer_wait(read_state);

auto read_stage = read_state.index();
// consume read_stage

pipeline.consumer_release(read_state);
++read_state;
```

## TMA Pipeline Notes

- Set `PipelineTmaAsync::Params::transaction_bytes` to the total bytes expected to arrive at each stage's transaction barrier.
- `PipelineTmaAsync::producer_acquire(...)` arms the stage transaction barrier with `params.transaction_bytes`; do not add a separate `producer_expect_transaction(...)` call in normal `PipelineTmaAsync` code.
- In current C++ CUTLASS, `PipelineTmaAsync::producer_commit(state, bytes)` exists for unit-test simulation of TMA completion; normal TMA mainloops should pass the pipeline barrier pointer to the TMA operation and treat producer commit as a protocol placeholder when local code uses it.
- Use one elected producer thread or the exact producer group expected by the TMA path; all participants must still follow the pipeline protocol expected by the kernel.
- Keep TMA barrier initialization, cluster synchronization, producer completion, consumer wait, WGMMA use, and release ordering consistent with local SM90 examples.
- Keep this section limited to barrier, state, and producer/consumer protocol around staged resources.

In this example, `shared_storage.pipeline_storage` must have type
`cutlass::PipelineTmaAsync<Stages>::SharedStorage` and reside in shared memory.

```c++
using TmaPipeline = cutlass::PipelineTmaAsync<Stages>;
typename TmaPipeline::Params params;
params.role = TmaPipeline::ThreadCategory::Producer;
params.is_leader = elected_tma_producer;
params.num_consumers = NumConsumerThreads;
params.num_producers = NumProducerThreads;
params.transaction_bytes = transaction_bytes;

TmaPipeline pipeline(shared_storage.pipeline_storage, params, cluster_shape);
auto write_state = cutlass::make_producer_start_state<TmaPipeline>();

pipeline.producer_acquire(write_state);
// issue TMA with pipeline.producer_get_barrier(write_state)
pipeline.producer_commit(write_state, transaction_bytes);
++write_state;
```

## Tail And Cleanup

- Use class-provided tail methods such as `producer_tail(...)` when the local pipeline example or class contract requires draining producer state.
- Ensure outstanding asynchronous producer or WGMMA work is waited on before reusing shared storage or writing final outputs.
- Treat pipeline state advancement and barrier phase changes as part of correctness, not just performance.

## Debugging Pipeline Hangs

- First verify participant counts, elected producer conditions, and whether every guarded producer/consumer path reaches the corresponding acquire/commit/wait/release.
- Check transaction bytes for TMA paths.
- Check that initialization barriers are visible to all participating CTAs or clusters before use.
- Check that producer and consumer states advance exactly once per logical stage.
- Prefer comparing against local examples under `examples/cute/tutorial/hopper` or the relevant `cutlass/pipeline/*_pipeline.hpp` class before changing protocol shape.
