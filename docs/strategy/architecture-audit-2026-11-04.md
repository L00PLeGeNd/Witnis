# Witnis Architecture Audit

**Status:** draft working paper — **not committed as a release claim**  
**Date:** 2026-11-04  
**Scope:** Core / CLI / MCP / SDK / Studio / Rust native / Evidence / Impact / Verify  
**Method:** code path review + fixture probes (mini_py, semantic_java_di)  
**Governing plans:** [`ROADMAP.md`](../../ROADMAP.md) (external sequencing) · [`2026-open-source-landing-plan.md`](2026-open-source-landing-plan.md) · [`2026-Q4-next-phase-plan.md`](2026-Q4-next-phase-plan.md) (engineering notebook)

> This document answers Phase-1 gate questions. It is deliberately harsh.  
> Fixture green ≠ real-project proof.

---

## 0. Executive answers (Phase-1 acceptance questions)

- **What engineering relations can Witnis actually understand today?** — **Python:** AST symbols + imports / inherit / decorate / calls / overrides (name-level). **JS/TS/Go:** shallow regex symbols + imports/calls. **Java:** symbols + imports/extends + **implements / injects / typed field calls** (regex Spring-style) — indexed, but **not fully consumed by Impact**.
- **Which relations are only syntactic inference?** — Almost all call/import/DI edges are **DERIVED** from text/AST patterns. No classpath, no bytecode, no Spring container, no runtime traces in the default path.
- **Which results are truly verified?** — Only steps under gated `verify --execute` + `WITNIS_ALLOW_VERIFY=1` (pytest/compileall/syntax/import-graph). Search/trace/impact are **not** VERIFIED.
- **Largest technical bottleneck?** — **(1)** Impact/Change Intelligence still stringly and incomplete vs indexed relations (esp. Java callers / DI). **(2)** Evidence not bound to index snapshot + content hash graph. **(3)** Dual Python/Rust engines diverge; Java forced onto Python. **(4)** No real-repo Precision/Recall baseline yet.

**Go / no-go for large feature work:** **NO-GO.** Finish defect inventory + Benchmark V1 annotation rules + one real Java/Spring corpus pin before Phase-2 semantic expansion beyond fixing Impact consumption of already-indexed edges.

---

## 1. System map (as built)

```
Agent / Human
    |-- CLI (typer) --------\
    |-- MCP (FastMCP) -------+--> witnis.core.tools / verify / index
    |-- SDK (re-exports) ---/
    |-- Studio (static HTML render from tools)
              |
         Store (SQLite + FTS5)
              |
    +---------+---------+
    |                   |
 Python parsers     Optional Rust (_native)
 (AST / regex)      discover/hash/shallow parse/index/search
```

**Seam reality:** Almost all product behavior funnels through `src/witnis/core/tools.py` (~2300+ lines) — a **shallow mega-module**: large interface surface, high change risk, hard to test locally. MCP is a thin JSON adapter over the same functions. SDK re-exports the same set. CLI mixes orchestration + formatting.

**Deletion test:** Deleting MCP/SDK/Studio would not remove Core complexity; deleting pieces of `tools.py` without splitting would scatter complexity. Deepening target for later: split **Context / Change / Evidence** façades without renaming contracts.

---

## 2. Surface inventory

### 2.1 CLI (kept, uneven depth)

Present and useful for demos: `index`, `look`, `up`, `demo`, `scene`, `experiment`, `search`, `trace`, `impact`, `plan`/`verify`, `studio`, `bench`, `capabilities`, baselines, change helpers.

**Audit note:** CLI surface is already wide. Strategy says strengthen core workflow — prefer hardening `index → look/impact → plan/verify` over new verbs.

### 2.2 MCP (priority surface)

`mcp_server.py` exposes a large tool list (overview/status/search/trace/explain/impact/change-impact/tests/evidence/verify/…).  

**Strengths:** Host-agnostic; same envelopes as CLI.  
**Defects:** Tool count high → Agent tool-selection noise; no first-class “scene/story” MCP tool; verify execute still easy to misuse if host auto-sets env.

### 2.3 SDK

Thin re-export layer — good for scripts; does not add invariants.

### 2.4 Studio

Static HTML from `render_studio` — read-only dashboard. Matches strategy: **do not expand UI** until evidence/impact paths are trustworthy.

### 2.5 Rust / PyO3

Present for discover, hash, shallow multi-lang parse, SQLite index write, search.  
**Java trees prefer Python indexer** (Spring-aware relations). Rust `implements` exists; **injects not ported**. Parity tests exist but Jaccard floor is loose (0.4).

