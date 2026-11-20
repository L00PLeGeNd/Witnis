# Witnis 对照实验报告（填写版 + 操作教学）

> **2026-11-04：实验执行暂停。** 战略总纲见 [`../strategy/2026-Q4-next-phase-plan.md`](../strategy/2026-Q4-next-phase-plan.md)。  
> 本文保留为实验重启后的操作手册；当前优先做 Architecture Audit，不必先填本表。

> **你怎么用这份文件（重启实验后）**  
> 1. 代码块是**教学**：照着敲；`【填写】` 是**你的结果**。  
> 2. 建议边做边填。  
> 3. 另存为 `EXPERIMENT_REPORT_你的名字_日期.md` 发出。  
> 4. 铜牌 / 银牌 / 金牌见文末第 9 节。

---

## 0. 报告元信息

| 项         | 内容             |
| --------- | -------------- |
| 填写人       | loop           |
| 填写日期      | 2026/11/4      |
| Witnis 版本 | 1.9.1          |
| 操作系统      | win11          |
| Python 版本 | 3.12.10        |
| 本机配置      | i9 32g rtx4070 |

### 0.1 教学：查出 Witnis 版本

在 Witnis 仓库根目录：

```powershell
# Windows PowerShell
cd C:\Users\你的用户名\Desktop\IT\Witnis   # 改成你的真实路径
python --version
pip install -e .
witnis version
```

```bash
# macOS / Linux
cd ~/path/to/Witnis
python3 --version
pip install -e .
witnis version
```

**期望**：打印类似 `1.9.1`。若提示找不到命令：

```powershell
python -m witnis version
# 或确认 Scripts 在 PATH：pip show witnis
```

你实际输出：  
```text
【填写】粘贴 witnis version 全文
```

---

## 1. 安装与第一次有效分析（必做 · 含教学）

### 1.1 教学：5 分钟内跑通产品故事

目标：不接 Agent 也能先看懂 Witnis 产出什么。

```powershell
cd <Witnis仓库根目录>
pip install -e .

# ① 产品叙事（改 token refresh：上下文 → 影响 → 验证计划）
witnis scene

# ② 更小样例的 look 卡片
witnis demo

# ③ grep vs Witnis 分析完备性（无需大模型）
witnis experiment

# ④ 可选：图形化静态页
witnis demo --studio
# 或对已索引符号：
# witnis index fixtures/auth_refresh
# witnis studio refresh_token --open
```

**`witnis scene` 你该看到什么（对照用）**

```text
Scene: modify token refresh
Task    Modify token refresh so ...
Context (engineering facts)
  index   … files · … symbols
  def     AuthService.refresh_token  service.py:…
  caller  controller.py:…
  caller  filter.py:…
Impact
  edges   …
  tests   test_auth_refresh.py
Verification  state=planned_only
  step    …
```

若没有 `caller` / `tests`，把完整终端输出贴到下面「卡点」。

| 步骤 | 成功？ | 大约耗时 | 卡点 / 报错原文 |
|---|---|---|---|
| `pip install -e .` | 【填写】 | 【填写】 | 【填写】 |
| `witnis scene` | 【填写】 | 【填写】 | 【填写】 |
| `witnis experiment` | 【填写】 | 【填写】 | 【填写】 |
| `witnis demo --studio`（可选） | 【填写】 | 【填写】 | 【填写】 |

**scene 是否让你明白「为什么需要 Witnis」？**  
【填写】明白 / 一半 / 不明白 —— 原因：…

**你希望 scene 还多哪句「人话」？**  
【填写】

### 1.2 教学：对「任意业务仓库」建立索引

把 `<REPO>` 换成你要实验的项目根目录（绝对路径更稳）：

```powershell
# 进入业务仓库
cd <REPO>

# 生成索引（会创建 .witnis/index.sqlite）
witnis index .

# 看一个你认识的符号（Python 例子常用 login / refresh；Java 常用 findUser）
witnis look login

# 只要影响面
witnis impact login

# 相关测试
witnis tests login

# 验证计划（默认不执行）
witnis plan login
witnis verify login
# 真跑测试（需双重授权）：
# $env:WITNIS_ALLOW_VERIFY="1"
# witnis verify login --execute
```

**Windows 环境变量写法：**

