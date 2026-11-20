# Witnis 下一阶段战略规划与研发实验计划书

**版本：V1.1**  
**规划周期：12 周（工程深度 / 实验笔记）**  
**项目定位：Agent Engineering Intelligence**  
**核心方向：Software Change Causality**  
**基线日期：2026-11-04**  
**执行原则：先验证产品方向，再验证技术能力，最后决定是否扩大投入。**

> **对外开源排期与转化优先级**以根目录 [`ROADMAP.md`](../../ROADMAP.md) 与 [`2026-open-source-landing-plan.md`](2026-open-source-landing-plan.md) 为准。  
> 本文保留为**工程审计、缺陷、实验规范与深度笔记**；与增长总纲冲突时（尤其语言投入），**服从 ROADMAP 双轨口径**：Demo/文档主路径 Python + TS/JS；Java 诚实浅层；PetClinic GT 仅作基线可信度，不默认开 Spring 深挖。  
> 未完成可信基线（人工 GT + 可复现 P/R）与转化阶段 1 门槛前，不进入大规模功能扩张或重写。

---

# 一、项目战略定位

## 1.1 项目愿景

Witnis 致力于构建面向 AI 编程 Agent 的工程智能基础设施。

随着 AI 编程工具从代码补全发展为自主执行复杂工程任务，核心问题正在变化：

- Agent 是否真正理解当前项目？
- Agent 是否理解代码之间的实际依赖关系？
- 一处修改会影响哪些模块、接口、业务流程和数据结构？
- Agent 是否遗漏了间接影响？
- 测试通过是否真的意味着变更正确？
- 系统能否从过去的变更和故障中积累工程知识？

现有代码搜索、RAG、静态分析和普通 AI Code Review 只能解决其中一部分问题，并不天然具备完整的项目级工程理解和独立证据验证能力。

Witnis 的目标不是再造代码搜索，也不是给 Agent 加一层提示词。

**Witnis 希望成为 AI Agent 的独立工程认知与变更见证层。**

> Let Agents Build. Let Witnis Understand and Verify.

## 1.2 产品定位

| 层次 | 核心能力 | 解决的问题 |
|---|---|---|
| Engineering Context | 工程上下文理解 | Agent 是否真正理解项目 |
| Change Intelligence | 软件变更影响分析 | 修改会影响什么 |
| Engineering Witness | 独立工程证据与验证 | 变更是否得到证据支持 |

三层是一个完整体系，不是三个独立产品。

## 1.3 长期技术方向

**Software Change Causality（软件变更因果理解）**

示例：修改 Spring Service 方法时，应尝试分析调用方、业务依赖、DI/AOP/事务、数据访问、异步/消息、相关测试、已验证与仍未知项——形成可追溯证据链。

代码静态关系 ≠ 真实运行时因果。须结合静态分析、运行时信息、测试结果与历史数据提高可靠性。

---

# 二、产品设计原则

## 2.1 不做功能堆积

每项核心能力必须回答：

- 解决了什么真实工程问题？
- 相比现有工具有什么实际优势？
- 能否通过可重复实验证明？

无明确价值和验证指标的功能，不进入核心开发计划。

## 2.2 不与现有工具低价值重复

优先利用：Git、Tree-sitter、LSP/编译器、CodeQL/Semgrep、测试框架、OpenTelemetry（远期）、MCP。

Witnis 的价值在于**整合、关联、解释**工程事实，并形成可验证的变更证据。

## 2.3 可信度优先于覆盖率

| 状态 | 含义 |
|---|---|
| OBSERVED | 直接观察到的事实 |
| DERIVED | 根据工程关系推导 |
| VERIFIED | 已通过指定测试或独立检查 |
| UNVERIFIED | 证据不足 |
| CONTRADICTED | 存在相反证据 |
| STALE | 对应代码版本已过期 |

推测不得写成事实；测试通过不得写成「整个系统无问题」。

---

# 三、产品架构规划

## 3.1 总体架构（目标态，非立即全做）

统一工程分析内核，多入口接入，多场景复用：

```
                  AI Coding Agents
                         |
          +--------------+--------------+
          |              |              |
         CLI             MCP            SDK
          |              |              |
          +--------------+--------------+
                         |
                  Witnis Core
                         |
       +-----------------+------------------+
       |                 |                  |
 Engineering        Change              Evidence
 Context            Intelligence       & Verification
       |                 |                  |
       +-----------------+------------------+
                         |
                Engineering Graph
                         |
       +-----------------+------------------+
       |                 |                  |
  Static Analysis   Runtime Evidence    Test Evidence
       |                 |                  |
       +-----------------+------------------+
                         |
                Historical Knowledge
                         |
                 SQLite / Storage
                         |
                  Studio / PR / CI
```

## 3.2 核心模块

### A. Engineering Context

文件/符号/调用/依赖、模块边界、框架语义、测试关联、配置约束。  
**对外主路径：Python + TS/JS（见 ROADMAP）。** Java/Spring 仅作 GT 基线与已有边消费，深挖待评估。

