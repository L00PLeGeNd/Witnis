# Failure-case gallery

What Witnis **misses, misleads, or refuses to pretend**.  
Use this before quoting P/R or calling verify “proof.” Companion: [`DEPTH.md`](DEPTH.md) · PetClinic scores: [`benchmarks/petclinic-human-v2.md`](benchmarks/petclinic-human-v2.md).

Each case: **symptom → why → what to do**. IDs are stable for issues / reviews.

---

## F1 — Typed use was not a relation (Indirect FN) — **mitigated**

| | |
| --- | --- |
| **Seen in** | PetClinic human-v2 · `Person` → Indirect `OwnerController` |
| **Was** | Impact / Indirect recall **0.0** on a labeled 2-hop: controller methods take `Owner`, which inherits `Person`. |
| **Now** | Java emits `uses_type` (method params/returns); `analyze_impact` walks subclass typed-users into **transitive**. PetClinic Indirect on this task is **TP** at the pinned SHA. |
| **Still limited** | Signature-derived only — not flow-sensitive; JDK/collection names skipped; other languages not covered the same way. |
| **Do** | Cite Direct inject/inherit/call + `uses_type` for Java typed blast radius. Keep the GT Indirect expect so regressions surface. |

---

## F2 — Auto “source-confirmed” ≠ human GT — **partially mitigated**

| | |
| --- | --- |
| **Seen in** | `spring_petclinic_auto.json` · was `auto_implements_001` (`for` → `Serializable`) |
| **Was** | Bootstrap labels looked green against the same index; keyword/noise implements slipped in. |
| **Now** | `gt_filters.is_noise_edge` rejects keyword endpoints; bootstrap skips them; checked-in auto labels scrubbed. |
| **Still** | Auto ≠ human GT. Measuring Witnis against Witnis can inflate confidence. |
| **Do** | Cite [`spring_petclinic_human.json`](../benchmarks/ground-truth/labels/spring_petclinic_human.json) for credibility claims. |

---

## F3 — Self-calls and tautological Direct hits — **partially mitigated**

| | |
| --- | --- |
| **Seen in** | Auto OwnerController constructor self-`calls` |
| **Was** | Direct pack included “X calls X” / ctor-name collisions. |
| **Now** | Java call extract drops self method/ctor-name calls; enclosing-method pick uses nearest header. |
| **Still** | Cross-method name collisions can remain. Prefer inject / inherit / implements / uses_type for Spring claims. |

---

## F4 — Transitive one-hop name collisions — **partially mitigated**

| | |
| --- | --- |
| **Seen in** | Audit D10 · `analyze_impact` transitive pack |
| **Was** | Call-follow matched short leaves across unrelated symbols. |
| **Now** | Call-follow skips tiny/common leaves; those edges are status `uncertain`. Subclass `uses_type` Indirect stays `derived`. |
| **Do** | Never treat call-follow transitive as Direct. Prefer typed Indirect for merge policy. |

---

## F5 — `change-impact` ≠ full PR

| | |
| --- | --- |
| **Seen in** | Trusted Agent Loop ops |
| **Symptom** | Tip-commit hunk impact understates a multi-commit PR. |
| **Why** | `change-impact` is revision-local; PR range needs merge-base / three-dot. |
| **Do** | Use `witnis pr-gate --base … --head …` (or the composite Action). |

---

## F6 — Index STALE vs live HEAD

| | |
| --- | --- |
| **Seen in** | Envelope limitations after edits without re-index |
| **Symptom** | Evidence looks solid; tree already moved. |
| **Why** | Answers bind to `indexed_revision`, not magically to worktree dirty state. |
| **Do** | Re-index (`witnis index` / `loop-init` / Action reindex). Treat STALE as a hard warning in PR comments. |

---

## F7 — `verified` means automation, not human sign-off

| | |
| --- | --- |
| **Seen in** | contracts · verify honesty flags |
| **Symptom** | Agents say “tests passed / verified” after one gated run. |
| **Why** | `state=verified` + `automation_verified`; skipped steps ≠ reviewed. Failures can mark `contradicted`. |
| **Do** | Require `WITNIS_ALLOW_VERIFY=1` + `--execute`. Quote limitations. Do not equate with code review. |

---

## F8 — Authorize ≠ OS sandbox; Harnis ≠ jail

| | |
| --- | --- |
| **Seen in** | SECURITY · Harnis threat model |
| **Symptom** | Marketing or agents imply container/kernel isolation. |
| **Why** | Verify isolate = worktree/copy + scrubbed env. Harnis = stdio MCP seatbelt on `tools/call` / path reads. URL MCP, hooks bypass, renamed tools can miss the proxy. |
| **Do** | Say **seatbelt**. Read [Harnis THREAT_MODEL](https://github.com/L00PLeGeNd/Harnis/blob/main/THREAT_MODEL.md). Prefer `witnis loop-init` wrap. |

---

## F9 — Java Spring: honest shallow outside P0 edges

| | |
| --- | --- |
| **Seen in** | DEPTH language table · paused Spring deep dive |
| **Symptom** | Missed `@Primary` multi-impl, AOP proxies, generics erasure, classpath-only types. |
| **Why** | Index is Spring-pattern derived, not container-proven. |
| **Do** | Claim implements / field+ctor inject / typed field calls only. PetClinic GT is a **subset** baseline, not “we understand Spring.” |

---

## F10 — Public acceptance score ≠ semantic accuracy

| | |
| --- | --- |
| **Seen in** | README public bench 21/21 |
| **Symptom** | Readers infer 100% correctness on large repos. |
| **Why** | Acceptance suite is smoke / fixture-proven contracts, not corpus leadership. |
| **Do** | Point to this gallery + PetClinic human-v2. Never sell public suite as P/R leadership. |

---

## How to add a case

1. Reproduce on a pinned SHA or fixture.  
2. Give it an `F#` id; one symptom / why / do.  
3. If it is a GT miss, keep or add a label that **expects** the miss (do not delete to greenwash).  
4. Link from [`LABELING_SHEET.md`](../benchmarks/ground-truth/LABELING_SHEET.md) when corpus-related.

## Explicit non-goals of this page

- Not a competitive teardown of SCIP/LSIF/Kythe.  
- Not a promise that every row will be fixed next release.  
- Not exhaustive — only cases we are willing to put our name on.
