# mcd-reach-trend — Handoff 记忆

> 新会话第一步：读本文件 + `README.md`。本文档只记**当前态 + 关键决策**，每次迭代追加变更日志。

---

## 1. 项目一句话

**麦当劳 CNN 触达数据可视化** Streamlit 单页工具。上传 xlsx/csv，按日/渠道/Owner 维度分析触达、点击、CTR、转化漏斗。

- 在线：https://ori-yin-mcd-reach-trend.streamlit.app
- 本地：`C:\ideon\mcd-reach-trend`（已从 OneDrive 迁出，避文件锁）
- 部署：Streamlit Cloud 自动从 `main` 分支部署

## 2. 决策与约束

| 维度 | 决策 |
|------|------|
| 工具形态 | Streamlit 单页（6 Tab：监控/趋势/渠道/owner/漏斗/券） |
| 数据源 | 1 个 xlsx：Sheet1 = plan 明细（17 列 A-Q）、Sheet2 = DAU（日期/渠道/DAU） |
| 基期/现期 | **现期 = 单日**（默认最新），**基期 = 日期范围**（默认全量），用于 P5/P25/P75/P95 分位 |
| 健康度方向 | **所有 6 指标"越高越好"型**（触达/点击/CTR/成功率/GC转化/Sales） |
| 配色 | 麦当劳红金 `#DA291C` + `#FFC72C` + 健康度 5 档彩虹（见 §6） |
| 命名 | `mcd-reach-trend`（独立项目，与 mcd-content-rank 共用 SQL 数据源） |

**关键约束**：
- CTR 一律 plan 加权：`sum(点击) / sum(触达成功)`，不做记录级平均
- 列名模糊映射（substring），不依赖精确列名，中英文都可
- 列名「触达」一律写「**触达成功**」（避免和「预计触达」混淆）
- 分布条"位置指示点"颜色 = 该值的健康度色，不是当前 band 色
- UI 不放 emoji，沟通全程中文

## 3. 文件落点

```
C:\ideon\mcd-reach-trend\
├── app.py              主入口（上传守卫 + 侧栏筛选 + 6 Tab 路由）
├── config.py           配色常量 + CSS 注入 + 坐标轴 helper（axis_mk/axis_rate）
├── data.py             load_xlsx/load_csv + 列名映射 + read_dau_sheet + compute_ctr
├── components.py       pct_band + dot_span + LABEL_MAP + kpi_card_with_bar
├── tabs/
│   ├── tab_health.py     监控（健康度总览 + DAU 分渠道 + CTR 分渠道 + 异常归因）
│   ├── tab_overview.py   趋势（双轴柱+线 + DAU 叠加）
│   ├── tab_channel.py    渠道（每渠道独立双轴图）
│   ├── tab_drilldown.py  owner（饼图 + 排行 + 趋势下钻）
│   ├── tab_funnel.py     漏斗（预计触达→触达→点击→下单）
│   └── tab_coupon.py     券（是否用券维度）
├── sql/                28天plan明细查询.sql + dau查询.sql
├── static/             favicon.png + loading.gif + mcdonalds.svg
├── README.md           功能说明 + 数据格式 + 图表布局约定
├── Handoff.md          本文件
├── requirements.txt / setup_and_run.bat / config.toml
```

## 4. 复用清单

| 来源 | 复用模式 |
|------|---------|
| `mcd-content-rank` | SQL 数据源（同一个 28 天查询） |
| `mcd-copy-analyzer` | 多编码 fallback + 列名模糊映射 + 项目骨架 |

## 5. 上传守卫（关键）

**没上传数据整个 App 停**（`app.py:19-50`）：上传 expander 默认展开，未上传直接 `st.stop()`，不显示 Tab 框架。`df_loaded` session_state 标记决定后续渲染。

**结构**：
```
if uploaded is None:
    show expander + stop
else:
    try: read + cache to session_state
    except ValueError: show error + stop
```

## 6. 健康度逻辑（监控 Tab 核心）

**5 档彩虹配色**（领导对红黄敏感 — 黄色不再出现在"好"侧）：

| val 区间 | 颜色 | 色号 | 标签 | 透明度 (分布条背景) |
|---------|------|------|------|---------------------|
| `< P5` | 🔴 红 | `#DA291C` | 异常 | 0.25 |
| `P5~P25` | 🟡 黄 | `#F5A623` | 预警 | 0.3 |
| `P25~P75` | 🟢 绿 | `#00A04A` | 正常 | 0.25 |
| `P75~P95` | 🩵 青 | `#06B6D4` | 偏好 | 0.3 |
| `> P95` | 💜 淡紫 | `#A78BFA` | **极好** | 0.4 |

