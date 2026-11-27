<div align="center">

# `math-modeling-frontier`

**面向新一代旗舰模型的极简双层数模竞赛工程 Skill（v2.0）**
*Rule #0 First · Substantive Math & Narrative · O(1) Relay Memory · Nature/Science Visuals · Zero-Transcription LaTeX*

[![CI](https://github.com/monesy231/math-modeling-frontier/actions/workflows/ci.yml/badge.svg)](https://github.com/monesy231/math-modeling-frontier/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2B4C7E.svg)](./LICENSE)
[![Core Protocol](https://img.shields.io/badge/SKILL.md-43_Lines-009E73.svg)](./.agents/skills/math-modeling-frontier/SKILL.md)
[![Relay Memory](https://img.shields.io/badge/Relay_Memory-O(1)_%E2%89%A480_Lines-D95F02.svg)](#2-o1-分层接力记忆跨模型切换不失忆不爆上下文)
[![Works With](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Codex%20%7C%20Claude%20Code%20%7C%20Cursor-7570B3.svg)](#五-一键安装与本地自测)

</div>

---

## 为什么做这个 Skill？（给旗舰模型摘掉“辅助轮”）

市面上绝大多数高星数模 Skill，本质是在给上一代弱模型打补丁：动辄几千行保姆式 SOP、硬编码“评价题必用熵权法+TOPSIS”的套路表。把这套紧箍咒套在当代顶级推理模型上，**不仅白白吃掉上下文，还会把模型原生的数学直觉和创新上限反向锁死**。

而直接裸跑顶级模型打 72–99 小时数模竞赛，又必然踩中四个真实痛点：
1. **死磕单题卡死全局**：遇到非凸优化不收敛或病态求解器，反复修到第 8 遍把后面几问拖烂尾；
2. **通篇防御废话或“审计日志化”**：要么在摘要和结果段疯狂自我捅刀，要么把微观校验过程（`LOO-45`、`2×2` 析因、补丁探针）写成流水账，丢掉摘要叙事张力、正文数学推导厚度与文献参数依据；
3. **重工程轻正文 / 180 页代码倾倒**：把全套画图/排版/打包脚本一股脑倾倒入 PDF 附录，却忽视题面本身的核心提问与正规竞赛排版规范；
4. **长程漂移与“手抄幻觉”**：切模型忘上下文、半夜改代码重跑后论文里残留旧数字、默认 Matplotlib 廉价丑图、匿名/查重低级失误。

**`math-modeling-frontier` v2.0 的核心哲学：**
> **以“题目要求、官方规则与问题回答”为最大优先（Rule #0），将 99% 建模创造力还给旗舰模型；把防卡死、防失忆、防编数与“摘要叙事张力 + 数学推导厚度 + 参数文献依据 + 精简附录”全部压进 43 行极简协议与 4 个有完整 E2E 测试与 CI 保障的 Python 脚本。**

---

## 一、 架构全景与大刊级出图实拍

<p align="center">
  <img src="./assets/workflow_pipeline_showcase.png" alt="Dual-Tier Frontier Mathematical Modeling Workflow" width="96%" />
</p>

> 上图直接由内置 [plot_style.py](./.agents/skills/math-modeling-frontier/scripts/plot_style.py) 的 `plot_pipeline_diagram()` 矢量渲染生成——零 AI 生图乱码，可直接作为论文 **Figure 1 整体技术路线图**。

<p align="center">
  <img src="./assets/nature_3panel_showcase.png" alt="Nature/Science 3-Panel Publication Showcase" width="96%" />
</p>

> 上图为 `python plot_style.py --self-test` 一键生成的 *Nature/Science* 双栏（`7.2 in`）三联图实拍：粗体 `a, b, c` 面板标识、纯黑 `#000000` 坐标与轴线、无框图例、95% CI 置信带、灵敏度龙卷风图、零中心自动反色 `RdBu_r` 热力图，支持中英文一键切换。

---

## 二、 七大核心亮点（v2.0 实质学术力 + 工程防呆双均衡）

### 0. 最高优先级原则（Rule #0）：以赛题要求、官方规则与问题本身为最大优先
- **`00_problem/` 绝对压倒一切通用默认**：无论是正文与附录的分开页限、纯黑白排版还是彩色要求、支撑包是否禁止附带原题原始数据，还是某道小问指定的指标口径，**均以 `00_problem/` 实时提取规则为最高准绳**。
- **`Prompt Sub-Question & Requirement Traceability Checklist`**：在 `00_plan.md` 强制建立“题面明示/隐含子问题 → 模型/指标 → 正文小节 → 核验状态”全链路对照表，防止沉迷工程自证而跑偏或漏答核心赛题。

### 1. 旗舰思考 × 主力执行 × 旗舰审查（零负担 `MM Step 1–6` 一行切换 + `Gate R` 写前总审）
- **旗舰 `[F]` 零负载裸跑**：`MM Step 1` 与 `MM Step 4` **不加载任何额外参考文件**，只看 43 行 `SKILL.md`，彻底释放原厂高智商。
- **双支柱 `Gate R` 写前总审**：在动笔写论文前同步审计**数学实质与文献依据**（每问第一性原理推导、分析性质/可识别性、3 级参数溯源）与**统计/代码保真度**（同协议嵌套 CV、单源超参传递、边界反例与同刻不动点重检）。

### 2. O(1) 分层接力记忆：跨模型切换不失忆、不爆上下文
| 温度层 | 文件 | 读写规则 | 为什么永远不膨胀？ |
| :--- | :--- | :--- | :--- |
| **热层 (HOT)** | `handoff.md` | **每次切模型唯一必读文件** | **默认硬上限 ≤ 80 行（支持 `--max-lines`），每次交接直接覆写**，并由 `audit_paper.py --check-handoff` 校验行数、禁贴代码块与指针真实性。 |
| **基准层 (CANONICAL)** | `00_plan.md` | 按需读对应小节 | 存动态提取赛制红线（`--plan` 硬拦截未清除占位符）、**题面问题对照清单**、`Q1→Qn` **数学推导主脊**、**3 级参数/权重溯源表**、统一符号表与门禁状态。 |
| **冷层 (COLD)** | `01_log.md` | **默认绝不加载**（只追加） | 存 EDA 统计细节、**真实文献 DOI/URL 与数据出处**、废弃路线与熔断档案，排错或写文献时按需检索。 |
| **零拷贝指针** | `03_outputs/metrics/` & `figs/` | 仅传路径与一行指标 | 严禁把大表/代码粘进 Markdown 记忆，彻底杜绝上下文腐烂。 |

### 3. 四大实质写作与推导硬校准（告别“高工程分、低学术观感”）
经过 9 轮真题盲审打磨，v2.0 在 [writing.md](./.agents/skills/math-modeling-frontier/references/writing.md)、[audit.md](./.agents/skills/math-modeling-frontier/references/audit.md) 与 [audit_paper.py](./.agents/skills/math-modeling-frontier/scripts/audit_paper.py) 中同步落地四项实质标准（**Stage 2 自动信号 + 5 轴评分表**）：
1. **摘要四拍叙事张力（`ABS-ARC` / `[ABSTRACT_AUDIT_CLUTTER]`）**：禁止把摘要写成审计报告流水账（堆砌 `LOO-expID 45`、`2×2` 析因、Holm 微观参数或 `"assumed function / candidate for field testing"`）；强制采用 **“核心冲突立意 → 统一机理主线+旗舰量化成果 → 紧凑稳健性包络 → 明确可落地决策”** 四拍结构。
2. **正文数学推导厚度（`MATH-DEPTH` / `[THIN_MATH_DERIVATION]`）**：禁止“丢一个孤立公式+二十行 CV 刷分表”或零公式建模节；要求每道核心题遵循 **“第一性原理 → 分步推演至编号控制方程/似然/目标 → 解析性质/可识别性/闭式推论 → 求解收敛判据”** 四步弧线，`audit_paper.py` 自动盘点正文各节显示公式数量。
3. **权重与物理参数 3 级文献溯源（`PARAM-GROUND` / `[UNGROUNDED_PARAM_WEIGHT]`）**：严禁无依据的魔数公式（如手拍指数或任意效用权重）；所有权重与物理参数必须明确标定为 **Tier 1 数据识别**（MLE/CV/CRITIC 附 SE/CI）、**Tier 2 物理定律/真实文献引用**（`\cite{...}` 记录于 `01_log.md`）或 **Tier 3 边界情景先验**（附带单纯形/敏感性扫面证明排序不变性）。
4. **精简策划型 PDF 附录（`APP-LEAN` / `[APPENDIX_BLOAT]` / `[APPENDIX_BOILERPLATE_CODE]`）**：PDF 附录默认精选 **1 页复现清单 + 扩展证明/表 + 核心建模求解模块**（除非 `00_problem/` 明示要求全源码附入论文）；将 `build_report.py`、`plot_style.py`、`package_support.py`、`audit_paper.py` 等工程脚手架与完整可运行工程留在独立 **支撑包 ZIP**（并按赛规剔除官方原题与原始数据）。

### 4. 防卡死双保险 & 同源“零手抄”同步
- **全题 Baseline 先行 + 3-Attempt 熔断**：全题端到端贯通前禁止单问死磕；连续 3 次根因修复失败立即交回 `[F]` 按 `L1 精确解 → L2 机理近似 → L3 解析/MC 区间` 降级。
- **单源配置 & 零手抄同步**：超参调优结果从唯一配置源传遍所有重抽样（禁静默回退默认值）；[sync_metrics.py](./.agents/skills/math-modeling-frontier/scripts/sync_metrics.py) 自动生成 `generated_metrics.tex`（全深度数组 `NaN/Inf` 校验 + 中文键唯一 ASCII 宏）与 Booktabs 三线表，配合 `audit_paper.py` 新鲜度/孤儿表门禁彻底杜绝旧数漂移。

### 5. 大刊科研审美 & 纯黑正式竞赛排版双模态
- **默认正式竞赛纯黑学术排版（`DOCUMENT_PALETTE_MONOCHROME`）**：正文/Word/TeX 默认纯黑 `#000000` 字体与 Booktabs 三线表、纯白 `#FFFFFF` 底色，零装饰色块；交互式 HTML 看板或现代技术报告可选用 `DOCUMENT_PALETTE`（Charcoal-Ink + Oxford Slate-Navy）。
- **图件代码防重叠（`plot_style.py`）**：坐标轴/刻度/面板字母统一纯黑 `#000000`，内置 `plot_with_ci()`、`plot_delta_bars()`、`plot_tornado()`、`plot_diverging_heatmap()`、`plot_pipeline_diagram()`、`group_close_points()`，且 `check_figure_layout()` 自动检测 **图例越界裁剪与标注撞图例**。

### 6. 实战淬炼的自动化红队与真 LaTeX 编译 CI（v2.0 实战增强）
- **`--body-start-page` & `--max-appendix-pages` + 附录代码段豁免**：按正式竞赛规范精准区分封面/目录/正文/附录页码；自动识别附录源码清单页并仅豁免源码页面的 `[PDF_UNRENDERED_LATEX]` 检查（正文与散文公式保持 100% 零漏网扫描，且全本缺字 `\ufffd` 照查不误）。
- **AST 级核验器审计 + 原数据防篡改封条**：用 Python `ast` 遍历核查 `verify.py` 中所有跨行 `zip(...)` 是否显式带 `strict=True` 或使用 `zip_longest`；`--verify-raw` 校验 `00_problem/` 与 `01_data/raw/` SHA-256 不可变封条；`--check-csv --strict-csv` 拦截 BOM、`NaN/Inf`、重复复合键与小数位数漂移；`--check-html` 审计离线看板 JSON 有限性与 JS 语法；`--render-pdf` 逐页光栅化供多模态肉眼终审。
- **全链路 CI（Ubuntu 真编 `pdflatex` + Windows 矩阵）**：[tests/test_e2e_pipeline.py](./tests/test_e2e_pipeline.py) 覆盖 14 组端到端正反用例。

---

## 三、 横向对比

| 维度 | 直接裸跑顶级模型 | 传统重型数模 Skill | `math-modeling-frontier` v2.0 |
| :--- | :--- | :--- | :--- |
| **规则优先级与建模自由度** | 0 约束，易漏答核心小问 | 数千行 SOP + 套路表，锁死上限 | **Rule #0 赛题/规则压倒一切 + 43 行极简协议**，旗舰思考期零参考负载 |
| **实质学术深度与叙事张力** | 易写流水账或魔数拍脑袋 | 堆砌套话，缺严格证明 | **4 拍摘要 + 4 步推导弧线 + 3 级参数文献溯源 + 精简策划型附录** |
| **切模型记忆与卡壳容错** | 上下文腐烂、死磕单题 | 粘贴大段日志爆窗口 | **O(1) `handoff.md`（≤80 行校验）+ `MM Step 1–6` + 3-Attempt 熔断** |
| **数据一致性与红队终审** | 手抄旧数、匿名/排版踩雷 | 无测试无 CI，正则易误报 | **零手抄宏/表同步 + 分页限/AST/HTML/PDF 逐页渲染 + 5 轴终审表** |

---

## 四、 仓库结构

```text
.
├── .github/workflows/ci.yml                             # GitHub Actions 跨平台 CI（Ubuntu + Windows, Py3.11/3.12）
├── tests/test_e2e_pipeline.py                           # 全链路自动化测试（14 组正反用例 + 真 LaTeX 编译）
├── assets/                                              # README 实拍效果图（均由内置 plot_style.py 生成）
├── .agents/skills/math-modeling-frontier/
│   ├── SKILL.md                                         # [43行] 主控：Rule #0、双层角色、O(1) 接力、MM Step 1–6、6 条底线
│   ├── references/
│   │   ├── visual.md                                    # [11行] 仅 Step 3 加载：Nature/Science 纯黑坐标与图例防撞规范
│   │   ├── writing.md                                   # [46行] 仅 Step 5 加载：Rule #0、4 拍摘要、推导弧线、3 级参数溯源、精简附录
│   │   └── audit.md                                     # [38行] 仅 Step 6 加载：独立两阶段红队终审 + 5 轴实质评分表
│   └── scripts/
│       ├── init_project.py                              # 一键建目录、Rule #0 问题对照表、参数溯源表、O(1) 记忆与 raw 封条
│       ├── plot_style.py                                # Nature/Science 绘图、纯黑单色/看板双色板、图例防撞与散点聚类原语库
│       ├── sync_metrics.py                              # JSON/CSV → LaTeX 数值宏与 Booktabs 三线表零手抄同步（全深度禁 NaN）
│       └── audit_paper.py                               # v2.0 终审：正文/附录分页限、AST zip 校验、Stage 2 实质信号与 PDF 转 PNG
├── LICENSE
└── README.md
```

---

## 五、 一键安装与本地自测

### 安装到全局（Antigravity / Codex / Claude Code / Cursor）
```powershell
# Windows PowerShell（Antigravity 全局 skills 目录）
Copy-Item -Recurse -Force ".\.agents\skills\math-modeling-frontier" "$env:USERPROFILE\.gemini\config\skills\math-modeling-frontier"
```
```bash
# macOS / Linux（按需替换为 ~/.claude/skills/ 或 ~/.codex/skills/）
cp -r .agents/skills/math-modeling-frontier ~/.gemini/config/skills/math-modeling-frontier
```

### 运行全链路自测（确认本机可用）
```bash
python -m unittest discover -s tests -v
```

---

## 六、 开赛即用的 1 行极简切换口令（告别粘贴长提示词）

把本次比赛最新要求文件和原始数据放进 `00_problem/` 与 `01_data/raw/` 后，每切换一个会话只需粘贴 **1 行**（`handoff.md` 末尾也会自动给出下一棒口令）：

| 步骤 | 推荐模型 | 1 行启动口令（直接复制） | 自动行为与门禁 |
| :--- | :--- | :--- | :--- |
| **Step 0→1** | `[F]` 旗舰 | `使用 math-modeling-frontier 执行 MM Step 1（先初始化并从 00_problem/ 提取最新规则）` | 提规、建问题对照表、EDA、推导主脊与参数溯源 → 停在 **Gate M** |
| **Step 2** | `[W]` 主力 | `使用 math-modeling-frontier 执行 MM Step 2` | 读 `handoff.md` → 清洗、单源配置与全题 Baseline → 校验过 **Gate P1** |
| **Step 3** | `[W]` 主力 | `使用 math-modeling-frontier 执行 MM Step 3` | 加载 `visual.md` → 同协议消融/灵敏度 + `sync_metrics.py` + 大刊终图过 **Gate P2** |
| **Step 4** | `[F]` 旗舰 | `使用 math-modeling-frontier 执行 MM Step 4` | 零参考负载双支柱总审 → 核查题面覆盖、推导厚度、文献溯源与边界 → **Gate R** |
| **Step 5** | `[W]`/`[F]` | `使用 math-modeling-frontier 执行 MM Step 5` *(新开干净窗口)* | 仅加载 `writing.md` → 4 拍摘要 + 推导正文 + 精简附录 + 单源构建 PDF |
| **Step 6** | `[F]` 旗舰 | `使用 math-modeling-frontier 执行 MM Step 6` *(另开只读窗口/换另一旗舰)* | 仅加载 `audit.md` → `audit_paper.py`（逐页转 PNG）→ Stage 1 + 5 轴 Stage 2 |

---

## 许可协议

本项目基于 [MIT License](./LICENSE) 开源。
