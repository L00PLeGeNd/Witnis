# Witnis Design Spec

**Date:** 2026-11-03  
**Status:** Draft for review  
**Codename etymology:** *Witness* → **Witnis** (sibling to Harnis ← *Harness*)

---

## 1. One-liner

**Witnis** is local-first engineering verification infrastructure for AI coding agents: understand the repository, trace why code changed, and verify that changes hold — with evidence, not vibes.

Not another codebase chatbot. Not a PDF/folder RAG shell.

**Pairing with Harnis**

| Project | Role |
|---|---|
| **Harnis** | Safety harness — constrain what an agent may *do* |
| **Witnis** | Engineering witness — ground what an agent may *claim* and *prove* |

Same worldview, different layer. v1 does **not** couple the two codebases; complementary narrative only.

---

## 2. Problem

AI coding agents can read, edit, and run tests, but often cannot:

1. Understand real project structure and call/dependency relationships  
2. Explain *why* code exists (Git evolution, not just current text)  
3. Bound the blast radius of a change  
4. Prove a change did what was intended  
5. Separate observed facts from model guesses  

Existing “code intelligence MCP” tools crowd **search + graphs**. The sharp wedge is **evidence-graded answers + change verification**, not another embedding index.

---

## 3. Product principles (frozen)

1. **Core independent of MCP** — SDK / CLI / MCP / Studio are adapters  
2. **Evidence before chat** — engineering facts first; LLM explains/plans optionally  
3. **Verification is core**, not a plugin — otherwise Witnis collapses into a code-graph MCP  
4. **Repository-native · Evidence-first · Git-aware · Model-agnostic · Agent-native · Local-first · Read-only by default**  
5. **Vectors optional** — SQLite + FTS5 + typed relations are the foundation  
6. **Uncertainty is first-class** — prefer `partial` + `limitations` over false certainty  
7. **English product surface**; i18n for UI: `en`, `zh`, `pt`, `fr`, `ru`  
8. **No LLM required** for structure analysis, search, Git facts, or basic verification orchestration  

---

## 4. Non-goals (v1 boundary)

| In scope | Out of scope |
|---|---|
| Local repo index & structure | General chatbot product |
| Git evolution ↔ symbols | PDF / generic folder knowledge base |
| Evidence objects & statuses | Cloud repo hosting / multi-tenant SaaS |
| Impact analysis | Default auto-mutation of user repos |
| Authorized verification runs | Full CI/CD platform |
| MCP + CLI (+ Studio later) | Replacing the IDE or the agent |

---

## 5. Product shape (priority)

```
Witnis Core  >  Witnis MCP  >  Witnis CLI  >  Witnis Studio (local web)
```

- **Core:** parse, index, relations, git, evidence, impact, verification scheduling  
- **MCP:** primary distribution into Cursor / Claude / other MCP clients  
- **CLI:** human debug, scripting, CI-friendly checks  
- **Studio:** showcase + inspect graphs, evidence, verification reports (not the temple)

Model providers: OpenAI-compatible APIs (default for NL) + Ollama (optional). Core facts work offline without any model.

---

## 6. Architecture

### 6.1 Layers

```
Integration   MCP · CLI · Studio · SDK
Intelligence  Orchestrator · Understanding · Change · Impact · Verify · Evidence
Analysis      Tree-sitter · (LSP later) · Git · Test discovery · Config
Data          SQLite metadata · FTS5 · Relations · Snapshots · Reports
Source        Git working tree · Build/test · Optional runtime traces (later)
```

**Hard rule:** deterministic engineering facts must not depend on an LLM.

### 6.2 Engines

| Engine | Responsibility | Priority |
|---|---|---|
| Repository Understanding | Files, symbols, refs, calls, modules, tests discovery | P0 |
| Change Intelligence | Commit / Diff / Blame → file & symbol mapping | P0 |
| Evidence Engine | Typed evidence + status lifecycle | P0 (differentiator) |
| Impact Analysis | Direct / transitive / behavioral / uncertain | P0 after graph |
| Verification Engine | Plan → authorized run → before/after report | P1 (product core, after MCP) |
| Runtime Intelligence | Traces fused with static facts | P2 |

### 6.3 Evidence model (core differentiator)

Each evidence item includes: id, repo id, source type, source ref, path/lines when applicable, captured_at, content/commit version, status, provenance.

**Statuses (not a single fuzzy score):**

- `observed` — measured from repo/tools  
- `derived` — inferred from observed facts  
- `verified` — confirmed by an explicit verification run  
- `unverified` — not yet checked  
- `contradicted` — conflicts with other evidence  
- `stale` — underlying source changed  

**Response envelope (all tools):**

```json
{
  "status": "success | partial | failed",
  "repository": { "name": "...", "revision": "..." },
  "result": {},
  "evidence": [],
  "limitations": [],
  "generated_at": "ISO-8601 UTC"
}
```

### 6.4 Storage

- SQLite: repositories, files, symbols, relations, commits, changes, snapshots, evidence, verification_runs, test_results  
- FTS5: keyword search  
- Filesystem: bulky reports / optional artifacts  
- Vector index: **optional plugin only**

No Neo4j / ES / Redis required for v1.

---

## 7. MCP tool surface (engineering semantics)

