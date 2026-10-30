---
name: cuda-fence-sync-barrier
description: CUDA fence, sync, barrier, memory ordering, PTX ld/st acquire-release, cp.async, TMA, WGMMA, mbarrier, and TCGEN05 reference. Use when answering or implementing work about CUDA/PTX synchronization semantics on Ampere, Hopper, or Blackwell.
---

# CUDA Fence Sync Barrier

Use this skill for CUDA/PTX synchronization, memory-ordering, fence, barrier,
async-copy, TMA, WGMMA, mbarrier, and TCGEN05 questions or implementation work.

## Scope

- Target architectures: Ampere (`sm_80`), Hopper (`sm_90`/`sm_90a`), and
  Blackwell (`sm_100`/`sm_120`) unless the user asks otherwise.
- Treat official NVIDIA documentation as normative for semantics and support.
- Treat local reference repositories as implementation examples only.
- Ask for or infer CUDA Toolkit version and target SM when exact support matters.

## Reference Rules

- Use NVIDIA documentation as the source of truth for semantics and support.
- Use local code only as implementation examples, not as specification.
- Verify exact instruction spelling, support constraints, and wrapper names before
  making precise claims.
- Follow the project's existing abstraction level. In CuTe-based code, prefer
  its established arch wrappers; in ordinary CUDA C++, prefer documented CUDA
  primitives. Do not introduce CUTLASS solely for a synchronization wrapper.
  Use inline PTX when the required operation is not otherwise exposed.
- Distinguish C++ CuTe/CUTLASS wrapper names from CuTe DSL Python APIs.
  The `cute arch` table column refers to C++ wrappers, while the `cutedsl` column
  refers to Python DSL entry points such as `cute.arch.*`,
  `cute.nvgpu.cpasync.*`, `cute.nvgpu.warpgroup.*`, or higher-level DSL
  constructs when a direct primitive is not intended for user code.

## Concept Split

Keep these categories separate when explaining or designing code:

- **Memory op semantics**: `ld.acquire`, `st.release`, `atom.*.{sem}.{scope}`;
  ordering attached to a memory operation.
- **Fences**: `fence.{sem}.{scope}`, legacy `membar`, proxy fences; ordering
  only, no thread rendezvous.
- **Barriers**: `bar.sync`, `bar.warp.sync`, `barrier.cluster`, named barriers,
  `mbarrier`; rendezvous or phase synchronization, sometimes with memory
  semantics.
- **Async completion/pipeline sync**: `cp.async.commit/wait`, TMA completion via
  `mbarrier`, `wgmma.fence/commit/wait`, TCGEN05/TMEM sync-qualified ops;
  ordering/completion for a specific async engine, not generic memory ordering.

## Memory Operation Semantics

Use this table when the question is about load/store/atomic memory ordering.

| ptx | intrinsic | cute arch | cutedsl | arch | desc |
| --- | --- | --- | --- | --- | --- |
| `ld.relaxed.scope` | `cuda::atomic_ref<T, Scope>.load(memory_order_relaxed)` | usually not wrapped in CuTe arch | no common direct DSL primitive; use DSL atomics if exposed or inline asm | SM80+ | Atomic/ordered load without acquire ordering. Scope matters for atomic ABI forms. |
| `ld.acquire.scope` | `cuda::atomic_ref<T, Scope>.load(memory_order_acquire)` | usually not wrapped in CuTe arch | no common direct DSL primitive; use DSL atomics if exposed or inline asm | SM80+ | Acquire load; subsequent memory operations are ordered after a matching release. |
| `st.relaxed.scope` | `cuda::atomic_ref<T, Scope>.store(memory_order_relaxed)` | usually not wrapped in CuTe arch | no common direct DSL primitive; use DSL atomics if exposed or inline asm | SM80+ | Atomic/ordered store without release ordering. |
| `st.release.scope` | `cuda::atomic_ref<T, Scope>.store(memory_order_release)` | usually not wrapped in CuTe arch | no common direct DSL primitive; use DSL atomics if exposed or inline asm | SM80+ | Release store; prior memory operations become visible to matching acquire. |
| `atom.relaxed.scope.*` | `cuda::atomic_ref` relaxed RMW | project-specific wrappers | project-specific DSL wrappers or inline asm | SM80+ | Atomic read-modify-write without inter-thread ordering beyond atomicity. |
| `atom.acquire.scope.*` | `cuda::atomic_ref` acquire RMW | project-specific wrappers | project-specific DSL wrappers or inline asm | SM80+ | RMW with acquire semantics. |
| `atom.release.scope.*` | `cuda::atomic_ref` release RMW | project-specific wrappers | project-specific DSL wrappers or inline asm | SM80+ | RMW with release semantics. |
| `atom.acq_rel.scope.*` | `cuda::atomic_ref` acq_rel RMW | project-specific wrappers | project-specific DSL wrappers or inline asm | SM80+ | RMW with both acquire and release semantics. |