```powershell
$env:WITNIS_ALLOW_VERIFY = "1"
witnis verify refresh_token --execute
```

**macOS / Linux：**

```bash
WITNIS_ALLOW_VERIFY=1 witnis verify refresh_token --execute
```

你对业务仓库第一次 `look` 的符号名：【填写】  
粘贴 `witnis look <符号>` 输出（可截断到 30 行）：  
```text
【填写】
```

---

## 2. 实验环境（必须固定）

### 2.1 Agent 宿主与模型

| 项 | A 组（纯 Agent） | B 组（Agent + Witnis） |
|---|---|---|
| 宿主 | 【填写】Claude Code / Codex / Cursor / 其他 | **同 A** |
| 模型 | 【填写】 | **同 A** |
| 温度等 | 【填写】或「默认」 | **同 A** |
| 联网 | 【填写】开/关 | **同 A** |
| 自动跑终端 | 【填写】开/关 | **同 A**（B 只多 Witnis） |

### 2.2 教学：接通 MCP（B 组必做）

#### 步骤 A — 先在业务仓库建好 DB

```powershell
cd <REPO>
witnis index .
# 记下绝对路径，例如：
# C:\Users\Ibiza\Desktop\proj\myapp\.witnis\index.sqlite
```

#### 步骤 B — 配置示例（复制后改路径）

**通用 / 多数 MCP 宿主（含部分 Cursor 配置形态）：**

```json
{
  "mcpServers": {
    "witnis": {
      "command": "witnis",
      "args": ["mcp"],
      "env": {
        "WITNIS_DB": "C:/Users/你/绝对路径/repo/.witnis/index.sqlite"
      }
    }
  }
}
```

注意：JSON 里 Windows 路径建议用 `/` 或 `\\`，不要用未转义的单个 `\`。

若 `witnis` 不在 PATH，改成：

```json
{
  "mcpServers": {
    "witnis": {
      "command": "python",
      "args": ["-m", "witnis", "mcp"],
      "env": {
        "WITNIS_DB": "C:/Users/你/绝对路径/repo/.witnis/index.sqlite"
      }
    }
  }
}
```

仓库内也可参考：

- `examples/mcp.example.json`
- `examples/mcp.claude-code.example.json`
- `examples/mcp.codex.example.json`

#### 步骤 C — 自检 MCP 是否可用

在 Agent 里让它调用（或你本地）：

```powershell
witnis capabilities
```

应能看到 `repo_search` / `trace_symbol` / `analyze_impact` / `run_verification` 一类能力。

| 项 | 你的结果 |
|---|---|
| MCP 已接通 | 【填写】是 / 否 |
| `WITNIS_DB` 绝对路径 | 【填写】 |
| 配置贴在哪个文件 | 【填写】如 Claude 设置 / codex config |
| 自检方式 | 【填写】如「Agent 列出了 witnis 工具」 |

### 2.3 B 组强制提示词（教学：直接粘贴）

```text
你可以使用 Witnis（MCP 工具或等价 CLI）。修改代码前必须先完成：
1) 定位相关符号（search / look）；
2) 查看调用方与影响范围（trace / impact）；
3) 找出相关测试（related tests）。
修改后若环境允许，再走 gated verify；不要把「我读过文件」当成证据。
在最终回复中用简短列表写出：符号位置、关键调用方、相关测试、验证状态。
```

你实际使用的提示词：【填写】（可写「与上面相同」）

---

## 3. 实验仓库（钉死 commit）

### 3.1 教学：如何钉死可复现版本

```powershell
cd <REPO>
git rev-parse HEAD
git status
# 若脏了，实验开始前：
git reset --hard <钉死的SHA>
git clean -fd   # 慎用：会删未跟踪文件；先确认没有要留的本地改动
```

克隆开源示例（任选，仅作参考）：

```powershell
# 例：Flask 某一 tag（你可改成别的）
git clone https://github.com/pallets/flask.git
cd flask
git checkout 2.3.3
git rev-parse HEAD
```

### 3.2 仓库登记

#### 仓库 R1

| 项 | 内容 |
|---|---|
| 显示名 | 【填写】 |
| URL 或本地路径 | 【填写】 |
| **commit SHA** | 【填写】 |
| 主语言 | 【填写】 |
| 规模 | 【填写】 |
| `witnis index` 是否成功 | 【填写】是 / 否；符号数约【填写】 |

#### 仓库 R2（推荐）

| 项 | 内容 |
|---|---|
| 显示名 | 【填写】 |
| 路径/URL | 【填写】 |
| commit SHA | 【填写】 |
| 主语言 | 【填写】 |

#### 仓库 R3（推荐）

| 项 | 内容 |
|---|---|
| 显示名 | 【填写】 |
| 路径/URL | 【填写】 |
| commit SHA | 【填写】 |
| 主语言 | 【填写】 |

---

## 4. 任务设计（含可改写的样例题）

### 4.1 出题硬规则

1. 有客观成功标准  
2. 写明不应误伤的范围  
3. 需要跨文件理解  
4. A/B **题目原文完全一致**  
5. 两组之间必须 `git reset --hard <SHA>`  

### 4.2 教学：样例任务原文（复制到你的仓库后改名）

**样例 P（Python 认证）——可直接用于 `fixtures/auth_refresh` 热身：**

```text
任务：修改 token 刷新逻辑，使 refresh_expired=True 的 refresh token 被拒绝；
登录（login）与未过期 refresh 仍须成功。
请补齐/修正实现与测试，不要无关重构。
成功标准：在仓库内运行
  pytest fixtures/auth_refresh/test_auth_refresh.py -q