### B. Change Intelligence

Git Diff、修改符号、直接/间接影响、影响路径、风险、测试推荐、预测 vs 实际对照。

### C. Evidence & Verification

证据来源与版本绑定、置信度、验证计划、测试结果、验证范围、反证与未知、历史追溯。

### D. Historical Knowledge（长期）

历史变更、预测/实际影响、测试与（授权后的）环境反馈、错误与遗漏、依赖演化。  
须建立在前三项可靠之后。

---

# 四、现有能力处理策略

不推翻现有架构，渐进升级。

| 现有方向 | 处理 | 要求 |
|---|---|---|
| Python Core | 保留 | 主开发与验证基础 |
| Rust Core | 保留 | 性能瓶颈处使用，不为 Rust 而 Rust |
| SQLite | 保留 | 本地索引与证据历史 |
| CLI | 保留并强化 | 核心工作流可用 |
| MCP | 重点强化 | Agent 获取工程上下文主入口 |
| SDK | 保留 | 接口稳定可扩展 |
| Studio | 暂缓大规模扩展 | 先展示核心证据与影响路径 |
| Evidence Envelope | 深化 | 版本、来源、状态、验证范围 |
| Impact Analysis | 重点升级 | 符号级、框架级 |
| Gated Verify | 保留并加强 | 权限、执行环境、验证边界 |

---

# 五、12 周研发路线

## 第一阶段：现状审计与实验基线（第 1—2 周）

**目标：** 摸清真实能力，建立可复现基线。  
**本阶段不写大规模新功能。**

工作：

1. 审计 Core / CLI / MCP / SDK / Studio  
2. 检查模块接口与数据流  
3. Evidence Envelope 是否可追溯到代码版本  
4. Impact 实际 Precision / Recall  
5. Gated Verify 权限与隔离  
6. 统一实验环境  
7. 确定真实项目测试集  

交付：

- Architecture Audit  
- 当前能力清单  
- 核心缺陷清单  
- Benchmark V1  
- 实验数据记录规范  

验收必须能回答：当前能理解哪些关系？哪些只是语法推断？哪些经过真实验证？最大技术瓶颈是什么？

## 第二阶段：工程语义增强（第 3—5 周）

> V1.1：本阶段**不自动开工**。须先满足 ROADMAP 转化阶段 1 + GT 基线；若重开，再选语言突破口（默认不再预设 Java）。

原草案突破口曾为：**Java / Spring Boot**（非永久语言限制）——保留条文备查：

优先：类/方法/接口/继承、Bean/DI、接口实现与代理、AOP、事务、Controller–Service–Repository、MyBatis/JPA、异步与消息。

每种关系明确：输入、类型、规则、证据来源、置信度、不支持场景、测试样例。

交付：Java Semantic Analyzer V1、Spring Dependency Model V1、Framework Relationship Benchmark、错误案例集。

## 第三阶段：Change Intelligence（第 6—8 周）

工作流：Diff → 修改符号 → 上下文 → 依赖/影响 → 路径 → 风险 → 测试推荐 → 证据报告。

交付：Change Intelligence V1、Impact Report V1、路径可视化、CLI/MCP 集成。

## 第四阶段：独立验证与历史反馈（第 9—10 周）

验证计划、测试关联、受控执行、环境与版本记录、预测 vs 实际、错误与遗漏。  
无法独立验证必须标 UNVERIFIED。

交付：Verification Engine V1、Change Evidence Record、Historical Feedback Model V1。

## 第五阶段：真实用户体验与产品验证（第 11—12 周）

入口优先级：MCP → CLI → GitHub PR/CI → Studio → 其他 IDE。  
无重要风险时不打扰开发者。

交付：V1 Beta、演示项目、真实 Benchmark、外部试用反馈、Roadmap V2。

---

# 六、核心实验设计（计划生死线）

> **当前执行状态：实验暂停。** 先完成第一阶段审计与基线设计；实验在基线就绪后按本节规范启动，避免「功能越来越多、核心价值未证明」。

## 实验一：工程影响分析准确性

问题：是否比代码搜索 / 基础静态分析 / Agent 自身判断更准？

对象：3–5 个真实 Java/Spring 开源项目（完整历史、可构建、有测试、典型分层）。

方法：历史 Commit → 人工标注影响集 → 多工具对比。

对照：A Agent+搜索；B Agent+基础静态分析；C Agent+Witnis；（可选 CodeQL/Semgrep）。

指标：Precision / Recall / F1；直接影响；间接影响；路径正确率；误报；耗时；资源。

阶段目标（研发目标，非现状声明）：直接影响 Recall≥90%、Precision≥85%；间接 Recall≥75%；路径正确率≥80%。

## 实验二：Agent 工程任务成功率（产品价值生死线）

30–50 个有明确验收的真实任务；A 原生 / B 普通检索 / C Witnis MCP；同模型同版本同初始代码；多次独立运行。

