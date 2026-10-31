# round-table

Agent presets and CUDA, CuTe C++, CuTe DSL, PDF, and Git workflow skills for
[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness),
organized as a round table: one presiding agent owns each task and brings in
specialists when the work calls for it.

> 为 DeepSeek Harness 提供 agent presets 以及 CUDA、CuTe C++、CuTe DSL、PDF 和 Git 工作流 skills，按圆桌结构组织：
> 由一位主持者对每项任务负全责，必要时召集专职 agent。

## Presets

| Preset | Writes | Runs code | Web | Delegates | Use for |
|---|---|---|---|---|---|
| `arthur` | yes | yes | yes | yes | Any task; the default choice |
| `perceval` | no | reads only | yes | no | Broad research, comparisons, feasibility |
| `bedivere` | no | inspects only | yes | no | Independent review of a substantial change |

**Arthur** handles tasks from investigation through implementation and verification,
bringing in specialists when research or an independent review would help.

**Perceval** investigates unfamiliar code and documentation, compares options, and
reports findings and uncertainties without modifying files or running project code.

**Bedivere** reviews correctness, necessity, maintainability, and consistency with
project conventions. It works by static inspection; checks that require tests,
builds, or code execution are left for an agent with execution permission.

> Arthur 负责调查、实现与验证，按需召集专职 agent。
> Perceval 负责研究和方案比较，不修改文件或运行项目代码。
> Bedivere 负责静态审查，不运行测试、构建或代码。

## Install

### Presets

Requires DSH `>= 0.2.1-rc.2` and `pnpm`.

```bash
corepack enable pnpm
dsh plugin --profile web add link:/absolute/path/to/round-table
```

Restart `dsh` after installation. The presets appear under **Custom** in the preset
selector. After updating the linked checkout, restart `dsh` to use the changes.

> 安装后重启 `dsh`，即可在 preset 选择器的 **Custom** 分类中找到这些 presets。
> 更新链接的仓库后，重启 `dsh` 使修改生效。

### Agreements and skills

Requires Bash 3.2+ and standard Unix file utilities. From the repository directory,
run:

```bash
bash install.sh                         # Install agreements and skills
bash install.sh --module agents         # Install agreements only
bash install.sh --module skills         # Install skills only
bash install.sh --module all            # Same as the default
bash install.sh --help
```

Agreements are installed to `~/.agents/AGENTS.md` and skills to `~/.agents/skills/`.
Preset installation is separate and uses the DSH command above.

Rerun the installer after updating the repository. Identical files are skipped;
to replace files whose contents differ, use `--overwrite`:

```bash
bash install.sh --overwrite
bash install.sh --module skills --overwrite
```

Unrelated files are preserved, and obsolete files are not removed automatically.
Destination paths must not contain symbolic links. If copying fails, files already
copied remain installed.

For a different destination, set `ROUND_TABLE_INSTALL_DIR` to an absolute path.
This changes the installation location; configure your agent to discover skills
there if needed.

> 需要 Bash 3.2+ 和标准 Unix 文件工具。在仓库目录运行 `bash install.sh`，
> 默认安装约定和 skills；使用 `--module agents` 或 `--module skills` 可单独安装。
> 更新仓库后重新运行即可更新安装内容，内容冲突需显式使用 `--overwrite`。
> 其他文件会保留，过时文件需手动清理；目标路径不能包含符号链接。
> 复制失败时，已完成的复制不会回滚。可通过 `ROUND_TABLE_INSTALL_DIR` 指定绝对路径，
> 并按需配置 agent 的技能发现目录。Presets 需使用上方 DSH 命令单独安装。

## Skills

The skills cover CUDA programming and the CuTe C++ and CuTe DSL APIs for layouts,
tensors, data movement, matrix multiplication, and pipelines. The PDF skill reads,
searches, renders, OCRs, splits, and merges PDF files. Git skills help prepare
commits and maintain project ignore rules.

