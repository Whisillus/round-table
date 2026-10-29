# round-table

Agent presets for DeepSeek Harness, organized as a round table: one presiding
agent owns each task and convenes specialist agents when the work calls for it.

> 为 DeepSeek Harness 设计的一组 agent preset，按圆桌结构组织：由一位主持者
> 对每项任务负全责，必要时召集专职 agent。

The repository currently ships two presets. The remaining seats are designed
before they are implemented, so each addition arrives with a reason and a
verification step rather than as a batch.

> 当前交付两位 preset。其余席位先设计、后实现，因此每一项新增都附带理由与
> 验证步骤，而非成批加入。

## Contents

| Path | Purpose |
|---|---|
| `presets/perceval.patch.yml` | The investigator's declaration |
| `presets/arthur.patch.yml` | The presiding agent's declaration |
| `agents/GLOBAL-AGENTS.md` | Working agreements, installed as `~/.agents/AGENTS.md` |
| `package.json` | Bundle manifest declaring the patch layers |

## Presets

| id | Name | Scope |
|---|---|---|
| `arthur` | Arthur（亚瑟） | Presiding agent: full tool surface, delegates to Perceval |
| `perceval` | Perceval（珀西瓦尔） | Read-only investigator: no write tool, no delegation, no user questions |

Arthur handles localized work directly and delegates when a task requires
surveying many files, a tool surface that should not stay open for the whole
session, or an independent reading that could change the conclusion. Delegation
defaults to `perceval`, so a delegation is read-only research unless the model
explicitly selects `arthur` for a full-capability child. Every delegation is
research or a bounded independent subtask — Arthur still does small work itself.

> Arthur 直接处理局部工作；当任务需要勘察大量文件、需要不宜全程常驻的工具面，
> 或需要一项可能改变结论的独立判断时，才委派。委派默认交给 `perceval`，因此除非
> 模型显式选择 `arthur` 以获取全能力子 agent，委派都是只读调研。小事仍由 Arthur
> 自行处理。

Perceval cannot modify the workspace — `tool-fs` registers neither `write` nor
`edit` — cannot delegate, and cannot ask the user. It reports what it could not
establish instead of asking, so an incomplete answer names its gaps.

> Perceval 无法修改工作区（`tool-fs` 不注册 `write` 与 `edit`），无法委派，也无法
> 向用户提问。它把无法证实之处作为结果报告，而非转而询问。

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

- Arthur's tool surface mirrors the shipped `standard` preset, with one omission:
  `workflow-ptc` and `tool-workflow` are absent. The workflow engine registers a
  standing prompt section on every request, and no orchestration fan-out is
  configured yet.
- **Patch order matters.** `allowedAgentPresets` ids are resolved while Arthur
  mounts, and a preset publishes its record only after fully mounting. So
  `perceval.patch.yml` must be listed before `arthur.patch.yml` in
  `dsh.bundle.patch`; the reverse order fails Arthur's activation with
  `agent-preset/not-found`, and removing `perceval` breaks that mount rather than
  degrading it to a single option. Preset `order` numbers control selector
  position, not load order.
- `allowedAgentPresets` is `[perceval, arthur]` with `perceval` as the default, so
  an unspecified delegation is read-only research while an explicit `arthur`
  yields a context-free child with the full tool surface. Self-reference is safe
  because the registry publishes a definition's record before activating it.
- `subagent_fork` accepts no preset selection: it inherits the parent preset and
  the conversation, and is the way to continue an existing thread.
- Perceval's read-only guarantee is structural for files (`tool-fs` registers
  neither `write` nor `edit`) but only advisory for the shell. `tool-bash`
  exposes no read-only switch, so the rule rests on the persona and on the
  session's sandbox and approval policy.
- The plan-mode section is copied verbatim from the shipped `standard` preset.
  Upstream wording changes will not propagate; that is the cost of a preset being
  a snapshot rather than an overlay.

> **设计注记（中文摘要）**
>
> 补丁顺序有实质影响：`perceval.patch.yml` 必须排在 `arthur.patch.yml` 之前，
> 因为 Arthur 的 `allowedAgentPresets` 会在其挂载期间解析该 id，而 preset 只有
> 完整挂载后才完成注册。`order` 字段只影响选择器中的排序，与加载顺序无关。
>
> Perceval 的只读保证对文件是结构性的（`tool-fs` 不注册 `write`、`edit`），
> 对 shell 则仅为约定——`tool-bash` 没有只读开关。

## Status

Composition verified with `--dump-config`. The bundle is not installed.