---

## 3. Data model & Evidence Envelope

### 3.1 SQLite (Store)

Tables: `repositories`, `files` (content_hash), `symbols`, `relations`, `commits`, `commit_files`, `index_snapshots`, `verification_runs`, `evidence_items`, `test_results`, FTS.

**Gaps vs strategy “version-bound evidence”:**

- **Index tied to git revision** — `repositories` has **no** `revision`/`head_sha` column. Envelope `repository.revision` is **live `git_head(root)` at query time**, not “revision when indexed”.
- **Symbol/relation provenance** — Relations store `status` (observed/derived) but not analyzer version or rule id.
- **STALE detection** — No automatic compare of file hashes vs evidence rows after edits.
- **CONTRADICTED** — Status string allowed in prose/contracts; no systematic producer.

### 3.2 Envelope shape

`make_envelope`: `status`, `repository`, `result`, `evidence[]`, `limitations[]`, `generated_at`.

Evidence items typically `{type, status, ...}` with statuses like `observed` / `derived` / verify step statuses.

**Probe (2026-11-04, mini_py `login` impact):** evidence statuses ∈ `{observed, derived}`; limitations correctly admit non-runtime and name collision risk.

**Verdict:** Envelope is a good **product contract**, but **not yet an evidence ledger** meeting plan §2.3 / §3.2.C.

---

## 4. Engineering Context (what parsers actually emit)

| Lang | Symbols | Relations | Notes |
| --- | --- | --- | --- |
| Python | AST (classes/funcs/methods) | imports, inherits, decorated_by, calls, overrides… | Strongest path; Jedi/LSP optional |
| JS/TS | regex shallow | imports/calls | No TS types |
| Go | regex shallow | imports/calls | No interfaces across packages |
| Java | regex + Spring-ish | imports, inherits, implements, injects, typed field calls | DI edges indexed; Impact ignores injects/implements |

**Fixture probe — `semantic_java_di` / `findUser` impact:**

- Direct edges returned: **1** (self-ish `UserService.findUser → findUser`)  
- **Missing:** `UserController` caller (typed call exists in index narrative/tests elsewhere)  
- Root cause candidates: (a) impact matches `target_equals` short name / exact string poorly against `UserService.findUser`; (b) no use of `injects`/`implements` in impact assembly.

This is a **P0 product defect** relative to the Java/Spring breakthrough narrative.

---

## 5. Change Intelligence (current)

| Capability | Present? | Quality |
| --- | --- | --- |
| explain_change (git name-status + blob parse) | Yes | Useful for touched files/symbols |
| analyze_change_impact | Yes | Chains explain_change → impact-like logic; still limited by relation quality |
| analyze_impact | Yes | Relation lookup; stringly; incomplete relation types |
| Impact path visualization | Partial | Mermaid export exists; Studio shows graphs |
| Predict vs actual | No | Plan Phase 4/实验三 — not built |
| Risk classification | No | — |

**Benchmark reality:** Public suite 21/21 is **acceptance** on mini fixtures vs grep. Ground-truth runner exists for vendored labels only. **No real Spring repo Precision/Recall.**

---

## 6. Evidence & Gated Verify

- **Dual gate (`--execute` + `WITNIS_ALLOW_VERIFY=1`)** — Works (probe: blocked → verified)
- **Command allowlist** — pytest / compileall
- **Path sandbox** — cwd under root
- **Isolation default** — worktree or **copy** + scrubbed env + FS diff; network **hint only**
- **Container / cgroup** — **Not present**
- **Version binding of verify report** — `verification_runs.revision` field exists; depends on plan/revision args
- **False-pass tracking** — Not a first-class metric in Core

Probe note: with allow+isolate, `static_compile`/`run_tests` reported `isolation` + `network=deny-hint`; syntax/import_graph steps are in-process (no isolation flag).

---

## 7. Capability checklist (honest)

### Can claim today (with limitations)

- Local index of multi-lang trees into SQLite  
- Search / look card / scene narrative on fixtures  
- Python-centric trace/impact with explicit limitations  
- Java DI **indexing** on Spring-style fixtures  
- Gated verify with soft isolation  
- MCP/CLI/SDK shared envelopes  
- Fixture GT + grep-vs-Witnis analysis experiment pack  

### Must not claim

- Mature Software Change Causality  
- Production Spring container fidelity (AOP/tx/proxy/@Primary)  
- Real-repo impact Precision/Recall leadership  
- Agent task success improvement (experiments paused; no filled A/B)  
- Hard multi-tenant sandbox  
- Historical knowledge moat  

