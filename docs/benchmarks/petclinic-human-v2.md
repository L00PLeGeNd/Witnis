# PetClinic human-v2 (adjudicated subset)

Pinned: [spring-petclinic](https://github.com/spring-projects/spring-petclinic) @ `500158f732419217507c7656904b8e6aa1bcc0d6`  
Labels: [`spring_petclinic_human.json`](../../benchmarks/ground-truth/labels/spring_petclinic_human.json)  
Scope: [`SCOPE.md`](../../benchmarks/ground-truth/SCOPE.md)  
Adjudication: [`petclinic-human-v2.md`](../../benchmarks/ground-truth/adjudication/petclinic-human-v2.md)  
Blind pack for a future human B: [`blind-pack/`](../../benchmarks/ground-truth/blind-pack/)  
Protocol: [`dual-annotator-protocol.md`](dual-annotator-protocol.md)

**Annotators:** `human-v1` (A) + `human-v2-adjudication` (maintainer second-pass, **not a second person**).  
**label_mode:** `human_v2_adjudicated` — **not** `human_dual`.  
FYLGls 2026-11-18 review was AI-assisted / non-blind — archived only: [`petclinic-fylgls-ai-review-2026-11-18.md`](../../benchmarks/ground-truth/adjudication/petclinic-fylgls-ai-review-2026-11-18.md).

## Measured (local pin, after review fixes)

| Metric | TP | FP | FN | P | R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Symbol locate | 2 | 0 | 0 | 1.0 | 1.0 |
| Call / inject / inherit / uses_type edges | 12 | 0 | 0 | 1.0 | 1.0 |
| Impact **Direct** | 8 | 0 | 0 | 1.0 | 1.0 |
| Impact **Indirect** | 3 | 0 | 0 | 1.0 | 1.0 |

**18/18** tasks ok. Indirect expect = OwnerController + PetController + VisitController (production `uses_type` → Owner).  

**Scoring honesty:** metrics are **expected-item recall** plus Indirect FP for unexpected main-source `uses_type` participants. Not a claim of full-app precision.

## Honesty

- Maintainer second-pass ≠ dual-human.  
- True `human_dual` needs a **human** B on the **blind-pack**, without prior access to A answers.  
