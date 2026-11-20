# Archived — FYLGls blind-pack draft (2026-11-19)

**Status:** AI-assisted draft. Annotator identity says NOT a human and not a valid blind pass.
**Action:** Do **not** set `label_mode: human_dual`.
**Content check:** All 18 rows Keep under SCOPE; `h_impact_person` Indirect = OwnerController + PetController + VisitController — already matches current human labels after prior review.

Original filled worksheet follows.

---

# PetClinic Annotator B worksheet (blind) — filled

Fill **only the B column** from the pinned `src/main/java` sources.  
Read `SCOPE.md` and `CLONE.md` in this folder. Do not ask for or open any “human JSON” / A answers until you submit.

**Pin:** `500158f732419217507c7656904b8e6aa1bcc0d6`  
**Vocabulary:** Keep / Drop / Edit / Unsure

When done: return this filled file (email / chat / PR into a blind branch).

## Tasks

| Task id | Prompt (read sources) | B |
| --- | --- | --- |
| h_sym_owner_controller | Locate `OwnerController` | Keep — class `OwnerController` in `owner` package (`OwnerController.java:49`). |
| h_sym_owner_repository | Locate `OwnerRepository` | Keep — interface `OwnerRepository` (`OwnerRepository.java:36`). |
| h_edge_owner_ctrl_injects_repo | OwnerController injects OwnerRepository? | Keep — ctor takes `OwnerRepository owners` (`OwnerController.java:55`). |
| h_edge_pet_ctrl_injects_repo | PetController injects OwnerRepository? | Keep — first ctor param `OwnerRepository owners` (`PetController.java:57`). |
| h_edge_visit_ctrl_injects_repo | VisitController injects OwnerRepository? | Keep — ctor takes `OwnerRepository owners` (`VisitController.java:47`). |
| h_edge_vet_ctrl_injects_repo | VetController injects VetRepository? | Keep — ctor takes `VetRepository vetRepository` (`VetController.java:41`). |
| h_edge_formatter_injects_types | PetTypeFormatter injects PetTypeRepository? | Keep — ctor takes `PetTypeRepository types` (`PetTypeFormatter.java:41`). |
| h_edge_pet_ctrl_injects_types | PetController injects PetTypeRepository? | Keep — second ctor param `PetTypeRepository types` (`PetController.java:57`). |
| h_edge_owner_ctrl_uses_owner | OwnerController uses_type Owner? | Keep — `Owner` in method return/params (`OwnerController.java:65,78,95,154`). |
| h_edge_visit_ctrl_uses_owner | VisitController uses_type Owner? | Keep — `@ModelAttribute Owner owner` param (`VisitController.java:98`). |
| h_edge_formatter_implements | PetTypeFormatter implements Formatter? | Keep — `implements Formatter<PetType>` (`PetTypeFormatter.java:37`); generic arg not counted, `Formatter` is the target. |
| h_edge_owner_inherits_person | Owner extends Person? | Keep — `Owner extends Person` (`Owner.java:50`). |
| h_edge_vet_inherits_person | Vet extends Person? | Keep — `Vet extends Person` (`Vet.java:45`). |
| h_edge_named_inherits_base | NamedEntity extends BaseEntity? | Keep — `NamedEntity extends BaseEntity` (`NamedEntity.java:31`). |
| h_impact_owner_repository | Direct **production** inject sites for OwnerRepository | Keep — Direct set: `OwnerController` (ctor 55), `PetController` (ctor 57), `VisitController` (ctor 47). No other production inject site. |
| h_impact_person | Direct subclasses of Person; Indirect = production typed users of those subclasses (Owner/Vet) via method params/returns | Keep — Direct: `Owner`, `Vet`. Indirect: `OwnerController`, `PetController`, `VisitController`. `PetController` uses `Owner` at 101/108/145/186; `VisitController` at 98. Vet-side has no non-generic signature use in production sources. |
| h_impact_vet_repository | Direct **production** inject sites for VetRepository | Keep — Direct set: `VetController` (ctor 41) only. |
| h_impact_pet_type_repository | Direct **production** inject sites for PetTypeRepository | Keep — Direct set: `PetTypeFormatter` (ctor 41), `PetController` (ctor 57). |

## Reject / do-not-promote (confirm Yes/No)

These are **historical noise ids** (may already be scrubbed from auto labels):

| Item | B agrees reject? |
| --- | --- |
| Historical `auto_implements_001`: symbol `for` → `Serializable` | **Yes** — not a real type edge. The real edge is `BaseEntity implements Serializable` (`BaseEntity.java:33`); the false edge comes from `class for ...` in the line-26 comment. |
| Historical OwnerController constructor self-`calls` | **Yes** — tautological/name collision, not blast-radius signal. Current parser no longer emits ctor self-calls, but the historical auto ids were noise. |

## Annotator B identity

- Name / handle: **Claude Code (AI-assisted draft; NOT a human — cannot claim `human_dual` alone)**
- Date: 2026-11-19
- Time spent (minutes): N/A (AI-assisted; not human annotation time)
- Blind? (did you see A’s expects before finishing): **No** — this draft was produced after an earlier AI review that had already seen A’s expects. It is technically source-based but not a valid blind pass.
- Conflicts you want adjudicated: `h_impact_person` Indirect must include `PetController` and `VisitController` under `SCOPE.md`; if the human label lists only `OwnerController`, adjudicate as **Edit** on the human label. All other 17 rows are straightforward under the fixed scope.

## Notes for the human reviewer

- All 18 prompts are valid under `SCOPE.md`.
- Under the fixed scope (production `src/main/java`; params/returns yes; generics no; class literals no; tests = Test link), the only scope-sensitive row is `h_impact_person`. Vet-side indirect is empty because `Vet` appears only in generic arguments (`Page<Vet>`, `List<Vet>`, `Collection<Vet>`) or class literals, all excluded.
- This file is an AI-assisted draft, not a human blind pass. Per `README.md`, it must **not** set `label_mode: human_dual`. A human should independently re-read the pinned sources, re-fill the B column, and complete the identity section before submission.
