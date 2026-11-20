# 请你帮忙：PetClinic Annotator B（约 45–90 分钟）

你好，

想请你帮 Witnis 做一轮**独立人工标注（Annotator B）**。不是写功能、也不用会 Witnis，只要能读一点 Java 源码即可。

**重要：** 为了盲审成立，请先**只要**下面这个盲审包，不要先拿整个仓库 Collaborator（有答案泄漏风险）。交卷后再开仓库权限也可以。

盲审包目录（仓库内）：`benchmarks/ground-truth/blind-pack/`  
也可把该目录单独打成 zip 发给你。

---

## 背景（30 秒）

Witnis 在做「改一处代码会影响哪里」的证据，需要人工 ground truth。  
我已经做过 Annotator A。按协议需要**第二个人在不看我答案的前提下**再过一遍同一批题，才能称为 dual-human。

协议：`docs/benchmarks/dual-annotator-protocol.md`  
口径：盲审包内 `SCOPE.md`

---

## 你要做什么

1. 固定版本：`500158f732419217507c7656904b8e6aa1bcc0d6`（见 `CLONE.md`）
2. 只看 **`src/main/java`**（测试代码不算 Direct/Indirect）
3. 只填盲审包里的 `worksheet.md`（Keep / Drop / Edit / Unsure）
4. **不要**打开 `labels/spring_petclinic_human.json` 或任何 A/裁决文档
5. 交卷：填好的 `worksheet.md` 发我，或事后再开 PR

表末请写：真名/网名、是否人类、是否盲审、日期、用时。

**说明：** 仅 AI 辅助、或先看了 A 答案的复核，我们会当质量反馈归档，**不会**标成 `human_dual`。

---

## 判定口径（摘要）

| 项 | 规定 |
| --- | --- |
| 生产源码 | `src/main/java` only |
| 测试 | 不算 Direct/Indirect |
| 方法参数/返回类型 | 算 uses_type |
| 泛型参数 / class literal | 不算 |

谢谢。

—— Witnis 维护者
