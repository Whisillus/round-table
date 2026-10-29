# round-table

Agent presets for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness),
organized as a round table: one presiding agent owns each task and convenes
specialist agents when the work calls for it.

> 为 DeepSeek Harness 设计的一组 agent preset，按圆桌结构组织：由一位主持者
> 对每项任务负全责，必要时召集专职 agent。

## Presets

| Preset | Writes | Runs code | Web | Delegates | Use for |
|---|---|---|---|---|---|
| `arthur` | yes | yes | yes | yes | Any task; the default choice |
| `perceval` | no | reads only | yes | no | Broad research, comparisons, feasibility |
| `bedivere` | no | inspects only | yes | no | Independent review of a substantial change |

Arthur handles small work itself and delegates when an answer needs many files,
a tool surface that should not stay open for the whole session, or an independent
reading. Delegation defaults to `arthur`, so an unspecified child is
full-capability; `perceval` and `bedivere` must be selected explicitly.

> Arthur 自行处理小改动；当任务需要跨大量文件、需要不宜全程常驻的工具面，或需要
> 一项独立判断时才委派。委派默认交给 `arthur`，即全能力子 agent；`perceval` 与
> `bedivere` 需显式选择。

**Perceval** answers "what is it, what are the options". Its filesystem tools
cannot write, so findings come back as text. It cannot ask, delegate, or resolve
ambiguity with the user; it states the assumption it made and the gaps it left.

**Bedivere** answers "is this change sound". It reviews by inspection only: no
tests, no builds, no code execution. Anything that needs running is returned as
an open question with the command that would settle it, and the verdict records
`Execution: none (static review)`. It judges necessity at two levels — whether
the change is needed at all, and which changed lines earn their place — and holds
style to two authorities: what the user asked for, and what the project already
establishes.

> Perceval 回答「是什么、有哪些选择」；其文件系统工具无法写入，结论以文本返回。
> Bedivere 回答「这次改动是否站得住」；它仅做静态审查，凡需执行才能定论的，都以
> 待决问题交回并注明 `Execution: none (static review)`。二者都不会向用户提问，
> 也不会再委派。

## Install

Requires DSH `>= 0.2.1-rc.2` and `pnpm`.

```bash
corepack enable pnpm
dsh plugin --profile web add link:/absolute/path/to/round-table
```

Restart `dsh` afterwards: presets are composed at startup, so a running process
does not see a bundle-layer change. The presets then appear under **Custom** in
the preset selector. Use `link:` rather than a bare path — it pins symlink
semantics, so editing a preset here needs only a restart.

> 安装后必须重启 `dsh`，preset 在启动时合成。使用 `link:` 可确定符号链接语义，
> 修改本仓库的 preset 后只需重启，无需重装。

## Choosing a preset

Each new session picks a preset in the selector; the default for future sessions
is set under Settings → General. A preset is fixed when the session starts, so an
existing session keeps the composition it was created with.

Delegation inside a session is separate from the preset you chose: Arthur asks the
model to pick `perceval` or `bedivere` when the task is research or review, and
otherwise spawns a full-capability child.

> 选择器决定新会话的 preset；已存在会话保持创建时的组合。会话内的委派是另一件
> 事：研究与审查会显式指定 `perceval` / `bedivere`，其余情况派生全能力子 agent。

## Working agreements

`agents/GLOBAL-AGENTS.md` holds language- and style-level working agreements
produced by this repository. Install them globally by copying, renaming on the
way:

```bash
cp agents/GLOBAL-AGENTS.md ~/.agents/AGENTS.md
```

Nothing here loads `agents/` automatically, and this repository deliberately does
not keep a root `AGENTS.md`: the file is a product of this repository, not a rule
for maintaining it.

> `agents/GLOBAL-AGENTS.md` 是本仓库产出的工作约定，复制时改名即完成全局安装。
> 本仓库不保留根目录 `AGENTS.md`：该文件是产物，不是维护本仓库的规则。

### Project memory

All three presets also load `.arthur.md` from the repository root, if it exists.
It is Arthur's own working memory for a repository — the commands that really
work, environment quirks, non-obvious layout, decisions and their reasons, and
traps that look correct but fail. Arthur writes and prunes it as it works, and a
touched instruction file is reloaded within the same session, so a note takes
effect immediately.

The file is listed in `.gitignore` and is not meant to be committed: it records
machine-specific facts and changes often. No format is enforced, but the persona
asks for `## Commands`, `## Environment`, `## Layout`, `## Decisions`, and
`## Gotchas`, and for roughly a hundred lines — the file is loaded on every
request, so its size is a standing cost.

> 三个 preset 都会加载仓库根目录的 `.arthur.md`（若存在）。它是 Arthur 自己的
> 项目记忆：真正可用的命令、环境怪癖、非直观的布局、决策与理由、以及看似正确
> 但会失败的陷阱。Arthur 在工作过程中维护和清理它；指令文件被触碰后同一会话内
> 即重新加载，因此笔记立即生效。
>
> 本仓库将其列入 `.gitignore`，不提交：它记录机器相关的事实且变动频繁。格式无
> 强制，但 persona 要求分为 `## Commands`、`## Environment`、`## Layout`、
> `## Decisions`、`## Gotchas` 五节，并控制在约一百行以内——该文件在每次请求
> 时都进入上下文，其体量是常驻成本。

## Development

The bundle is a single manifest plus one patch file per preset. `dsh.bundle.patch`
order is the layer order.

```bash
DSH_HOME=$(mktemp -d) \
  dsh --profile web --dump-config \
  --patch ./presets/perceval.patch.yml \
  --patch ./presets/bedivere.patch.yml \
  --patch ./presets/arthur.patch.yml
```

Point `DSH_HOME` at a throwaway directory: `--dump-config` rewrites the profile's
`cordis.yml` before printing, so running it against a live profile has a side
effect even though it mounts nothing.

This validates YAML syntax, `!!js` expressions, patch targeting, and row order. It
does not validate whether plugin names resolve, whether a preset id collides, or
whether activation succeeds — those surface only at mount time.

> 该命令验证语法、`!!js` 表达式、补丁定位与行序；不验证插件名解析、id 冲突与激活
> 成败，后者仅在真实挂载时暴露。`DSH_HOME` 必须指向临时目录，因为 `--dump-config`
> 会先重写 profile 的 `cordis.yml`。

## License

MIT. See [LICENSE](LICENSE).