Rules:

- Loads support relaxed/acquire-style semantics; loads do not carry release.
- Stores support relaxed/release-style semantics; stores do not carry acquire.
- Acquire/release synchronization requires a valid communication pattern and a
  scope that includes the participating threads.
- Sequential consistency is generally expressed with `fence.sc.scope` around
  operations rather than `ld.sc` or `st.sc`.
- Prefer CUDA C++ atomics for portable code; use inline PTX only when exact
  instruction selection is required.

## Fences

Use this table when the question is about ordering without rendezvous.

| ptx | intrinsic | cute arch | cutedsl | arch | desc |
| --- | --- | --- | --- | --- | --- |
| `fence.sc.cta` / legacy `membar.cta` | `__threadfence_block()` | none; use CUDA intrinsic | `cute.arch.fence_acq_rel_cta()` for acq_rel-style fences; verify exact semantic needs | SM80+ | CTA-scope memory fence; orders this thread's memory ops for block scope; not a barrier. |
| `fence.sc.gpu` / legacy `membar.gl` | `__threadfence()` | none; use CUDA intrinsic | `cute.arch.fence_acq_rel_gpu()` for acq_rel-style fences; verify exact semantic needs | SM80+ | Device-scope memory fence; heavier than CTA scope. |
| `fence.sc.sys` / legacy `membar.sys` | `__threadfence_system()` | none; use CUDA intrinsic | `cute.arch.fence_acq_rel_sys()` for acq_rel-style fences; verify exact semantic needs | SM80+ | System-scope fence; visible to host/peers where supported; heaviest common CUDA fence. |
| `fence.acquire.scope` | `cuda::atomic_thread_fence(memory_order_acquire, scope)` | usually not wrapped in CuTe arch | no common direct acquire-only DSL primitive; use available `cute.arch.fence_acq_rel_*` only if acq_rel is acceptable | SM80+ | Acquire fence; orders later memory operations after matching release. |
| `fence.release.scope` | `cuda::atomic_thread_fence(memory_order_release, scope)` | usually not wrapped in CuTe arch | no common direct release-only DSL primitive; use available `cute.arch.fence_acq_rel_*` only if acq_rel is acceptable | SM80+ | Release fence; orders earlier memory operations before matching acquire. |
| `fence.acq_rel.scope` | `cuda::atomic_thread_fence(memory_order_acq_rel, scope)` | usually not wrapped in CuTe arch | `cute.arch.fence_acq_rel_{cta,cluster,gpu,sys}()` | SM80+ | Both acquire and release fence semantics. |
| `fence.sc.scope` | `cuda::atomic_thread_fence(memory_order_seq_cst, scope)` | usually not wrapped in CuTe arch | no common direct seq_cst DSL primitive; use inline asm if exact SC is required | SM80+ | Sequentially consistent fence at the selected scope. |
| `fence.proxy.async.shared::cta` | inline PTX / CuTe | `cute::tma_store_fence()` | `cute.arch.fence_proxy()` / `cute.arch.fence_view_async_shared()` depending on async view | SM90+ | Orders normal shared-memory stores before TMA store async-proxy reads shared memory. |
| `fence.proxy.tensormap::generic.release.gpu` | inline PTX / CuTe | `cute::tma_descriptor_fence_release()` | `cute.nvgpu.cpasync.fence_tma_desc_release()` / `cute.nvgpu.cpasync.cp_fence_tma_desc_release()` | SM90+ | Release fence for device-side TMA descriptor/tensormap modification. |
| `fence.proxy.tensormap::generic.acquire.gpu` | inline PTX / CuTe | `cute::tma_descriptor_fence_acquire()` | `cute.nvgpu.cpasync.fence_tma_desc_acquire()` | SM90+ | Acquire fence before consuming a modified TMA descriptor/tensormap. |

Notes:

- A fence orders memory operations; it does not make other threads wait.
- Use the narrowest scope that includes the communicating threads: CTA,
  cluster, GPU, or system.
- Proxy fences are for ordering across special memory/access proxy paths, such
  as TMA/tensormap/async shared views; they are not replacements for ordinary
  acquire-release synchronization.

## Barriers

Use this table when the question is about rendezvous, phase synchronization, or
producer-consumer barriers.