---

## 8. Defect inventory (prioritized)

| ID | Sev | Area | Defect | Evidence |
| --- | --- | --- | --- | --- |
| D01 | P0 | Impact | analyze_impact did not query injects / implements | fixed in working tree (tests green; uncommitted) |
| D02 | P0 | Impact | Java/fixture caller miss for findUser | fixed in working tree (qualified target match; uncommitted) |
| D03 | P0 | Evidence | Index revision not stored; no STALE | fixed in working tree (indexed_revision + STALE limitation; uncommitted) |
| D04 | P0 | Benchmark | No real Java/Spring corpus with human GT | strategy + ground-truth manifest “planned” |
| D05 | P1 | Architecture | tools.py god-module (~2.3k LOC) | line count |
| D06 | P1 | Dual engine | Java injects Python-only; Rust parity incomplete | index.py prefer path; rust java.rs |
| D07 | P1 | Verify | Isolation ≠ OS/container; network deny is hint | verify_isolate + SECURITY |
| D08 | P1 | MCP | Large tool surface without workflow guidance tool | mcp_server tool list |
| D09 | P2 | Evidence | STALE/CONTRADICTED rarely produced | envelope usage |
| D10 | P2 | Impact | Transitive one-hop name collisions admitted but still returned | limitations text |
| D11 | P2 | Studio | Static only; easy to over-invest UI before Impact fixed | strategy P3 |

---

## 9. Benchmark V1 — annotation rules (draft)

Until real corpora land, **do not publish numeric leadership**.

### 9.1 Unit of labeling

For a pinned `(repo, commit, change_or_symbol)`:

- **Direct dependence** — Must change or recompile/retest when symbol changes (callers, implementors, inject sites)
- **Indirect dependence** — Two+ hops or framework-mediated (proxy, event) with documented reason
- **Test coverage link** — Test that fails or should be run if symbol changes
- **Non-impact** — Name collision / string hit only

### 9.2 Metrics

Precision / Recall / F1 on Direct and Indirect separately; path correctness on sampled Direct edges; never inflate by dumping all files.

### 9.3 Process

Dual annotator on hard samples; disagreement → third pass. Record rule version in every report.

### 9.4 First corpus recommendation (Phase-1 exit)

Pin **one** mid-size Spring Boot app (e.g. PetClinic or internal service) at a SHA; label ≥20 symbol/change cases before Phase-2 feature claims.

---

## 10. Experiment data record norm (for when experiments resume)

Minimum fields (align plan §7.4):

`experiment_id, project, commit, agent, model, arm, task_id, config_hash, input_uri, output_uri, log_uri, scores{}, failure_tags[], annotator, created_at`

Store under `benchmarks/experiments/reports/` (gitignored) + summary markdown only when reviewed.

---

## 11. Recommended next engineering slices (still Phase-1 / early Phase-2)

Ordered; **no commit implied**:

1. **Fix D01–D02:** Impact consumes `injects`/`implements` + improve Java/Python caller resolution against qualified names. Add regression on `semantic_java_di` / `auth_refresh`.  
2. **Fix D03:** Persist `indexed_revision` + snapshot id on queries; mark STALE when file hashes drift.  
3. **Benchmark harness:** one external Spring SHA + labeling sheet (even if labels incomplete).  
4. **Only then** expand Spring semantic rules (AOP/tx) per plan Phase-2.  

Explicitly **defer:** Studio redesign, new languages, PR bot, Historical Knowledge.

---

## 12. Audit limitations

- Did not run full `pytest` suite in this pass (earlier sessions: green; re-run before any release).  
- Did not audit every CLI command path.  
- Did not security-review verify isolation as a red team.  
- Did not open a real Spring Boot monorepo in this document’s probes.

---

## 13. Sign-off checklist for Phase-1 “exit”

- [x] Architecture map written  
- [x] Capability list (honest)  
- [x] Defect inventory  
- [x] Benchmark annotation rules draft  
- [x] D01–D03 fixed in working tree (uncommitted; tests green)  
- [x] Real corpus cloned + SHA `500158f7…` + **30** source-confirmed auto labels (`spring_petclinic_auto.json`)  
- [x] Bootstrap script: `scripts/bootstrap_petclinic_gt.py` (checkout gitignored)  
- [x] User review of audit direction (approved 2026-11-04)  
- [ ] Dual-human re-label subset (still open for 实验一 credibility)  
- [ ] Explicit “one commit / push” when user asks

**Recorder:** engineering agent (working tree). **Do not treat as published marketing.**
