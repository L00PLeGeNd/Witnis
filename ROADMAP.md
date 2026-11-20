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
- Cross-platform **`witnis-core`** binary releases + Python `pip` fallback (**landed** — [`docs/BINARY.md`](docs/BINARY.md); full CLI still pip)  
- Browser demo (Studio / token-refresh) — **landed** `witnis browser-demo` / `scene --open` ([`docs/demo-browser.md`](docs/demo-browser.md))  
- README restructure + MCP/Harnis templates (landed under `examples/`)  
- `witnis loop-init` — default Harnis wrap as install accessory (repos stay separate)  
- PetClinic human GT subset (**landed** human-v1 → **human-v2 adjudicated**, 16 tasks; not dual-human) + Benchmark V1 numbers publish  
- Failure-case gallery (**landed** [`docs/FAILURE_CASES.md`](docs/FAILURE_CASES.md))  
- Issue/Discussion templates (**landed** under `.github/`)  
- Seed: [`examples/witnis-harnis-starter/`](examples/witnis-harnis-starter/) (**landed**)  
- CI bench report page (**landed** — [`docs/benchmarks/ci-report.md`](docs/benchmarks/ci-report.md); artifact + job summary)

### Mid (2–5 months)

- MCP directory listings (**payloads landed** — [`docs/mcp-listings.md`](docs/mcp-listings.md); form submit after push)  
- Flagship posts; Harnis co-marketing (**drafts landed** — [`docs/marketing/`](docs/marketing/); publish after push)  
- Incremental index, export reports, PR/CI impact as default adopter path (**docs landed** — [`docs/adopter-path.md`](docs/adopter-path.md))  
- Adopters + Showcase; good-first-issue pipeline (**landed** — [`ADOPTERS.md`](ADOPTERS.md) · [`docs/SHOWCASE.md`](docs/SHOWCASE.md) · [`docs/community/`](docs/community/))  
- PetClinic dual-annotator protocol + human-v2 adjudication (**landed** — [`docs/benchmarks/petclinic-human-v2.md`](docs/benchmarks/petclinic-human-v2.md); external Annotator B still welcome for `human_dual`)  

### Long (5–9 months+)

- Fuller Rust binary path (**7.0 landed** — [`docs/rust-full-binary.md`](docs/rust-full-binary.md) · `witnis-core parity`; ports still open)  
- Extension points (**landed** — [`docs/extensions.md`](docs/extensions.md))  
- Public bench miss-case surface (**landed** — [`docs/benchmarks/miss-cases.md`](docs/benchmarks/miss-cases.md))  
- Security model hardening (**checklist landed** — [`docs/security-hardening.md`](docs/security-hardening.md); container profile still open)  
- Committer growth path (**landed** — [`docs/community/committer-growth.md`](docs/community/committer-growth.md))  
- Stay niche: evidence envelope + audit loop as the moat  

## Explicitly deferred

Agent A/B **execution** (until baseline), Java AOP/tx deep dive, Historical Knowledge, Marketplace GitHub App (Action first), Studio redesign beyond demo, monopoly marketing claims.
