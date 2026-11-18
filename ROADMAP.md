# Witnis Roadmap

**Positioning:** Trusted Agent Loop — evidence-backed blast-radius for AI coding agents, the same envelope on MCP and GitHub PRs, gated verify, Harnis as a stdio MCP seatbelt.

Give agents auditable impact evidence so edits are grounded, not vibes.

## Constraints (always on)

| Do | Do not |
| --- | --- |
| Evidence envelopes + trust statuses | Vector RAG / generic code Q&A |
| Gated verify; read-only by default | Full taint / data-flow product |
| Local SQLite index; MCP-first + **PR evidence gate** | Replace LSP / CodeQL |
| Honest capability boundaries | Call Harnis an OS sandbox |
| Partner with [Harnis](https://github.com/L00PLeGeNd/Harnis) seatbelt | Heavy IDE plugins before Core is trusted |

**Topics:** `mcp-server`, `ai-coding-agent`, `code-analysis`, `blast-radius`, `llm-agent`, `static-analysis`

## Trusted Agent Loop (primary narrative)

1. **Witnis** — index → look/impact/`pr-gate` envelopes  
2. **PR/CI gate** — sticky evidence comment + check run  
3. **Gated verify** — blocked until `WITNIS_ALLOW_VERIFY=1` + execute  
4. **Harnis** — wrap MCP (`tools/call` / path `resources/read`); optional editor hooks  

Full loop doc: [`docs/trusted-agent-loop.md`](docs/trusted-agent-loop.md)

## Dual track

| Track | Job | Near term |
| --- | --- | --- |
| **Conversion** | 10s value, 1min demo, copy-paste MCP, **PR gate on every PR** | `loop-init` + `pr-gate` Action, MCP/Harnis templates, binary, browser demo |
| **Credibility** | Honest bench before claims | PetClinic human GT + Direct/Indirect P/R; publish failure cases |

**Language face for demos/docs:** Python (deep) + TS/JS; Go usable.  
**Java:** honest shallow + existing Spring edges. PetClinic GT is a baseline artifact; Spring deep dive stays paused until Stage-1 conversion clears.

Growth plan: [`docs/strategy/2026-open-source-landing-plan.md`](docs/strategy/2026-open-source-landing-plan.md)  
Engineering notebook: [`docs/strategy/2026-Q4-next-phase-plan.md`](docs/strategy/2026-Q4-next-phase-plan.md) · [`docs/DEPTH.md`](docs/DEPTH.md)

Growth plan governs external sequencing. Where language investment conflicts, **follow this ROADMAP**.

## Horizon

### Short (0–2 months) — Stage 1

- **PR evidence gate** (`witnis pr-gate` + Action + dogfood) — highest parallel priority  
- Cross-platform single binary; Python `pip` fallback  
- Browser demo (Studio / token-refresh)  
- README restructure + MCP/Harnis templates (landed under `examples/`)  
- `witnis loop-init` — default Harnis wrap as install accessory (repos stay separate)  
- PetClinic human GT subset + Benchmark V1 numbers  
- CI bench report page; Issue/Discussion templates  
- Seed: `witnis-harnis-starter` (planned)

### Mid (2–5 months)

- MCP directory listings; flagship posts; Harnis co-marketing  
- Incremental index, export reports, PR/CI impact as default adopter path  
- Adopters + Showcase; good-first-issue pipeline  

### Long (5–9 months+)

- Fuller Rust binary; extension points; public bench with miss cases  
- Security model hardening; committer growth  
- Stay niche: evidence envelope + audit loop as the moat  

## Explicitly deferred

Agent A/B **execution** (until baseline), Java AOP/tx deep dive, Historical Knowledge, Marketplace GitHub App (Action first), Studio redesign beyond demo, monopoly marketing claims.