| Tool | Purpose | Auth |
|---|---|---|
| `repo_overview` | Structure / languages / index health | read |
| `repo_search` | Code + symbol search | read |
| `trace_symbol` | Defs, refs, call relations | read |
| `explain_code` | Explanation bound to evidence | read |
| `explain_change` | Commit/diff analysis | read |
| `analyze_impact` | Blast radius of a change | read |
| `find_related_tests` | Related tests | read |
| `get_evidence` | Fetch / filter evidence | read |
| `create_verification_plan` | Plan checks for a diff | read |
| `run_verification` | Execute authorized checks | gated |
| `get_verification_report` | Report | read |

MCP adapter validates params, enforces permissions, calls Core — **no** AST/Git/DB logic inside the adapter.

---

## 8. Security (P0 from day one)

- Default **read-only**; mutation mode off  
- Path sandbox; symlink escape defense  
- Honor `.gitignore` + deny lists (`.env`, keys, etc.)  
- Secret redaction in outputs/logs  
- Treat repo text (README/comments) as **untrusted** (prompt-injection aware)  
- Verification: allowlisted tasks, cwd jail, timeouts, explicit user/agent authorization  
- Never let the agent freely concatenate shell strings for verification  

Harnis remains the behavioral moat when users stack both; Witnis still ships its own sandboxing.

---

## 9. Language & stack decisions

### 9.1 Language depth strategy

Do **one language deeply** before many shallowly.  
**v0.1 recommendation:** Python **or** TypeScript/Java first (pick at implementation plan time based on fixture availability and author velocity). Plugin-style analyzers thereafter (`analyzers/<lang>`).

Tree-sitter for syntax; LSP/specialized analyzers later for harder cross-file semantics. Unknown edges must surface as `uncertain` / `limitations`, never silent omission-as-certainty.

### 9.2 Implementation language

Architecture does **not** freeze Rust. Options:

- **Rust Core** — best long-term perf/deploy story; slower solo ramp  
- **Python Core** — fastest path given Harnis adjacency; must keep adapter boundaries clean  

**Frozen:** Core ↔ Adapter decoupling. **Open until plan:** Core language choice.

### 9.3 Suggested monorepo layout (illustrative)

```
witnis/
  core/                 # or crates/witnis-core
  cli/
  mcp/
  apps/studio/          # later
  analyzers/
  fixtures/
  benchmarks/
  docs/
  packages/             # shared types / model adapters
```

---

## 10. Roadmap (quality-gated, not calendar-gated)

| Version | Deliverable |
|---|---|
| **v0.1** | Core: scan, SQLite, Tree-sitter symbols, CLI search/overview |
| **v0.2** | Relations, Git evolution, incremental index, Evidence engine |
| **v0.3** | MCP server + agent integration tests + permissions |
| **v0.4** | Impact analysis + richer evidence queries |
| **v0.5** | Verification engine (build/test/static, reports) |
| **v0.6** | Studio (status, graph, evidence, reports) + i18n |
| **v0.8** | Runtime intelligence (optional traces) |
| **v1.0** | Stable contracts, cross-platform release, docs, public benchmarks |

### Acceptance themes (public benchmarks later)

Compare against: raw git+grep, naked coding agent, naive RAG, existing code MCP.  
Metrics: symbol/evidence line accuracy, impact recall (defined sets), incremental consistency, latency, token cost, zero unauthorized writes, core paths runnable without LLM.

---

## 11. Open source & brand

- **Name:** Witnis  
- **Tagline candidates:**  
  - *Witness your codebase.*  
  - *Understand. Trace. Verify.*  
  - *Engineering proof for AI agents.*  
- **README:** English first; localized docs optional  
- **License lean:** Apache-2.0 (preferred) or MIT — finalize at repo init after dependency scan  
- **Visual direction:** restrained engineering tool (not “AI glow / robot brain”). Sibling energy to Harnis: short coined name, serious infra tone  
- **GitHub:** `L00PLeGeNd/Witnis` (repo name free under this account as of 2026-11-03). Note: GitHub user handle `witnis` is taken by someone else — we use org/user `L00PLeGeNd` + repo `Witnis`

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Scope explosion | Strict phase gates; Studio/Runtime last |
| Commodity code-graph MCP | Lead with evidence statuses + verification loop |
| Shallow multi-language | One deep analyzer first |
| LLM washing facts | Facts from Core only; model for NL/planning |
| Solo bandwidth | Ship CLI+MCP before Studio polish |

---

## 13. Architecture freeze checklist

Before writing production code beyond spikes:

- [ ] Evidence schema v0 frozen  
- [ ] Index lifecycle (full + incremental) written  
- [ ] MCP tool contracts drafted  
- [ ] Security defaults documented  
- [ ] First language + Core language chosen  
- [ ] Fixture repo + 10 seed benchmark questions defined  

---

## 14. Immediate next steps (after this spec is approved)

1. Write implementation plan for **v0.1 only** (Foundation)  
2. Build locally only: spike index a fixture repo → CLI `overview` / `search` → prove SQLite+Tree-sitter path  
3. No Studio, no multi-provider UI, no Verification in v0.1  
4. **Release gate:** do **not** create or publish a public GitHub repo until there are real results (working demo / credible benchmark). Design-only or empty public repos are forbidden for Witnis.

---

## 15. Decision log

| Decision | Choice |
|---|---|
| Name | **Witnis** |
| Category | Engineering verification infra for agents |
| Distribution | MCP-first, CLI-native, Studio optional |
| Differentiator | Evidence lifecycle + verification, not RAG |
| Harnis relation | Complementary narrative; no hard dependency in v1 |
| i18n | en primary; zh/pt/fr/ru for UI later |
| Models | Optional; OpenAI-compatible + Ollama |
