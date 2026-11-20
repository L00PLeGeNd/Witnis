# Archived review — FYLGls / AI-assisted (2026-11-18)

Source: WeChat delivery `PetClinic_任务核查反馈_复核版.md`.

**Status:** useful quality review. **Not** Annotator B dual-human credit.  
Reviewer identity in the source file: Claude Code (AI-assisted), non-blind (opened human JSON after forming conclusions).

## What we took

| Item | Action |
| --- | --- |
| Do not set `human_dual` | **Honored** |
| Blind pack leak | Fixed — see `../blind-pack/` |
| Scope undefined | Fixed — `SCOPE.md` + LABELING_SHEET |
| `h_impact_person` missing Pet/VisitController | Fixed in human labels |
| Metrics look like P=1.0 without FP | Docs + report note: expected-item recall; test paths dropped from impact typed Indirect |
| 16 vs 18 / Keep vs Agree wording | Unified |

Full original text preserved below for audit.

---

# PetClinic Annotator B 任务核查反馈（AI 辅助，复核版）

日期：2026-11-18（Asia/Shanghai）
核查对象：GitHub `L00PLeGeNd/Witnis` master `37170fe`；PetClinic pin `500158f732419217507c7656904b8e6aa1bcc0d6`
源码范围：`src/main/java` 30 个 Java 文件（另检查了 `src/test/java` 的注入点）

## 结论与使用方式

**任务本身可做**：18 行都能从固定 pin 的源码判定。  
**但现在的邀请材料还不能支撑“独立 B / dual-human”**：盲审包不成立、判定口径缺范围、`h_impact_person` 的期望集漏项。

本文件是 AI 辅助的源码复核，**不是第二位人工标注者的独立交卷**，不能据此把 `label_mode` 升级为 `human_dual`。我在形成源码结论后才打开 `labels/spring_petclinic_human.json` 对照，因此本轮也不是盲审。

## 18 行 B 列建议（按 `src/main/java` 口径）

