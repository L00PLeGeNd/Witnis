# Harnis × Witnis co-marketing kit

**Rule:** one story — **Trusted Agent Loop**. Never sell Harnis as an OS sandbox. Never sell Witnis as “full program proof.”

| Piece | Says | Does not say |
| --- | --- | --- |
| Witnis | Witnesses claims (impact · evidence · PR gate · gated verify) | Replaces CodeQL / LSP / agents |
| Harnis | Seatbelts stdio MCP `tools/call` / path reads | Kernel/container isolation |
| Loop | Same narrative on both READMEs | “Monopoly” / “only solution” |

---

## Shared one-liners

**EN**

- Witnis grounds the claim; Harnis constrains the tools.  
- Evidence on the PR. Seatbelt on the MCP.  
- `witnis loop-init` — Trusted Agent Loop in one command.

**ZH**

- Witnis 见证主张；Harnis 约束工具。  
- PR 上贴证据；MCP 上加安全带。  
- `witnis loop-init`：一条命令装上闭环。

---

## Dual README blurb (paste)

```markdown
**Trusted Agent Loop:** [Witnis](https://github.com/L00PLeGeNd/Witnis) evidence → `pr-gate` → gated verify → [Harnis](https://github.com/L00PLeGeNd/Harnis) stdio MCP seatbelt (not an OS sandbox).
`witnis loop-init` writes the wrap.
```

---

## Launch checklist (same week)

| Day | Witnis | Harnis |
| --- | --- | --- |
| 0 | Push Stage commits; confirm CI green | Push listing doc if pending |
| 1 | Publish flagship post / Discussion | Quote/RT with seatbelt clarification |
| 1 | Submit Glama / mcp.so (see `docs/mcp-listings.md`) | Confirm Glama claim |
| 2 | Pin Discussion + link starter kit | Pin threat model + loop-init |
| 3 | Optional Dev.to cross-post | Optional short “why seatbelt ≠ sandbox” note |

Flagship draft: [`flagship-post-trusted-agent-loop.md`](flagship-post-trusted-agent-loop.md).

---

## Graphic brief (if/when designing assets)

- One composition: brand **Witnis** dominant; Harnis as accessory label  
- Motif: evidence envelope strip + thin “seatbelt” rail — no neon, no purple glow  
- Palette: ink `#121c18` · accent `#0c5c48` · paper `#eef3f0` (match browser-demo)  
- Must include subtitle: “seatbelt — not a sandbox”

---

## Comment macros (PR / HN / Reddit)

**When someone asks “is this a sandbox?”**  
> Harnis is a stdio MCP seatbelt. It judges tools/call before the child process. It is not an OS/container jail — threat model in the Harnis repo. Witnis authorize≠sandbox the same way.

**When someone asks “why not just Claude Code?”**  
> Agents already edit. Witnis returns typed impact + evidence statuses + a PR gate. Harnis optionally wraps the MCP so credential paths and destructive calls can be denied before they run.

**When someone cites Blastline / impact Actions**  
> They comment reachability. We comment evidence statuses, limitations, blocked vs automation-verified, and pair with Harnis. Same loop on MCP and GitHub.