**实现位置**：`components.py` 的 `pct_band` / `dot_span` / `DOT_MAP` / `LABEL_MAP` / `kpi_card_with_bar` 的 `vc` 和 5 段分布条背景。

**关键修复**（顺手）：原 `kpi_card_with_bar` 算了 `lbl = LABEL_MAP[band]` 但**没渲染到 HTML** — 圆点下方文字标签一直缺失。本次加上文字标签（"正常/极好/预警/异常/偏好"），领导不靠颜色识别更稳。

**位置指示点 vc**（分布条上的当前值圆点）：按 current vs P5/P25/P75/P95 同 5 档逻辑染色，跟 band 一致。

## 7. 图表布局约定（2026-08-25 迭代）

| 项 | 约定 | 原因 |
|----|------|------|
| 图例位置 | **统一左上**（`xanchor="left", x=0`，外层 `y=1.02`） | Plotly modebar 默认右上角，hover 时遮挡图例点击 |
| 子图标题（tab_channel / tab_drilldown） | 用 `fig.add_annotation` + `yref="paper"` 外移到顶部居中（`y=1.12`） | Plotly `layout.title.y` 限制 [0,1] 不能 >1，annotation 允许；避开与左上图例的视觉粘连 |
| `margin.t` | 35 → **55** | 容纳 annotation + legend 两层 |

涉及 4 文件共 5 处图例 + 2 处 annotation：`tabs/tab_channel.py` / `tab_coupon.py` / `tab_drilldown.py` / `tab_overview.py`。

## 8. 设计原则

1. **基期/现期对比** — 健康度基于历史分位（5 档），不基于绝对阈值
2. **健康度是"分位"不是"好坏"** — 同色不绝对代表好坏，按指标方向解读
3. **复用模式不照搬** — mcd-content-rank / mcd-copy-analyzer 模式按需改造
4. **领导对红黄敏感** — 红色只在"差"侧出现，黄色只在"预警"出现
5. **彩虹渐进** — 5 档颜色从红→黄→绿→青→紫 = 差→中→好→偏好→极好

## 9. 决策记录（关键）

- **数据源列数**：取前 17 列 A-Q（包含消息标题/内容 JSON 列预留）；如下游扩展可调大
- **DAU Sheet**：≥3 列视为"日期/渠道/DAU"，2 列视为"日期/DAU"自动渠道置 ALL
- **健康度"好侧不用金"**：原计划 P95+ 用品牌金 `#FFC72C`，跟 P5-P25 的黄 `#F5A623` 撞色，改为淡紫 `#A78BFA`
- **图例左上 vs annotation 标题**：先试了 `layout.title.y=1.12` 但 Plotly 强制 [0,1] 报错；改用 `add_annotation` + `yref="paper"`
- **异常归因模块待优化**：当前在监控 Tab 底部，跟上面健康度模块信息有重叠；下一步考虑改成"现期 vs 基期"对比表或搬到独立 Tab（待用户拍板）

## 10. 已知小 BUG（暂不修）

- `tab_health.py:5` 导入了 `cc` 未用（冗余 import）
- DAU 健康度模块遍历 unique 渠道时包含 "ALL"（总 DAU 行），跟"分渠道"语义不符
- 数据 < 3 天的渠道阈值 `p75=999` 兜底让任何非零值都显示绿色（视觉误导）
- `_quantiles` 没空 series 兜底（实际触发概率低）

## 11. 变更日志

> 每次迭代追加一段。最新在上。

- **2026-08-25（迭代 3）** — 健康度 5 档彩虹配色（红/黄/绿/青/紫）+ 顺手修复 lbl 标签渲染 bug + 图例统一左上 + 子图标题改 add_annotation 外移（4 文件 5 处图例 + 2 处 annotation，margin.t 35→55）+ 加 Handoff.md
- **2026-08-19** — 监控 Tab 重构：DAU 健康度上提到 CTR 之上，渠道卡片改 grid 修复宽度不一致
- **2026-07-29** — 趋势 / 渠道 Tab 双轴图 + 均值虚线
- **2026-07-22** — 券维度 Tab + DAU 第二个 sheet 解析
- **2026-07-06** — 初版上线
