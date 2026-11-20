# Witnis 万星开源完整落地计划

**状态：** 已采纳为**对外增长 / 开源运营总纲**（与 [`ROADMAP.md`](../../ROADMAP.md) 一致）  
**配套：** Witnis + [Harnis](https://github.com/L00PLeGeNd/Harnis) 打包为可信 Agent 闭环  
**周期：** 6–9 个月；四阶段：打磨准备（0–1k⭐）→ 冷启动（1k–3k⭐）→ 生态放大（3k–7k⭐）→ 标杆沉淀（7k–10k⭐+）

> 赛道是 **MCP 编码 Agent 的证据化变更爆炸半径分析**（利基小众高价值），不卷通用 RAG、不卷全语言静态分析。目标不是全民爆款，而是在可信 Agent 圈子成为标杆。

工程深度、审计与实验规范仍见 [`2026-Q4-next-phase-plan.md`](2026-Q4-next-phase-plan.md)。**对外排期与语言投入以本文 + ROADMAP 为准。**

---

## 一、核心定位与不变原则

一句话：**Witnis：Evidence-backed blast-radius analysis for AI coding agents.** 给 AI 编码 Agent 提供带证据、可审计的变更影响面分析，减少幻觉，让改动有据可查。

| | |
| --- | --- |
| 坚守 | 证据信封、可信度状态、gated verify、本地 SQLite、MCP 优先、只读默认安全 |
| 不做 | 向量 RAG、通用代码问答、完整污点分析、替代 LSP/CodeQL、重型 IDE 插件 |
| 搭档 | Harnis（**stdio MCP seatbelt**，非 OS 沙箱）；Witnis 分析取证，Harnis 约束已包装的 MCP/可选编辑器 hooks |

仓库 Topics：`mcp-server`, `ai-coding-agent`, `code-analysis`, `blast-radius`, `llm-agent`, `static-analysis`

---

## 二、阶段 1：打磨准备期（0 → 1000⭐｜4–6 周）

目标：README **10 秒看懂、1 分钟跑通 demo、复制粘贴接入 MCP**。不对外大规模投放。

### 1. 产品 & 工程

1. **跨平台单二进制 Release**（Rust 优先交付）— linux-amd64 / mac-arm64 / windows；Python 保留兜底  
2. **在线 Web Demo**（复用 Studio）— 内置 token-refresh：index → trace → impact → 证据可视化；README 顶部 Try Demo  
3. **MCP 预制模板** — Claude Code / Cline / Continue；基础模式 vs verify 授权模式  
4. **CI / Bench 看板** — 自动跑 benchmark、公开报告页、能力边界与失败 case  
5. **能力收敛** — 优先 Python（深）、TS/JS；Go 可用；**Java 标浅层，不大投入深语义**；envelope v1 冻结  
6. **安全摘要前置** — verify 门禁 ≠ OS 沙箱；Harnis 是 MCP seatbelt；默认只读、路径沙箱、密钥脱敏  
7. **PR evidence gate** — `witnis pr-gate` + GitHub Action（三方 merge-base 语义）作为默认分发面  

**可信轨并行（非营销）：** 完成 PetClinic 人工 GT 子集 + Direct/Indirect P/R，再谈公开「真实项目基线」。

### 2. README & 文档结构

1. Slogan + 对比卡片（grep / RAG / LSP / Witnis）  
2. 15s 流程 GIF  
3. 在线 Demo  
4. 复制即用 MCP 配置  
5. Quick Start（二进制 / pip）  
6. 适用 / 不适用  
7. 与 Harnis 闭环  
8. 架构图、证据信封样例  
9. Bench 看板、Adopters（可空）  
10. 文档索引、FAQ、License  

分层：新手教程 · architecture/contracts/DEPTH/SECURITY/benchmark · FAQ · CLI Cheatsheet · Agent Playbook  

### 3. 仓库基建

Issue 模板；Good First Issue；Discussions；简化 CONTRIBUTING；语义化 Release + CHANGELOG；`witnis-harnis-starter` 样板仓。

### 4. 验收

二进制跨平台可用；Demo 可访问；外部可独立接 MCP；CI/bench 稳定；小范围内测修 blocking bug。

---

## 三、阶段 2：冷启动破圈（1000 → 3000⭐｜约 4 周）

- 提交并维护 MCP 目录：Official Registry、MCP.so、Glama、PulseMCP、Smithery、Awesome-MCP-Servers 等  
- 三篇核心长文 + 共用 token-refresh 素材（掘金 / dev.to / HN Show HN / B 站 / 知乎）  
- 海外：HN、Reddit r/MCP 等；国内：掘金、知乎、B 站、社群 — 错开投放  
- 24h 响应 Issue/Discussions；Adopters；修接入/解析 bug；联动 Harnis  

---

## 四、阶段 3：生态放大（3000 → 7000⭐｜8–12 周）

- 客户端官方示例引用；SDK/扩展点；持续维护 starter  
- Showcase、素材包、短篇实战、沙龙分享  
- 企业向：增量索引、报告导出、契约升级指南、PR impact 辅助  
- Committer、月度同步、公开 Roadmap、稳定 Good First Issue  

---

## 五、阶段 4：标杆沉淀（7000 → 10000⭐+）

有限动态识别；完整 Rust 二进制；可配置校验与证据流水线；公开 bench + Adopters；第三方解析器生态；**不扩成通用代码问答**。

---

## 六、风险清单

| 风险 | 应对 |
| --- | --- |
| 赛道小众，星数上限低 | 抓高质量 Adopter / 集成量，不唯 star |
| MCP 协议变更 | 跟官方 Registry；契约版本隔离 |
| 大厂 IDE 内置影响分析 | 强化证据信封与可验证闭环 |
| 单人维护 | Good First Issue（文档/fixture）；分权 |
| 动态代码预期过高 | README/FAQ/bench 失败 case 透明 |
| Python 依赖劝退 | 单二进制最高优先；Python 作兜底 |

---

## 七、指标看板（周复盘）

**核心：** Star / Fork / Contributor、Issue 响应、PR 周期；MCP 收录与第三方教程；Demo / 二进制下载；Discussions / Showcase  

**次要：** HN/dev.to 阅读、社群转发、分享邀约  

---

## 八、极简时间盒（与根目录 ROADMAP 同步）

- **短期（0–2 月）：** 二进制 + Demo + README + MCP 收录准备 + GT 基线数字  
- **中期（2–5 月）：** CI 集成、增量索引、样板仓、社区与 Adopters  
- **长期（5–9 月+）：** 完整 Rust 二进制、扩展体系、公开 bench、标杆案例  

修订：2026-11-18 采纳；与 Q4 工程笔记双轨并存，冲突时以 ROADMAP / 本文对外排期为准。