| ptx | intrinsic | cute arch | cutedsl | arch | desc |
| --- | --- | --- | --- | --- | --- |
| `bar.sync` / `barrier.sync.aligned` | `__syncthreads()` | direct CUDA use | `cute.arch.sync_threads()` | SM80+ | Full CTA barrier; all block threads wait; includes block-level memory ordering. |
| `bar.warp.sync` | `__syncwarp(mask)` | direct CUDA use | `cute.arch.sync_warp()` | SM80+ | Warp-level barrier for active lanes in mask. |
| `bar.sync id,count` / named barrier | CUTLASS wrapper | `cutlass::arch::NamedBarrier` | `cutlass.pipeline.NamedBarrier` with `arrive_and_wait()` | SM80+ | Partial CTA/named barrier; common in warp-specialized kernels. |
| `bar.arrive` / `barrier.arrive` | inline PTX or CUTLASS wrapper | `cutlass::arch::NamedBarrier::arrive` | `cute.arch.barrier_arrive()` or `pipeline.NamedBarrier.arrive()` if exposed | SM80+ | CTA named-barrier arrive without waiting for completion. |
| `barrier.cluster.arrive.aligned` | `cooperative_groups::this_cluster().sync()` for full sync | `cute::cluster_arrive()` | `cute.arch.cluster_arrive()` | SM90+ | Arrive at cluster barrier; pairs with cluster wait. |
| `barrier.cluster.wait.aligned` | `cooperative_groups::this_cluster().sync()` for full sync | `cute::cluster_wait()` | `cute.arch.cluster_wait()` | SM90+ | Wait for CTAs in cluster to arrive. |
| `barrier.cluster.arrive.relaxed.aligned` | inline PTX / CuTe | `cute::cluster_arrive_relaxed()` | `cute.arch.cluster_arrive_relaxed()` | SM90+ | Cluster arrive without memory-ordering semantics. |
| `mbarrier.init.shared::cta.b64` | NVVM mbarrier intrinsics / inline PTX | `cute::initialize_barrier()` | `cute.arch.mbarrier_init()` plus `cute.arch.mbarrier_init_fence()` | SM90+ | Initialize a shared-memory mbarrier object. |
| `mbarrier.arrive.shared::cta.b64` | NVVM mbarrier intrinsics / inline PTX | `cute::arrive_barrier()` | `cute.arch.mbarrier_arrive()` | SM90+ | Release-style arrival on an mbarrier phase. |
| `mbarrier.try_wait.parity.shared::cta.b64` | NVVM mbarrier intrinsics / inline PTX | `cute::wait_barrier()` | `cute.arch.mbarrier_wait()` / `cute.arch.mbarrier_try_wait()` | SM90+ | Acquire-style wait/test for mbarrier phase completion. |
| `mbarrier.arrive.expect_tx.shared::cta.b64` | inline PTX / CuTe | `cute::set_barrier_transaction_bytes()` | `cute.arch.mbarrier_arrive_and_expect_tx()` / `cute.arch.mbarrier_expect_tx()` | SM90+ | Sets expected async transaction bytes and arrives; common for TMA loads. |

Notes:

- Prefer `cute.arch.sync_threads()` for full CTA synchronization. In CUTLASS
  commit `1e7394829291360bdcf07036cbe5411631d2d33b`, both `sync_threads()` and
  parameterless `barrier()` emit `nvvm.barrier`; `barrier()` additionally accepts
  a barrier ID and participant count. This was checked in
  `python/CuTeDSL/cutlass/cute/arch/nvvm_wrappers.py`; verify the installed version
  before choosing named-barrier arguments.
- CTA barriers and named barriers are not global/device barriers.
- Cluster barriers require cluster-capable launches and `sm_90+` support.
- `mbarrier` is a memory barrier object with phases; it is not the same as
  `__syncthreads()` and must be initialized/reused carefully.

## Async Completion And Pipeline Sync

Use this table when the question is about waiting for async engines rather than
generic memory ordering.

