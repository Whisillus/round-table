# round-table

Agent presets for DeepSeek Harness, organized as a round table: one presiding
agent owns each task and convenes specialist agents when the work calls for it.

> 为 DeepSeek Harness 设计的一组 agent preset，按圆桌结构组织：由一位主持者
> 对每项任务负全责，必要时召集专职 agent。

The repository currently ships three presets. The remaining seats are designed
before they are implemented, so each addition arrives with a reason and a
verification step rather than as a batch.

> 当前交付三位 preset。其余席位先设计、后实现，因此每一项新增都附带理由与
> 验证步骤，而非成批加入。

## Contents

| Path | Purpose |
|---|---|
| `presets/perceval.patch.yml` | The investigator's declaration |
| `presets/bedivere.patch.yml` | The reviewer's declaration |
| `presets/arthur.patch.yml` | The presiding agent's declaration |
| `agents/GLOBAL-AGENTS.md` | Working agreements, installed as `~/.agents/AGENTS.md` |
| `package.json` | Bundle manifest declaring the patch layers |

## Presets

| id | Name | Scope |
|---|---|---|
| `arthur` | Arthur（亚瑟） | Presiding agent: full tool surface, delegates to the others |
| `perceval` | Perceval（珀西瓦尔） | Read-only investigator: no write tool, no delegation, no user questions |
| `bedivere` | Bedivere（贝狄威尔） | Read-only static reviewer: no write tool, no execution, no delegation |

Arthur handles localized work directly and delegates when a task requires
surveying many files, a tool surface that should not stay open for the whole
session, or an independent reading that could change the conclusion. Delegation
defaults to `arthur`, so an unspecified delegation is a context-free child with
the full tool surface — one that can write, which is why the persona requires the
task description to state the authorized changes. `perceval` and `bedivere` are
explicit choices for research and review respectively.

> Arthur 直接处理局部工作；当任务需要勘察大量文件、需要不宜全程常驻的工具面，
> 或需要一项可能改变结论的独立判断时，才委派。委派默认交给 `arthur`，即一个
> 上下文干净、具备完整工具面的子 agent——它能写，因此 persona 要求任务描述中
> 明确授权范围。调研与审查分别需显式选择 `perceval` 与 `bedivere`。

Perceval cannot modify the workspace — `tool-fs` registers neither `write` nor
`edit` — cannot delegate, and cannot ask the user. It reports what it could not
establish instead of asking, so an incomplete answer names its gaps.

> Perceval 无法修改工作区（`tool-fs` 不注册 `write` 与 `edit`），无法委派，也无法
> 向用户提问。它把无法证实之处作为结果报告，而非转而询问。

Bedivere reviews by inspection only and reports `Execution: none (static review)`.
Anything requiring a test run or a build is returned as an open question for
Arthur to settle, so a verdict never borrows authority it does not have. It
judges necessity at two levels — whether the change is needed at all, and which
changed lines earn their place — and holds style to two authorities: what the user
asked for, and what the project already establishes.

> Bedivere 仅做静态审查，并在结论中标注 `Execution: none (static review)`。凡需
> 运行测试或构建才能定论的，作为待决问题交回 Arthur，因此它的判定不借用未经
> 执行的权威。它从两个层级判断必要性：整个改动是否必要，以及哪些改动行真正
> 有其位置；风格则同时以用户要求与项目既有约定为依据。

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
  `perceval.patch.yml` and `bedivere.patch.yml` must both be listed before
  `arthur.patch.yml` in `dsh.bundle.patch`; the reverse order fails Arthur's
  activation with `agent-preset/not-found`, and removing either breaks that mount
  rather than degrading it to fewer options. Preset `order` numbers control
  selector position, not load order.
- `allowedAgentPresets` is `[arthur, perceval, bedivere]` with `arthur` as the
  default. Self-reference is safe because the registry publishes a definition's
  record before activating it, so resolving `arthur` during its own mount
  succeeds.
- `subagent_fork` accepts no preset selection: it inherits the parent preset and
  the conversation, and is the way to continue an existing thread.
- Read-only is structural for files in both specialist presets: `tool-fs`
  registers neither `write` nor `edit`, so no path is writable. It is advisory
  for the shell. `tool-bash` exposes no read-only switch, and the pre-execute
  policy hook its own source marks as a TODO is not implemented. A delegated
  child's approval policy is pinned to `never` and its sandbox mode is inherited
  from the parent session, so an in-workspace write would succeed silently
  instead of prompting. The persona is the only constraint there.
- Bedivere has no `tool-jobs` by design: review commands are short foreground
  reads, and waiting on a long job would be execution rather than review.
- When a review needs execution, Bedivere returns the command and the result that
  would settle it as an open question, and writes `Execution: none (static
  review)` in its closing section. A verdict therefore never claims a test result
  it did not obtain.
- The trigger for using Bedivere lives in its `description`, not in Arthur's
  persona: that text is what Arthur reads when choosing a preset, so the rule
  reaches only delegation decisions instead of every request. A few lines in one
  or two files are reviewed by Arthur itself.
- The plan-mode section is copied verbatim from the shipped `standard` preset.
  Upstream wording changes will not propagate; that is the cost of a preset being
  a snapshot rather than an overlay.

> **设计注记（中文摘要）**
>
> 补丁顺序有实质影响：`perceval.patch.yml` 与 `bedivere.patch.yml` 都必须排在
> `arthur.patch.yml` 之前，因为 Arthur 的 `allowedAgentPresets` 会在其挂载期间
> 解析这些 id，而 preset 只有完整挂载后才完成注册。`order` 字段只影响选择器中的
> 排序，与加载顺序无关。
>
> 两个专职 preset 的只读保证对文件是结构性的（`tool-fs` 不注册 `write`、`edit`），
> 对 shell 则仅为约定——`tool-bash` 没有只读开关，其源码中标注为 TODO 的
> pre-execute 策略钩子尚未实现。且子 agent 的审批策略恒为 `never`、sandbox 模式
> 继承父会话，因此工作区内的误写会静默成功，不会弹窗。
>
> Bedivere 不含 `tool-jobs`：审查命令都是短时间的前台读取，等待长作业属于执行而
> 非审查。凡需执行才能定论的，它把命令与预期结果作为待决问题交回 Arthur，并在
> 结论中标注 `Execution: none (static review)`。
>
> 使用 Bedivere 的触发判据写在其 `description` 而非 Arthur 的 persona 中：该文本
> 只在 Arthur 选择 preset 时被读到，因此规则只作用于委派决策，不进入每个回合。

## Status

Composition verified with `--dump-config`. The bundle is not installed.