指标：通过率、正确率、隐藏测试、遗漏、不必要修改、时间、Token、人工介入。

若 C 只增成本不提质量 → 定位需重审；若仅复杂跨模块任务受益 → 收敛场景。

## 实验三：预测影响 vs 实际影响

时间顺序回放；预测阶段不得读未来代码/结果。

## 实验四：历史反馈是否形成壁垒

分阶段引入历史证据，对比有无反馈的指标变化。无改善则不得宣称历史知识库为壁垒。

---

# 七、实验规范与可信度

- 防泄漏：时间顺序、预测不见未来、训练/测试隔离  
- 人工标注：直接/间接/业务/运行时/测试覆盖/行为变化；复杂样本双人标注  
- 公平对照：同模型、任务、代码、环境、相近 Token/超时  
- 全量留存：实验 ID、项目版本、Commit、Agent/模型版本、配置、输入输出、日志、评价、失败案例；报告含分布与置信区间，禁只晒最佳 demo  

详细填写模板（暂停使用，保留备查）：`docs/experiments/EXPERIMENT_REPORT_FILLME.md`

---

# 八、竞争差异化

1. 工程语义深度（复杂框架与跨模块）  
2. 可追溯证据体系（代码/符号/版本/关系/测试/执行/状态）  
3. 预测 → 验证 → 历史反馈闭环  
4. 多入口生态（不绑定单一模型或 Agent）  

---

# 九、风险与调整机制

| 风险 | 应对 |
|---|---|
| 现有工具已够用 | 收缩场景，找真缺口 |
| 静态分析精度不足 | 加强类型/框架/运行时 |
| Agent 不愿用 | MCP 自动上下文，降摩擦 |
| 成本过高 | 增量索引、缓存、按需分析 |
| 历史无收益 | 重评历史模块必要性 |
| 验证环境不可靠 | 隔离、版本绑定、验证声明 |

**暂停扩功能条件：** 影响分析不优于基础工具；MCP 不改善 Agent；误报漏报毁体验；接入成本＞收益；历史反馈无提升。

---

# 十、12 周成功标准（非代码行数/功能数）

| 维度 | 必须成果 |
|---|---|
| 工程理解 | 一批真实 Java/Spring 关系可靠识别 |
| 影响分析 | 真实项目 Precision/Recall |
| Agent 效果 | 严格对照任务实验 |
| 独立验证 | 版本绑定证据 |
| 历史反馈 | 是否改善预测的初步实验 |
| 产品体验 | 外部可用 MCP/CLI |
| 可复现 | 数据、配置、失败案例可复现 |

五份核心成果：Architecture Audit；Engineering Benchmark V1；Agent A/B Report；Change Intelligence V1；Product Roadmap V2。

---

# 十一、最终战略判断

围绕长期问题：

**AI Agent 如何真正理解软件工程项目，并对自己引发的工程变更提供独立、可靠、可验证的证据？**

愿景：**Witnis — The Engineering Intelligence Layer for AI Agents.**

---

# 附录：执行优先级

| 优先级 | 工作 | 是否立即开始 |
|---|---|---|
| P0 | 现有仓库审计 | **是（下一刀）** |
| P0 | Benchmark 与人工标注规范 | 是（随审计） |
| P0 | Agent A/B 实验基线设计 | 设计先于开跑；**开跑暂缓** |
| P0 | 开源转化阶段 1（二进制 / README / MCP 模板 / Demo） | **是（与 ROADMAP 对齐）** |
| P1 | Java/Spring 语义增强 | **暂停评估** — GT 基线后按 ROADMAP 再开 |
| P1 | Change Intelligence | 转化门槛后 |
| P1 | Evidence 与独立验证 | 持续 |
| P2 | 历史反馈模型 | 有足够数据后 |
| P2 | GitHub PR 集成 | 核心能力验证后 |
| P3 | Studio 大规模 UI | 仅 Demo 所需；大改暂缓 |
| P3 | 多语言全面覆盖 | 暂缓 |

## 三个执行决定

1. **可信基线先于吹牛**——PetClinic 人工 GT + P/R；实验一/二开跑仍暂缓。  
2. **转化与深度双轨**——单二进制 / README / MCP 与 GT 收尾并行，不互相替代。  
3. **语言脸面跟 ROADMAP**——Python + TS/JS 主路径；Java 不默认深挖。

---

# 当前状态（相对本计划）

| 项 | 状态 |
|---|---|
| 工程计划书 | V1.1（本文）；增长总纲见 open-source landing |
| 仓库可见性 | 按运营节奏；增长动作见 ROADMAP |
| 用户侧动手实验 | **暂停** |
| 下一工程动作 | GT 收尾 + 转化阶段 1（见 ROADMAP） |
| 大规模重写 / 功能扩张 | **禁止**，直至基线与转化门槛 |

修订记录：V1.0 — 2026-11-04 采纳为工程总纲。V1.1 — 2026-11-18 与万星开源计划双轨对齐。
