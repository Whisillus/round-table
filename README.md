# round-table

Agent presets for DeepSeek Harness, organized as a round table: one presiding
agent owns each task and convenes specialist agents when the work calls for it.

> 为 DeepSeek Harness 设计的一组 agent preset，按圆桌结构组织：由一位主持者
> 对每项任务负全责，必要时召集专职 agent。

The repository currently ships one preset. The remaining seats are designed
before they are implemented, so each addition arrives with a reason and a
verification step rather than as a batch.

> 当前仅交付一位 preset。其余席位先设计、后实现，因此每一项新增都附带理由与
> 验证步骤，而非成批加入。

## Contents

| Path | Purpose |
|---|---|
| `presets/arthur.patch.yml` | The presiding agent's declaration |
| `agents/GLOBAL-AGENTS.md` | Working agreements, installed as `~/.agents/AGENTS.md` |
| `package.json` | Bundle manifest declaring the patch layers |

## Presets

| id | Name | Scope |
|---|---|---|
| `arthur` | Arthur（亚瑟） | Presiding agent: full tool surface, delegates on demand |

Arthur handles localized work directly and delegates when a task requires
surveying many files, a tool surface that should not stay open for the whole
session, or an independent reading that could change the conclusion.

> Arthur 直接处理局部工作；当任务需要勘察大量文件、需要不宜全程常驻的工具面，
> 或需要一项可能改变结论的独立判断时，才委派。

## Install

Installing requires `pnpm`; `dsh plugin` forwards its arguments to it.

```bash
corepack enable pnpm
dsh plugin --profile web add link:/absolute/path/to/round-table
```

Restart `dsh` afterwards. Presets are composed at startup, so a bundle-layer
change is not picked up by a running process. Arthur then appears under **Custom**
in the preset selector.

Use `link:` rather than a bare path: it pins the symlink semantics, so editing a
preset file here needs only a restart, not a reinstall.

> 安装后必须重启 `dsh`。preset 在启动时合成，运行中的进程不会感知 bundle 层变更。
> 使用 `link:` 而非裸路径，可确定其为符号链接语义——修改本仓库的 preset 文件后
> 只需重启，无需重装。

## Verify composition without installing

```bash
DSH_HOME=$(mktemp -d) dsh --profile web --dump-config --patch ./presets/arthur.patch.yml
```

Point `DSH_HOME` at a throwaway directory. `--dump-config` rewrites the profile's
`cordis.yml` before printing, so running it against the live profile has a side
effect even though it mounts nothing.

What this checks: YAML syntax, `!!js` expressions, patch targeting, and the
composed row order. What it does not check: whether plugin names resolve, whether
a preset id collides, and whether activation succeeds. Those surface only at
mount time.

> 该命令验证语法、`!!js` 表达式、补丁定位与合成顺序；不验证插件名解析、id 冲突
> 与激活成败——后者仅在真实挂载时暴露。

## Install the working agreements

```bash
cp agents/GLOBAL-AGENTS.md ~/.agents/AGENTS.md
```

The rename is part of the install: the file is named for what it contains here,
and only becomes `AGENTS.md` at its destination.

> 复制时改名是安装步骤的一部分：该文件在本仓库按内容命名，到达目标位置后才成为
> `AGENTS.md`。

## Apply them inside this repository

Nothing reads `agents/` automatically. To have this repository governed by the
same agreements, copy the file to the repository root once:

```bash
cp agents/GLOBAL-AGENTS.md AGENTS.md
```

Keep the two in sync, or skip this and rely on the global copy — the duplicate is
not tracked here, because the file is a product of this repository rather than a
rule for its own maintenance.

> 该文件是本仓库的产物，不是本仓库的规则，因此不会自动加载。若希望本仓库也受其
> 约束，可复制一份到根目录并保持同步。

## Design notes

- The tool surface mirrors the shipped `standard` preset, with one omission:
  `workflow-ptc` and `tool-workflow` are absent. The workflow engine registers a
  standing prompt section on every request, and no orchestration fan-out is
  configured yet.
- `tool-subagent` omits `agentPreset` and `allowedAgentPresets`. A preset id in
  that allowlist is validated at mount time, so the row gains them only once the
  specialist presets exist. Until then a spawned child inherits `arthur` itself.
- The plan-mode section is copied verbatim from the shipped `standard` preset.
  Upstream wording changes will not propagate; that is the cost of a preset being
  a snapshot rather than an overlay.

## Status

Composition verified with `--dump-config`. The bundle is not installed.