| Task id | B | 依据（固定 pin） |
| --- | --- | --- |
| h_sym_owner_controller | Keep | [OwnerController.java:49](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java#L49)：类定义，`owner` 包。 |
| h_sym_owner_repository | Keep | [OwnerRepository.java:36](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/OwnerRepository.java#L36)：接口定义。 |
| h_edge_owner_ctrl_injects_repo | Keep | [OwnerController.java:55](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java#L55)：构造器注入 `OwnerRepository`。 |
| h_edge_pet_ctrl_injects_repo | Keep | [PetController.java:57](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L57)：第一个构造参数。 |
| h_edge_visit_ctrl_injects_repo | Keep | [VisitController.java:47](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/VisitController.java#L47)：构造器注入。 |
| h_edge_vet_ctrl_injects_repo | Keep | [VetController.java:41](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/VetController.java#L41)：构造器注入。 |
| h_edge_formatter_injects_types | Keep | [PetTypeFormatter.java:41](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetTypeFormatter.java#L41)：构造器注入。 |
| h_edge_pet_ctrl_injects_types | Keep | [PetController.java:57](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L57)：第二个构造参数 `PetTypeRepository`。 |
| h_edge_owner_ctrl_uses_owner | Keep | [OwnerController.java:78](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java#L78)：`@Valid Owner owner` 参数；65/95/154 也有签名级使用。 |
| h_edge_visit_ctrl_uses_owner | Keep | [VisitController.java:98](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/VisitController.java#L98)：`@ModelAttribute Owner owner` 参数。 |
| h_edge_formatter_implements | Keep | [PetTypeFormatter.java:37](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetTypeFormatter.java#L37)：`implements Formatter<PetType>`。 |
| h_edge_owner_inherits_person | Keep | [Owner.java:50](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/Owner.java#L50)：`extends Person`。 |
| h_edge_vet_inherits_person | Keep | [Vet.java:45](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/Vet.java#L45)：`extends Person`。 |
| h_edge_named_inherits_base | Keep | [NamedEntity.java:31](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/model/NamedEntity.java#L31)：`extends BaseEntity`。 |
| h_impact_owner_repository | Keep | 生产源码 Direct 注入点为 OwnerController、PetController、VisitController；测试注入点按口径另列。 |
| **h_impact_person** | **Edit** | Direct: Owner、Vet。Indirect 至少应补 **PetController**、**VisitController**（见下方证据）；泛型/测试是否纳入待口径。 |
| h_impact_vet_repository | Keep | 生产源码仅 [VetController.java:41](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/VetController.java#L41) 注入；测试注入点按口径另列。 |
| h_impact_pet_type_repository | Keep | 生产源码为 PetTypeFormatter、PetController；测试注入点按口径另列。 |

## h_impact_person 为什么至少是 Edit

当前 human JSON 的 Indirect 只有 `OwnerController`，但工作表 prompt 写的是“Indirect typed users of Owner/Vet”。以下两个 Controller 的方法签名明确使用 `Owner`：

| 路径 | 签名证据 |
| --- | --- |
| Person → Owner → PetController | [PetController.java:101](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L101) `initCreationForm(Owner owner, ...)`；[108](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L108)、[145](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L145)、[186](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/PetController.java#L186) 同 |
| Person → Owner → VisitController | [VisitController.java:98](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/VisitController.java#L98) `processNewVisitForm(@ModelAttribute Owner owner, ...)` |

当前 master 的 Java 解析器实际也提取到了这三条 `uses_type`；`analyze_impact("Person")` 的 transitive 中出现了 `OwnerController`、`PetController`、`VisitController`。因此 `Keep` 等同于承认一份不完整的影响集。

若口径包含泛型/接口/测试，还应考虑：

| 候选 | 证据 | 当前工具 |
| --- | --- | --- |
| VetController | [VetController.java:48/56/65](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/VetController.java#L48)：`Page<Vet>` / `List<Vet>` | 泛型参数被 `_simple_type` 去掉，未提取 |
| Vets | [Vets.java:36](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/Vets.java#L36)：`List<Vet>` | 同上 |
| OwnerRepository | [OwnerRepository.java:36/45/60](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/owner/OwnerRepository.java#L45)：`Page<Owner>` / `Optional<Owner>` | 泛型 + 接口无方法体，未提取 |
| VetRepository | [VetRepository.java:38/46/56](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/vet/VetRepository.java#L46)：`Collection<Vet>` / `Page<Vet>` | 同上 |
| 测试类 | `OwnerControllerTests`、`VetControllerTests` 等 | 索引会扫描 `src/test`，transitive 中会出现 |

另有 [PetClinicRuntimeHints.java:34-35](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/PetClinicRuntimeHints.java#L34) 的 `Person.class` / `Vet.class` 反射注册；不属于方法签名类型使用，按当前口径不纳入。

## 两个拒绝项

| Item | B | 说明 |
| --- | --- | --- |
| auto `for` → Serializable | **Yes** | 应拒绝。真实边是 [BaseEntity.java:33](https://github.com/spring-projects/spring-petclinic/blob/500158f732419217507c7656904b8e6aa1bcc0d6/src/main/java/org/springframework/samples/petclinic/model/BaseEntity.java#L33) 的 `BaseEntity implements Serializable`；伪边来自第 26 行注释中的 `class for ...` 跨行匹配。当前 Python 解析器仍可复现该伪边。 |
| OwnerController self-calls | **Yes** | 应拒绝。当前解析器已不再产出构造器自调用；但 checked-in 的 auto labels 仍保留旧形式 `OwnerController.OwnerController -[calls]-> ...`，属于文件过期。更广义的噪声（annotation/type 名被当 calls）仍存在。 |

## 需要维护者先解决的问题

### 1. 盲审包不成立（P0）

A 的答案在仓库里至少还有这些入口：

- `benchmarks/ground-truth/adjudication/petclinic-human-v2.md`（A/B 列 + Resolve，与 worksheet 同目录）
- `benchmarks/ground-truth/adjudication/petclinic-annotator-b-worksheet.md` 第 9 行直接指向该文件
- `benchmarks/ground-truth/LABELING_SHEET.md`（A/B 决定摘要）
- `docs/benchmarks/petclinic-human-v2.md`
- Git 历史

而邀请要求给 B 整个 private repo 的 Collaborator 权限。B 即使主观上不看，也无法证明独立性。

**建议**：单独做盲审包（只放 worksheet、pin、判定口径、源码 clone 说明）；B 交卷后再给仓库权限，或直接邮件回填。

### 2. 判定口径缺范围（P0）

需要明确一行：

> Scope: `src/main/java` only; method params/returns; generic type arguments [yes/no]; interfaces without bodies [yes/no]; class literals [no]; test sources are Test link, not Direct/Indirect.

否则 `h_impact_person` 以及 3 个 repository impact 行只能写 Unsure。测试里的注入点很多：`OwnerControllerTests:71`、`PetControllerTests:65/68`、`VisitControllerTests:57`、`ClinicServiceTests:79/82/85`、`VetControllerTests:54`、`MySqlIntegrationTests:56`、`PetClinicIntegrationTests:41`、`PostgresIntegrationTests:61`。

### 3. 评分器不统计 FP（P1，影响 dual-human 的用途）

`src/witnis/core/ground_truth.py` 的 `evaluate_case` 从不递增 `fp`，impact 匹配使用子串（`needle in blob`）。本地实跑：

```text
Person transitive:
  OwnerController -> Owner
  PetController -> Owner  ×4
  VisitController -> Owner
  OwnerControllerTests -> Owner
  VetControllerTests -> Vet

metrics:
  impact_direct    8 TP / 0 FP / 0 FN
  impact_indirect  1 TP / 0 FP / 0 FN   P=1.0 R=1.0
```

工具多报了 2 个 Controller 和 2 个测试类，报告仍是 P=1.0、R=1.0。因此当前 `LABELING_SHEET.md` / `docs/benchmarks/petclinic-human-v2.md` 里的 “Impact Indirect P 1.0” 实质上是“期望项召回 + 子串命中”，不是 precision。文档已有 “subset recall” 的 honesty 说明，但表格仍容易被读成精度。

**建议**：统计 FP、改成精确名称匹配、单独处理 Test link/测试源码；否则把表格明确标成 “expected-item recall, FP not scored”。

### 4. 文档与材料不一致（P2）

- README 与 `docs/benchmarks/petclinic-human-v2.md` 一处写 **16 tasks**，worksheet / human JSON 是 **18**；同文档后又写 “18/18 ok”。
- 协议写 B 填 `Agree / Disagree / Unsure`，邀请和 worksheet 写 `Keep / Drop / Edit / Unsure`。
- 两个拒绝项已是历史噪声：当前 `spring_petclinic_auto.json` 已没有 `for → Serializable` 和构造器自调用；应在拒绝项旁注明“历史 id”，否则 B 找不到对应条目。
- checked-in auto labels 与当前解析器输出不一致（如 `OwnerController.OwnerController -> setAllowedFields` vs `OwnerController.setAllowedFields -> ...`），需要重新生成或明确冻结。

## 最小修改清单

1. 做盲审包：单独仓库/分支，只放 worksheet + pin + 口径；移除指向 `petclinic-human-v2.md` 的引用。
2. 补口径：生产 vs 测试、泛型、接口无方法体、class literal 四项各写 yes/no。
3. 修 `h_impact_person`：至少加入 `PetController`、`VisitController`；再按口径决定 Vet 侧与测试类。
4. 统一数字和词表：18 tasks；`Keep/Drop/Edit/Unsure` 或 `Agree/Disagree/Unsure` 二选一。
5. 修评分器或改说法：统计 FP、精确匹配；或明确标成 expected-item recall。
6. 重新生成或冻结 auto labels，并标注历史拒绝项。

## Annotator identity（保持透明）

- Name / handle：Claude Code（AI 辅助源码复核，不代表第二位人工标注者）
- Date：2026-11-18（Asia/Shanghai）
- Time spent (minutes)：不适用（AI）
- Conflicts you want adjudicated：`h_impact_person` 的泛型/接口/测试范围；盲审材料泄露；评分器 FP 统计
