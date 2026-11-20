# 填写表（第二位人工标注）

请先读 `00-请先读我.md`、`SCOPE.md`，再按 `CLONE.md` 打开源码。  
只填 **B 列**。填完后把本文件发回。

**固定版本：** `500158f732419217507c7656904b8e6aa1bcc0d6`  
**词汇：** Keep / Drop / Edit / Unsure  

## 任务表

| Task id | 你要核对什么 | B（填写） |
| --- | --- | --- |
| h_sym_owner_controller | 能否定位到类 `OwnerController` | |
| h_sym_owner_repository | 能否定位到接口 `OwnerRepository` | |
| h_edge_owner_ctrl_injects_repo | `OwnerController` 是否注入 `OwnerRepository` | |
| h_edge_pet_ctrl_injects_repo | `PetController` 是否注入 `OwnerRepository` | |
| h_edge_visit_ctrl_injects_repo | `VisitController` 是否注入 `OwnerRepository` | |
| h_edge_vet_ctrl_injects_repo | `VetController` 是否注入 `VetRepository` | |
| h_edge_formatter_injects_types | `PetTypeFormatter` 是否注入 `PetTypeRepository` | |
| h_edge_pet_ctrl_injects_types | `PetController` 是否注入 `PetTypeRepository` | |
| h_edge_owner_ctrl_uses_owner | `OwnerController` 的**方法签名**是否使用类型 `Owner` | |
| h_edge_visit_ctrl_uses_owner | `VisitController` 的**方法签名**是否使用类型 `Owner` | |
| h_edge_formatter_implements | `PetTypeFormatter` 是否 `implements Formatter`（泛型参数可忽略） | |
| h_edge_owner_inherits_person | `Owner` 是否 `extends Person` | |
| h_edge_vet_inherits_person | `Vet` 是否 `extends Person` | |
| h_edge_named_inherits_base | `NamedEntity` 是否 `extends BaseEntity` | |
| h_impact_owner_repository | 生产代码里谁注入了 `OwnerRepository`（写出 Direct 集合） | |
| h_impact_person | Direct：谁继承 `Person`；Indirect：谁在生产代码**方法签名**使用了这些子类 | |
| h_impact_vet_repository | 生产代码里谁注入了 `VetRepository` | |
| h_impact_pet_type_repository | 生产代码里谁注入了 `PetTypeRepository` | |

## 确认拒绝项（填 Yes 或 No）

| 项 | 是否同意拒绝？ |
| --- | --- |
| 伪边：符号名 `for` → `Serializable` | |
| `OwnerController` 构造器自调用一类噪声 | |

## 身份（必填）

- 姓名或网名：
- 我是人类本人填写（填 Yes / No）：
- 填写前没有看过标准答案 / human JSON（填 Yes / No）：
- 我是否就是第一位标注者 / 仓库维护者本人（填 Yes / No）：
- 日期：
- 大约用时（分钟）：
- 想让维护者裁决的分歧（没有写「无」）：