| ptx | intrinsic | cute arch | cutedsl | arch | desc |
| --- | --- | --- | --- | --- | --- |
| `cp.async.commit_group` | CUDA pipeline APIs / inline PTX | `cute::cp_async_fence()` | `cute.arch.cp_async_commit_group()` | SM80+ | Commits prior `cp.async` operations into a group; despite CuTe name, not a generic memory fence. |
| `cp.async.wait_group N` | CUDA pipeline APIs / inline PTX | `cute::cp_async_wait<N>()` | `cute.arch.cp_async_wait_group(N)` | SM80+ | Waits until all but `N` committed `cp.async` groups complete. |
| `cp.async.wait_all` | CUDA pipeline APIs / inline PTX | `cute::cp_async_wait<0>()` | `cute.arch.cp_async_commit_group()` followed by `cute.arch.cp_async_wait_group(0)` | SM80+ | Commits outstanding copies and waits for all prior `cp.async` operations. A wait on group 0 alone covers only committed groups. |
| `cp.async.bulk.tensor...mbarrier::complete_tx` | inline PTX / CuTe TMA copy wrappers | CuTe `SM90_TMA_*` / `SM100_TMA_*` copy structs | TMA copy atoms / `cute.nvgpu.cpasync.*` helpers and `cute.copy` / DSL TMA load/store constructs | SM90+ | Issues TMA bulk/tensor async copy and reports completion through mbarrier transaction bytes. |
| `cp.async.bulk.commit_group` | inline PTX / CuTe | `cute::tma_store_arrive()` / `cute::tma_desc_commit_group()` | `cute.arch.cp_async_bulk_commit_group()` | SM90+ | Commits TMA store/bulk async group; completion requires a separate matching wait. |
| `wgmma.fence.sync.aligned` | inline PTX / CuTe | `cute::warpgroup_arrive()` | `cute.nvgpu.warpgroup.fence()` or WGMMA DSL atom protocol | SM90a | WGMMA operand/order fence before async warpgroup MMA. |
| `wgmma.commit_group.sync.aligned` | inline PTX / CuTe | `cute::warpgroup_commit_batch()` | WGMMA DSL atom/protocol; verify exposed helper for current CuTe DSL version | SM90a | Commits issued WGMMA operations as a completion group. |
| `wgmma.wait_group.sync.aligned N` | inline PTX / CuTe | `cute::warpgroup_wait<N>()` | WGMMA DSL atom/protocol; verify exposed helper for current CuTe DSL version | SM90a | Waits for async WGMMA groups before reading accumulators. |
| `tcgen05.mma...` | inline PTX / CuTe | CuTe `SM100_MMA_*` wrappers | `cutlass.cute.nvgpu.tcgen05` atoms/helpers and generated DSL MMA code | SM100+ | Blackwell tensor-core generation 5 MMA; sync/ordering is operation-specific, not a generic fence. |
| `tcgen05.alloc/dealloc...sync.aligned` | inline PTX / CuTe | `cute::TMEM::Allocator1Sm/2Sm` | `cute.arch.alloc_tmem()`, `cute.arch.retrieve_tmem_ptr()`, `cute.arch.dealloc_tmem()`, or `cutlass.utils.tmem_allocator` | SM100+ | Tensor-memory allocation/deallocation synchronization; not a generic memory fence. |
| `tcgen05.cp/ld/st...sync.aligned` | inline PTX / CuTe | CuTe `copy_sm100.hpp` wrappers | `cute.nvgpu.tcgen05.make_tmem_copy()` / DSL copy atoms | SM100+ | Blackwell TMEM copy/load/store sync-qualified operations; operation-specific. |

Notes:

- At the CUTLASS commit cited above, C++ `cp_async_wait<0>()` emits
  `cp.async.wait_all` in `include/cute/arch/copy_sm80.hpp`, while the DSL
  `cp_async_wait_group(0)` emits only a group wait in `nvvm_wrappers.py`.
  Do not assume these wrappers have identical handling of uncommitted copies.
- Async completion primitives are usually paired with a data-visibility protocol:
  e.g. `cp.async.wait` plus `__syncthreads()` for CTA consumers, or TMA plus
  `mbarrier` wait for transaction completion.
- WGMMA has its own async proxy and completion group protocol; do not replace
  it with generic `__threadfence*`.
- Blackwell TCGEN05/TMEM operations require exact target support checks; verify
  current PTX ISA and CuTe wrapper support before making strong claims.

## Decision Guide

- Need only one thread's memory operations ordered? Use a fence or acquire/release
  memory operation.
- Need participating threads to wait together? Use a barrier.
- Need producer/consumer phase handoff? Use acquire/release, named barrier, or
  `mbarrier` depending on scope and async engine.
- Need `cp.async`, TMA, WGMMA, or TCGEN05 completion? Use that engine's specific
  commit/wait/fence protocol.
- Need portability in CUDA C++? Prefer `cuda::atomic`, `cuda::atomic_ref`,
  `cuda::barrier`, `cuda::pipeline`, cooperative groups, and documented CUDA
  intrinsics over inline PTX.

## Working Rules

- State the CUDA Toolkit version and target SM when support details matter.
- Separate specified semantics from common implementation patterns and from
  performance heuristics.
- Do not assume a CuTe or CUTLASS wrapper is normative; cross-check official PTX
  or CUDA docs for instruction semantics.
- Do not assume CuTe DSL and C++ CuTe use the same API spelling; inspect the
  installed CuTe DSL version before citing a `cute.arch.*` or
  `cute.nvgpu.*` wrapper.
- Inspect local reference files before citing wrapper names or code patterns.
- For inline PTX examples, verify exact instruction spelling, constraints, and
  `asm volatile` memory clobbers.
- For performance-sensitive code, prefer the narrowest correct scope and the
  least intrusive primitive, then benchmark.
