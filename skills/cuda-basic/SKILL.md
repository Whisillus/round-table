---
name: cuda-basic
description: Use whenever writing, reviewing, or debugging CUDA code; covers CUDA reference discipline, target SM/toolkit handling, kernels, memory hierarchy, streams, errors, synchronization routing, build/runtime routing, and debugging workflow.
---

# CUDA Basic

## Related Skills

- Treat this as the entry-point skill for CUDA programming tasks; load it before
  applying more specialized CUDA skills.
- Also use `cuda-general-reference` when the task needs NVIDIA documentation,
  local reference locations, architecture guides, PTX references, or CUDA API
  reference lookup.
- Also use `cuda-build-toolchain` when the task involves NVCC, NVRTC,
  nvJitLink, nvFatbin, fatbins, PTX/CUBIN generation, `-arch`, `-gencode`,
  ptxas diagnostics, line info, or binary inspection.
- Also use `cuda-runtime-driver` when the task involves CUDA Runtime or Driver
  APIs, streams, events, memory allocation, memory copies, graphs, modules,
  launches, contexts, or CUDA error handling.
- Also use `cuda-fence-sync-barrier` when the task involves memory ordering,
  fences, barriers, acquire/release, `cp.async`, TMA synchronization, WGMMA
  completion, mbarriers, cluster barriers, or TCGEN05/TMEM sync semantics.

## Reference Discipline

- Treat official NVIDIA documentation as normative for CUDA, PTX, compiler,
  runtime, driver, ABI, and architecture behavior.
- Treat local repositories and examples as implementation evidence, not as
  specification.
- Ask for or infer CUDA Toolkit version, driver constraints, and target GPU/SM
  before making architecture-specific or compiler-specific claims.
- Do not invent performance numbers, instruction support, occupancy, bandwidth,
  or latency claims. Verify them in docs, source, benchmarks, release notes, or
  measured output.

## Target And Version Handling

- Name target architectures explicitly, such as `sm_80`, `sm_90`, `sm_90a`,
  `sm_100`, or `sm_120`.
- Distinguish virtual architectures such as `compute_90` from real GPU targets
  such as `sm_90`.
- Architecture-specific suffixes such as `a` targets can enable instructions or
  features that are not portable to the generic architecture target; verify
  compatibility before using them.
- Match code paths, build flags, and runtime checks to the intended deployment
  GPUs.

## Kernel Basics

- Keep host code and device code responsibilities separate.
- Validate grid dimensions, block dimensions, dynamic shared-memory bytes,
  kernel argument layout, and launch stream before debugging lower-level issues.
- Use `threadIdx`, `blockIdx`, `blockDim`, and `gridDim` consistently; avoid
  hard-coded warp or block assumptions unless the kernel contract requires them.
- Use `__device__`, `__global__`, `__host__`, and `__forceinline__` deliberately;
  do not add qualifiers mechanically.
- Guard architecture-specific device code with compile-time target checks when a
  translation unit may be built for multiple SMs.

```c++
__global__ void kernel(float* out, float const* in, int n) {
  int tid = blockIdx.x * blockDim.x + threadIdx.x;
  if (tid < n) {
    out[tid] = in[tid] * 2.0f;
  }
}
```

## Memory And Data Movement

- Identify the memory space first: registers, local memory, shared memory, global
  memory, constant memory, texture/surface memory, managed memory, host memory,
  or peer memory.
- Prefer coalesced global-memory access and avoid unnecessary host-device copies.
- Treat shared memory as explicitly managed storage with explicit synchronization
  requirements.
- Check alignment and vectorization assumptions before changing access width.
- For asynchronous copies, use the matching completion and visibility protocol;
  do not rely on ordinary loads seeing async-copy results without the required
  waits and synchronization.

## Streams, Errors, And Runtime Behavior

- CUDA kernel launches are asynchronous with respect to the host.
- Check launch errors with `cudaGetLastError()` or the project's existing wrapper.
- Use stream or device synchronization only when the workflow needs completion or
  asynchronous error observation.
- Operations in one stream are ordered; cross-stream dependencies need events,
  explicit waits, or another documented dependency mechanism.
- In libraries, prefer explicit stream handling over silently relying on default
  stream behavior.

```c++
kernel<<<grid, block, smem_bytes, stream>>>(out, in, n);
auto launch_status = cudaGetLastError();
// Only when this workflow needs completion or asynchronous error observation:
auto exec_status = cudaStreamSynchronize(stream);
```

## Synchronization Routing

- Use `__syncthreads()` for full CTA rendezvous and block-level shared-memory
  visibility when all block threads participate.
- Use `__syncwarp(mask)` for warp-level rendezvous when the active-lane mask is
  correct.
- Use CUDA atomics or fences when ordering is needed without a rendezvous.
- Use the async engine's own completion protocol for `cp.async`, TMA, WGMMA, and
  TCGEN05/TMEM operations.
- For detailed memory-ordering and barrier choices, load `cuda-fence-sync-barrier`.

## Debug Workflow

- Reproduce the failure with the smallest relevant input and target SM.
- Identify whether the issue is host API usage, launch configuration, memory
  lifetime, synchronization, compiler flags, code generation, or device logic.
- Use CUDA error checks and synchronization points to locate asynchronous errors.
- Use `compute-sanitizer` for memory, race, initialization, and synchronization
  debugging when kernels fault or produce invalid results.
- Use line info and ptxas diagnostics through the build system when correlating
  source, generated code, and profiler output.

## Working Rules

- Inspect the local code and build configuration before modifying CUDA code or
  flags.
- Preserve existing project wrappers for error handling, stream management,
  allocation, and launch helpers unless they are the source of the bug.
- These skills provide methods, not permission to modify files or execute code.
  Follow the active agent's role and the user's authorized scope; a static
  reviewer reports required runtime checks instead of running them.
- Validate at input and launch boundaries; trust established internal contracts
  rather than adding repeated checks for states those contracts exclude.
- Keep correctness, portability, and performance claims separate.
- For performance-sensitive code, prefer a clear correctness fix first, then
  benchmark any optimization claim on the intended hardware.
