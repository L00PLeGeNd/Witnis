# PetClinic adjudication — human-v2

**Pin:** `500158f732419217507c7656904b8e6aa1bcc0d6`  
**A:** human-v1 (2026-11-18)  
**B (credited):** human-v2-adjudication — maintainer second-pass (**not** a second person)  
**External review (not dual-human):** FYLGls / AI-assisted non-blind 2026-11-18 — [`petclinic-fylgls-ai-review-2026-11-18.md`](petclinic-fylgls-ai-review-2026-11-18.md)  
**Mode:** `human_v2_adjudicated` (still). Scope: [`../SCOPE.md`](../SCOPE.md)

## Task table (post-review resolve)

| Task id | A | Ext. review | Resolve |
| --- | --- | --- | --- |
| Most Direct edge/symbol rows | Keep | Keep | Keep |
| h_impact_person Indirect | OwnerController only | **Edit** — add PetController, VisitController | **Added** both (production uses_type→Owner) |
| Generics / tests / class literals | out | ask scope | **Out** per SCOPE |
| Historical `for`→Serializable | Reject | Yes reject | Reject (historical id) |
| OwnerController self-calls | Reject | Yes reject | Reject (historical id) |

## Upgrade to human_dual

Only when a **human** completes [`../blind-pack/`](../blind-pack/) without prior A answers.
