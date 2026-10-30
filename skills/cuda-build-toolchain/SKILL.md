---
name: cuda-build-toolchain
description: CUDA build/toolchain reference for NVCC, NVRTC, nvJitLink, nvFatbin, fatbins, PTX/CUBIN generation, -arch/-gencode, ptxas diagnostics, line info, and binary inspection. Use when configuring or debugging CUDA compilation, runtime compilation, linking, or generated artifacts.
---

# CUDA Build Toolchain

Use this skill for CUDA compilation and artifact-generation tasks. Keep runtime
API behavior in `cuda-runtime-driver`, synchronization semantics in
`cuda-fence-sync-barrier`, and PTX instruction semantics in the official PTX ISA
until a dedicated PTX skill exists.

## Reference Priority

- Use official NVIDIA documentation for compiler option semantics, supported
  targets, compatibility rules, and tool behavior.
- Use project build files and local reference repositories for implementation
  patterns, not as specification.
- Follow `cuda-general-reference` for local reference discovery. When
  `~/workspace/reference/docs/cuda-13-3/` exists, it contains CUDA 13.3 snapshots;
  inspect the directory before citing a document. Prefer the version matching
  the task, and state the version used. Use official online docs when local
  material is absent or current behavior is required.

Primary references:

- NVCC: <https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html>
- NVRTC: <https://docs.nvidia.com/cuda/nvrtc/index.html>
- nvJitLink: <https://docs.nvidia.com/cuda/nvjitlink/index.html>
- nvFatbin: <https://docs.nvidia.com/cuda/nvfatbin/index.html>
- CUDA Binary Utilities: <https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html>
- CUDA Compatibility: <https://docs.nvidia.com/deploy/cuda-compatibility/index.html>

## Inputs To Establish

- CUDA Toolkit version and driver/runtime compatibility requirements.
- Host compiler and platform constraints.
- Target GPUs and SMs, such as `sm_80`, `sm_90`, `sm_90a`, `sm_100`, or
  `sm_100a`.
- Whether the project needs SASS/CUBIN, PTX for forward compatibility, fatbins,
  runtime compilation, device linking, or generated-code inspection.
- Existing build system: CMake, Make, setuptools, PyTorch extension, Bazel,
  custom scripts, or JIT launcher.

## NVCC Target Model

- Distinguish virtual architectures such as `compute_90` from real GPU targets
  such as `sm_90`.
- Use `-gencode arch=compute_XY,code=sm_XY` when emitting SASS for a specific
  target.
- Include `code=compute_XY` when the artifact should carry PTX for JIT fallback
  or forward compatibility, subject to the project's deployment policy.
- Architecture-specific targets such as `sm_90a` or `sm_100a` expose features
  that are not interchangeable with generic targets; verify compatibility docs
  before relying on them.
- Match target flags to the instructions used by the code. WGMMA, TMA, cluster,
  TCGEN05, and TMEM paths often require architecture-specific target support.

```bash
nvcc -gencode arch=compute_90,code=sm_90 ...
nvcc -gencode arch=compute_90,code='[sm_90,compute_90]' ...
```

## Common NVCC Workflows

- For project builds, inspect the existing build configuration before changing
  flags. Preserve project conventions unless they are the bug.
- Use `--generate-line-info` for profiler/source correlation with less debug
  overhead than full device debug.
- Use device debug options only when debugging correctness; they can change code
  generation and performance.
- Use ptxas verbose diagnostics when investigating registers, spills, stack
  usage, or shared-memory usage.
- For separable compilation and device linking, verify the project's use of
  relocatable device code and device-link steps before adding flags.
- For generated artifacts, record the complete command, CUDA version, target SM,
  and ptxas output needed to reproduce the result.

```bash
nvcc --generate-line-info -Xptxas=-v ...
nvcc -dc ...
nvcc -dlink ...
```

## NVRTC Runtime Compilation

- Use NVRTC when the program compiles CUDA source strings at runtime.
- Capture and surface compile logs on both success and failure when debugging.
- Pass target options explicitly; do not assume the host device target is selected
  automatically in a reusable library.
- For C++ kernels, use lowered-name APIs or project helpers when retrieving
  mangled kernel names.
- Decide whether the caller needs PTX, CUBIN, LTO IR, or another artifact based
  on the NVRTC version and target option support.

```text
NVRTC flow: create program -> compile with options -> read log -> retrieve PTX,
CUBIN, or other supported artifact -> load or link with the selected runtime path.
```

## Runtime Linking And Fatbins

- Use nvJitLink when runtime-generated or separately produced device code must be
  linked before loading.
- Use nvFatbin when creating or packaging CUDA fatbinary artifacts directly.
- Keep link options, target architecture, libdevice requirements, and logs with
  the artifact for reproducibility.
- Verify whether the deployment path expects Driver API module loading, Runtime
  API registration, framework extension loading, or a project-specific loader.

## Binary Inspection

- Use CUDA Binary Utilities documentation for `cuobjdump`, `nvdisasm`, fatbin
  inspection, and generated-code artifact analysis.
- Treat SASS inspection as target-specific evidence. Do not infer source-level
  semantics from SASS alone when the CUDA or PTX specification is the question.
- For ptxas diagnostics, distinguish compile resource reports from measured
  runtime performance.

## Troubleshooting Rules

- If a build fails, identify whether the failure is host compilation, device
  compilation, ptxas assembly, device linking, runtime JIT, or module loading.
- Unsupported-instruction errors usually require checking target SM, PTX ISA
  version, CUDA Toolkit version, and architecture-specific code paths together.
- Missing-symbol errors in device code often point to separable compilation,
  device linking, template instantiation, or runtime linker setup.
- Runtime JIT failures can come from driver/toolkit mismatch, target mismatch,
  unsupported PTX version, missing link inputs, or invalid options.
- Do not add broad flags globally until the narrow failing translation unit,
  generated source, or JIT option set is understood.