全部通过（若你在业务仓，改成该仓对应测试命令）。
```

热身操作（可选，不算进 A/B 也可）：

```powershell
cd <Witnis仓库>
witnis index fixtures/auth_refresh
witnis look refresh_token
witnis scene
pytest fixtures/auth_refresh/test_auth_refresh.py -q
```

**样例 J（Java 风格，需你有对应代码）：**

```text
任务：当 UserService.findUser 的返回行为变更时（例如 id==null 抛异常或返回 Optional.empty），
找出并修复所有调用方与测试，使项目约定测试通过。
禁止改无关模块的格式化与重命名。
```

对应你可先本地摸底：

```powershell
cd <REPO>
witnis look findUser
witnis impact findUser
witnis tests findUser
```

### 4.3 教学：判分时用的 Git 命令

```powershell
git diff --name-only
git diff --stat
# 需要补丁附件时：
git diff > %TEMP%\witnis-t1-a.diff
```

---

## 5. 单次任务执行（A/B 操作手册）

对每个「仓库 × 任务」做两遍。

### 5.1 教学：A 组流程（纯 Agent）

```text
1. git reset --hard <SHA> 且工作区干净
2. 新开 Agent 对话（不要沿用 B 的上下文）
3. 不要配置 / 禁用 Witnis MCP
4. 只粘贴「任务原文」（不要贴 Witnis 强制提示）
5. 开始计时 → Agent 改完或你判定失败 → 停止计时
6. 你来跑测试与判分（不要让模型自评成功）
7. 保存 diff 文件名列表
```

### 5.2 教学：B 组流程（Agent + Witnis）

```text
1. git reset --hard <SHA>
2. witnis index .
3. 确认 MCP 的 WITNIS_DB 指向该仓库
4. 新开对话
5. 粘贴：Witnis 强制提示 + 与 A 完全相同的任务原文
6. 计时；观察 Agent 是否真的调用了 search/look/impact/tests/verify
7. 你来跑测试与判分
8. 可选：
     $env:WITNIS_ALLOW_VERIFY="1"
     witnis verify <符号> --execute
