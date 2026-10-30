---
name: cuda-runtime-driver
description: CUDA Runtime and Driver API reference for streams, events, memory allocation/copy, modules, contexts, launches, graphs, and error handling. Use when implementing or debugging cuda* or cu* API code and CUDA host-side execution flows.
---

# CUDA Runtime Driver

Use this skill for host-side CUDA API work. Keep compiler flags and runtime
compilation details in `cuda-build-toolchain`, and memory-ordering or barrier
semantics in `cuda-fence-sync-barrier`.

## Reference Priority

- CUDA Runtime API: <https://docs.nvidia.com/cuda/cuda-runtime-api/index.html>
- CUDA Driver API: <https://docs.nvidia.com/cuda/cuda-driver-api/index.html>
- CUDA Programming Guide: <https://docs.nvidia.com/cuda/cuda-programming-guide/index.html>
- Local snapshots: `~/workspace/reference/docs/cuda-13-3/CUDA_Runtime_API.pdf`
  and `~/workspace/reference/docs/cuda-13-3/CUDA_Driver_API.pdf` when present.
  These are CUDA 13.3 snapshots, not necessarily the target project's version.
  Follow `cuda-general-reference` for other local locations; prefer matching
  versioned local docs and cite their version. Use official online docs when
  local material is absent or the task requires current behavior.

Use local reference repositories for examples only. Inspect the local code before
copying API patterns because framework integrations often wrap CUDA errors,
streams, memory pools, and contexts.

## API Boundary

- Runtime API functions usually use `cuda*` names and manage much of the context
  and module machinery implicitly.
- Driver API functions use `cu*` names and expose explicit devices, contexts,
  modules, functions, streams, events, and launch configuration.
- Mixing Runtime and Driver APIs can be valid, but context ownership and primary
  context behavior must be understood before changing code.
- Do not translate Runtime API code to Driver API code only for style. Do it when
  the task needs explicit module loading, JIT options, context control, or APIs
  not available through the Runtime path.

## Error Handling

- Check every CUDA API return status unless the surrounding project has a proven
  wrapper macro or exception layer.
- Runtime API calls return `cudaError_t`; Driver API calls return `CUresult`.
- Kernel launches are asynchronous. Check launch configuration errors separately
  from later execution errors.
- Use a stream or device synchronization point only when the workflow needs to
  observe asynchronous errors or completion.
- For Driver API errors, retrieve names and messages with `cuGetErrorName(...)`
  and `cuGetErrorString(...)` when reporting failures.

```c++
kernel<<<grid, block, smem_bytes, stream>>>(args...);
auto launch_status = cudaGetLastError();
// Only when this workflow needs completion or asynchronous error observation:
auto exec_status = cudaStreamSynchronize(stream);
```

## Streams And Events

- CUDA operations in the same stream are ordered; operations in different streams
  may overlap unless dependencies are added.
- Default-stream behavior can be legacy or per-thread depending on compilation
  and runtime configuration. Verify before relying on default-stream ordering.
- Use events for stream-to-stream dependencies, timing, and host-side completion
  checks.
- Event timing measures GPU stream time for recorded work; it is not a substitute
  for end-to-end host timing.
- Prefer explicit streams in libraries and framework integrations instead of
  silently using the default stream.

```c++
cudaEventRecord(done, producer_stream);
cudaStreamWaitEvent(consumer_stream, done, 0);
```

## Memory Allocation And Copies

- Identify the memory type first: device, pinned host, pageable host, managed,
  array, pitched allocation, peer memory, or framework-owned memory.
- `cudaMallocAsync` and `cudaFreeAsync` are stream-ordered and tied to memory-pool
  behavior; do not replace `cudaMalloc` blindly without checking lifetime and
  stream semantics.
- Host-device copy overlap generally requires pinned host memory and compatible
  stream usage.
- `cudaMemcpyAsync` is ordered in its stream. Cross-stream visibility still needs
  events or another dependency.
- For managed memory, verify prefetching, advice, access patterns, and device
  support before attributing behavior to normal device-memory semantics.
- For peer access and multi-GPU code, verify device topology, peer-access enable
  calls, and selected context/device for each allocation and copy.

## Kernel Launches

- Confirm grid, block, dynamic shared memory, stream, and kernel argument layout.
- Runtime launches use triple-chevron syntax or Runtime API launch helpers;
  Driver launches use `cuLaunchKernel(...)` with a `CUfunction` and explicit
  parameter arrays or extra config.
- Dynamic shared-memory size must match the kernel's shared storage assumptions.
- Target architecture and module contents must support the launched kernel.

```c++
void* params[] = {&arg0, &arg1};
cuLaunchKernel(func, gx, gy, gz, bx, by, bz, smem_bytes, stream, params, nullptr);
```

## Modules And Contexts

- Driver API module loading paths include `cuModuleLoad`, `cuModuleLoadData`, and
  `cuModuleLoadDataEx` depending on whether the input is a file or memory buffer
  and whether JIT options/logs are needed.
- Use `cuModuleGetFunction(...)` to retrieve kernels from loaded modules.
- Establish context and device selection before loading modules or allocating
  memory in Driver API code.
- In Runtime API projects, understand the current device and primary context
  before introducing Driver API module loading.

## CUDA Graphs

- Use graphs when repeated launch structure dominates overhead or the project
  already uses graph capture.
- During stream capture, only capture-safe CUDA operations are allowed; verify
  API restrictions before moving allocations, events, or library calls into a
  captured region.
- Distinguish graph construction, instantiation, update, launch, and destruction
  lifetimes.
- Graph updates are constrained by the instantiated graph structure; if an update
  fails, inspect which node or parameter change is unsupported.

## Debugging Checklist

- Record CUDA Toolkit version, driver version when relevant, device name, compute
  capability, selected device, and active context model.
- Identify the first failing API call and whether the error is synchronous or
  reported later by a synchronization point.
- Check stream ordering before assuming a memory or kernel race.
- Check allocation lifetime and ownership before adding synchronization.
- For framework code, use the framework's current stream and allocator APIs when
  local conventions require them.