| Skill | Use for |
|---|---|
| `cuda-basic` | CUDA entry point, kernels, memory, streams, and debugging |
| `cuda-general-reference` | NVIDIA documentation and local reference discovery |
| `cuda-build-toolchain` | NVCC, runtime compilation, linking, and binary inspection |
| `cuda-runtime-driver` | Runtime/Driver APIs, contexts, streams, memory, and graphs |
| `cuda-fence-sync-barrier` | Memory ordering, barriers, and async completion protocols |
| `cute-basic` | CuTe C++ entry point, conventions, predication, and debugging |
| `cute-layout` | C++ layouts, layout algebra, tiling, and partitioning |
| `cute-tensor` | C++ tensors, memory-space pointers, fragments, and slicing |
| `cute-copy` | C++ copy atoms, tiled copies, predication, and TMA |
| `cute-mma` | C++ MMA atoms, tiled MMA, fragments, and GEMM |
| `cute-pipeline` | C++ CUTLASS pipeline classes and producer/consumer protocols |
| `cutedsl-basic` | CuTe DSL entry point, JIT functions, types, and debugging |
| `cutedsl-layout` | DSL layouts, layout algebra, tiling, and partitioning |
| `cutedsl-tensor` | DSL tensors, pointers, register tensors, and slicing |
| `cutedsl-copy` | DSL copy atoms, tiled copies, predication, and TMA |
| `cutedsl-mma` | DSL MMA atoms, tiled MMA, fragments, and GEMM |
| `cutedsl-pipeline` | DSL pipeline classes and producer/consumer protocols |
| `process-pdf` | PDF text, tables, figures, OCR, search, and page splitting or merging |
| `write-git-commit` | Commit preparation, selective staging, and repository-aware messages |
| `write-gitignore` | Conservative ignore rules for local files and generated outputs |

DSH discovers skills installed in `~/.agents/skills/`. CUDA tooling and reference
materials are not included. `process-pdf` requires poppler (`brew install poppler`)
and, for scanned PDFs, tesseract. Skills follow the active agent's permissions;
Bedivere remains a static reviewer when using them.

> Skills 覆盖 CUDA 编程，以及 CuTe C++ 和 CuTe DSL 的布局、张量、数据搬运、矩阵乘法和流水线。
> PDF skill 用于读取、搜索、渲染、OCR、拆分和合并 PDF 文件。Git skills 用于准备提交和维护项目忽略规则。
> DSH 会发现安装在 `~/.agents/skills/` 下的技能；CUDA 工具和参考资料需另行准备。
> `process-pdf` 需要 poppler（`brew install poppler`），处理扫描件还需要 tesseract。
> 使用技能仍受当前 agent 的权限约束，Bedivere 始终只做静态审查。

## Choosing a preset

Choose a preset in the selector when starting a session. Set the default for future
sessions under **Settings → General**. Existing sessions keep their original preset.

Use Arthur for work that includes implementation, Perceval for research and
comparisons, and Bedivere for an independent static review.

> 新建会话时在选择器中选择 preset；在 **Settings → General** 设置后续会话的默认值。
> 已有会话保持原 preset。实现任务选择 Arthur，研究与比较选择 Perceval，
> 独立静态审查选择 Bedivere。

## Working agreements

The [working agreements](agents/GLOBAL-AGENTS.md) cover failure handling, scope,
readability, verification, and version control. Install them for use across your
repositories:

```bash
bash install.sh --module agents
```

> 工作约定涵盖错误处理、改动范围、可读性、验证和版本控制。
> 安装到 `~/.agents/AGENTS.md` 后，可在各仓库中使用。

### Project memory

All three presets use `.arthur.md` in the repository root when present. Arthur
maintains it to retain useful project knowledge across sessions, such as verified
commands, environment quirks, and decisions with their reasons. Keep machine-specific
notes out of version control.

> 三个 presets 都会使用仓库根目录的 `.arthur.md`（若存在）。Arthur 维护其中的
> 项目知识，例如已验证的命令、环境注意事项和决策理由，供后续会话参考。
> 与本机环境相关的笔记不应提交到版本控制。

## License

MIT. See [LICENSE](LICENSE).