```

**若 Agent 乱调用工具**：在提示中追加一句：

```text
优先使用 Witnis 的 look/impact/related tests；不要一上来就全库读文件。
```

### 5.3 任务卡（复制为 T1、T2、T3…）

#### 任务 T【编号】— 仓库 R【编号】

| 项 | 内容 |
|---|---|
| 标题 | 【填写】 |
| 给 Agent 的完整原文 | 【填写】 |
| 成功标准 | 【填写】 |
| 预期应改文件/符号 | 【填写】 |
| 不应改动范围 | 【填写】 |
| 测试命令（请写出完整可复制命令） | 【填写】 |
| 先做 A 还是先做 B | 【填写】 |

##### T? × A 结果

| 指标 | 填写 |
|---|---|
| 耗时 | 【填写】 |
| Token | 【填写】或「未知」 |
| 成功 0/1 | 【填写】 |
| 正确 0/1 | 【填写】 |
| 遗漏的应改项 | 【填写】 |
| 误伤文件 | 【填写】 |
| 测试结果 | 【填写】 |
| 过程观察（3～8 句） | 【填写】 |

`git diff --name-only`：  
```text
【填写】
```

##### T? × B 结果

| 指标 | 填写 |
|---|---|
| 耗时 | 【填写】 |
| Token | 【填写】或「未知」 |
| 成功 0/1 | 【填写】 |
| 正确 0/1 | 【填写】 |
| 遗漏 | 【填写】 |
| 误伤 | 【填写】 |
| 测试结果 | 【填写】 |
| 是否调用 Witnis | 【填写】是（列工具名）/ 否 |
| verify 状态 | 【填写】blocked / verified / failed / 未使用 |
| 过程观察（3～8 句） | 【填写】 |

`git diff --name-only`：  
```text
【填写】
```

**可选：B 组你自己先跑一遍「人类 + Witnis CLI」对照（帮助你判断 Agent 有没有用对）：**

```powershell
witnis look <符号>
witnis impact <符号>
witnis tests <符号>
witnis plan <符号>
```

把你认为「Agent 应该看到但没看到」的点写这里：【填写】

---

## 6. 汇总表

| 任务 | 仓库 | 组 | 成功 | 正确 | 遗漏数 | 误伤数 | 测试 | Token | 耗时 | Witnis |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | R1 | A | 【】 | 【】 | 【】 | 【】 | 【】 | 【】 | 【】 | — |
| T1 | R1 | B | 【】 | 【】 | 【】 | 【】 | 【】 | 【】 | 【】 | 【】 |
| T2 | | A | | | | | | | | — |
| T2 | | B | | | | | | | | |
| T3 | | A | | | | | | | | — |
| T3 | | B | | | | | | | | |

| 问题 | 结论 |
|---|---|
| B 是否更容易做对？ | 【填写】 |
| B 是否更少漏影响面？ | 【填写】 |
| B 是否更费 Token/时间？ | 【填写】 |
| 最有用的能力 | 【填写】look / impact / verify / scene / 都没用 |

---

## 7. 缺陷与需求（写给我改代码用）

格式建议：`[仓库][任务][A/B] 现象 → 期望`

1. 【填写】  
2. 【填写】  
3. 【填写】  

主观总评：【填写】

**下一刀优先（最多勾 2 个）**  
- [ ] Java/Spring 语义  
- [ ] Python 跨文件影响  
- [ ] scene / Studio 产品化  
- [ ] MCP 接入摩擦  
- [ ] verify 隔离/体验  
- [ ] 真实仓库 Ground Truth  
- [ ] 其他：【填写】

---

## 8. 附件

| 附件 | 有/无 | 路径或说明 |
|---|---|---|
| 对话导出 | 【】 | |
| diff 文件 | 【】 | |
| 测试日志 | 【】 | |
| scene/experiment 输出 | 【】 | |
| Studio 截图 | 【】 | |

---

## 9. 交付档位与回消息模板

| 档位 | 要求 |
|---|---|
| **铜牌** | 第 0～1 节 + 第 7 节（安装与 scene 跑通 + 吐槽） |
| **银牌** | 铜牌 + 同一仓库 ≥2 任务完整 A/B（第 5～6 节） |
| **金牌** | 银牌 + ≥2 仓库或 ≥3 任务 + 缺陷清单较完整 |

发给我时复制：

```text
实验报告已完成，档位：铜牌/银牌/金牌
Witnis 版本：
主仓库 + commit：
Agent + 模型：
报告文件：docs/experiments/EXPERIMENT_REPORT_….md
请按第 7 节优先项继续改。
```

---

## 附录 · 常用命令速查

```powershell
witnis version
witnis scene
witnis demo
witnis demo --studio
witnis experiment
witnis index <REPO>
witnis look <symbol>
witnis impact <symbol>
witnis tests <symbol>
witnis plan <symbol>
witnis verify <symbol>
$env:WITNIS_ALLOW_VERIFY="1"; witnis verify <symbol> --execute
witnis studio <symbol> --open
witnis capabilities
witnis bench --suite ground-truth
```

**诚实原则：** B 组若实际没调用 Witnis，写「否」——我会当接入/提示失败处理，不会假装 Witnis 无效。
