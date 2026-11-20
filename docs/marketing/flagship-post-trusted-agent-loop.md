# Flagship post draft — Trusted Agent Loop

**Status:** draft for publish after Stage-1 commits are pushed  
**Channels:** GitHub Discussion / personal blog / Dev.to / X thread (cut-down)  
**Tone:** niche operator, not growth-hack. Evidence over vibes. No monopoly claims.

---

## Title options

1. **Agents already edit your repo. Who witnesses what they claim?**  
2. **The Trusted Agent Loop: evidence on every PR, a seatbelt on MCP**  
3. **Grep finds strings. Witnis witnesses claims. Harnis constrains tools.**

Recommended: **#2** for Launch; **#1** for HN/Dev.to hook.

---

## Body (EN)

Coding agents are useful because they change code. That is also why they scare careful teams.

They treat a text hit as a typed symbol.  
They miss call, inject, and inherit edges that define blast radius.  
They say “tests passed” when a chat once looked green.

**Witnis** does not replace your agent. It witnesses the claim:

- Local SQLite index of the tree  
- Every answer as an **evidence envelope** (`observed` / `derived` / `verified` / `stale` / `contradicted` / …)  
- Blast-radius impact agents can cite  
- **`witnis pr-gate`** — the same envelope as a sticky PR comment + check  
- Verify that stays **blocked** until you authorize it (`WITNIS_ALLOW_VERIFY=1` + execute)

**Harnis** does not replace your sandbox. It is a **stdio MCP seatbelt**:

- Sits between the client and the server  
- Judges `tools/call` and path-like `resources/read` **before** the child sees them  
- Denials return to the client; they never become tool executions  
- Not an OS/container jail — read the [threat model](https://github.com/L00PLeGeNd/Harnis/blob/main/THREAT_MODEL.md)

Together they are the **Trusted Agent Loop**:

```text
Agent intent
  → Witnis look / impact / pr-gate     (claims + evidence)
  → PR/CI sticky comment + check       (distribution)
  → plan-verify → authorize → verify   (proof)
  → Harnis mcp / hooks                 (what tools may run)
```

### Sixty seconds

```bash
uvx --from git+https://github.com/L00PLeGeNd/Witnis.git witnis loop-init
# merge .witnis/mcp.loop.json into Claude Code / Cline / Cursor

witnis look <symbol>
witnis pr-gate --base origin/main --head HEAD
witnis browser-demo       # token-refresh story in the browser (from Witnis checkout)
```

Starter kit to copy: [`examples/witnis-harnis-starter`](https://github.com/L00PLeGeNd/Witnis/tree/master/examples/witnis-harnis-starter).

### What we will not pretend

- Public acceptance bench ≠ “we understand every large repo”  
- Authorize ≠ OS sandbox; Harnis ≠ jail  
- PetClinic human-v2 is a **subset** baseline (Direct strong; Indirect still honest-miss on typed-use; not dual-human)  
- Full gallery: [FAILURE_CASES](https://github.com/L00PLeGeNd/Witnis/blob/master/docs/FAILURE_CASES.md)

### Links

- Witnis: https://github.com/L00PLeGeNd/Witnis  
- Harnis: https://github.com/L00PLeGeNd/Harnis  
- Loop doc: https://github.com/L00PLeGeNd/Witnis/blob/master/docs/trusted-agent-loop.md  

If you already run agents on PRs: start with **`pr-gate`**. If you already wrap MCP: start with **`loop-init`**. Same envelope either way.

---

## ZH 短版（可发即刻 / 即刻系 / 博客）

Agent 能改代码，也会把文本命中当成符号、漏影响面、把「测过一次」说成证明。

**Witnis** 是本地工程见证：证据信封、爆炸半径、`pr-gate` 贴到 PR、验证默认阻断。  
**Harnis** 是 stdio MCP **安全带**（不是 OS 沙箱）：拦的是进子进程之前的 `tools/call`。

合在一起是 **Trusted Agent Loop**。一分钟：`uvx --from git+https://github.com/L00PLeGeNd/Witnis.git witnis loop-init` → 合并 MCP 配置 → Action `pr-gate`。

诚实边界见 FAILURE_CASES；不吹垄断，不吹沙箱。

---

## X / Mastodon thread (cut)

1/ Agents edit. Someone still has to witness the claim.  
2/ Witnis: evidence envelopes + blast radius + PR gate + gated verify.  
3/ Harnis: stdio MCP seatbelt — not a jail.  
4/ `witnis loop-init` wires both.  
5/ Misses we publish: FAILURE_CASES. Repos in reply.
