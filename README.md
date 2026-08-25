# CNN 触达分析 — MCD Reach Trend Dashboard

麦当劳中国渠道触达数据可视化工具。上传 CSV，生成多维度触达追踪看板。

**在线地址**: https://ori-yin-mcd-reach-trend.streamlit.app

---

## 功能概览

| Tab | 功能 | 说明 |
|-----|------|------|
| 指标监控 | 健康度卡片 + 分位数分布条 | 6 个核心指标（触达/点击/CTR/触达率/GC转化/Sales）+ 分渠道 CTR 健康状态 |
| 趋势总览 | KPI 环比 + 双轴趋势图 | 触达量柱状 + CTR 折线，每日明细表 |
| 渠道分析 | 每渠道独立双轴图 | 触达量 + CTR 趋势，渠道贡献度表 |
| Owner分析 | 饼图 + 排行 + 趋势下钻 | 计划类型占比、Owner 投放排行、可选 Owner 趋势图 |
| 漏斗分析 | 转化漏斗 + 流失表 | 预计触达 → 触达成功 → 点击 → 下单 |

---

## 核心设计

### 基期 / 现期对比模型

- **现期**：单日选择（默认最新一天）— 卡片显示这天的值
- **基期**：日期范围（默认全量数据）— 用于计算分位数和日均值
- **对比**：现期值 vs 基期日均，分布条显示现期值在基期分位数中的位置

### 健康度状态

| 状态 | 区间 | 颜色 |
|------|------|------|
| 正常 | P25 - P75 | 绿 |
| 预警 | P5-P25 或 P75-P95 | 黄 |
| 异常 | < P5 或 > P95 | 红 |

---

## 数据格式

上传 CSV，支持 UTF-8 / GBK / GB2312 编码。必需字段：

| 字段 | 说明 |
|------|------|
| 发送日期 | 日期 |
| 渠道 | 渠道名称 |
| 计划类型 | 计划分类 |
| plan_id | 计划唯一标识 |
| owner | 负责人 |
| 预计触达 | 发送量 |
| 触达成功 | 实际触达数 |
| 点击人次 | 点击次数 |
| 点击后下单人次 | 下单数 |
| 订单GC | GC 订单数 |
| 订单Sales | 订单金额 |

列名支持模糊匹配（中英文均可）。

### DAU 数据（XLSX 第二个 sheet）

| 格式 | 列结构 | 说明 |
|------|--------|------|
| 3 列（推荐） | 日期 / 渠道 / DAU | 总 DAU 取 `渠道=ALL/all` 行；其他渠道叠加显示在趋势图上 |
| 2 列（旧） | 日期 / DAU | 全部视为总 DAU；趋势图只画一条线 |

> 渠道字典示例：ALL（总）、APP Push、企微1v1、微信小程序订阅消息、短信。

对应 SQL 见 `sql/` 目录：
- `sql/28天plan明细查询.sql` — Sheet 1 明细
- `sql/dau查询.sql` — Sheet 2 DAU（输出 ALL + 各渠道两段 UNION）

---

## 技术栈

- **框架**: Streamlit
- **图表**: Plotly
- **数据**: Pandas + NumPy
- **部署**: Streamlit Cloud（自动从 main 分支部署）

---

## 项目结构

```
mcd-reach-trend/
├── app.py              ← 入口：页面配置 + 侧边栏 + Tab 调度
├── config.py           ← 颜色常量 + CSS 注入
├── data.py             ← CSV 加载 + 列名映射 + 校验
├── components.py       ← 可复用 HTML 组件（KPI卡片+分布条）
├── tabs/
│   ├── tab_health.py   ← 指标监控
│   ├── tab_overview.py ← 趋势总览
│   ├── tab_channel.py  ← 渠道分析
│   ├── tab_drilldown.py← Owner分析
│   └── tab_funnel.py   ← 漏斗分析
├── requirements.txt
├── setup_and_run.bat   ← Windows 一键启动脚本
└── config.toml         ← Streamlit 主题配置
```

---

## 本地运行

### 方式一：一键启动（Windows）

双击 `setup_and_run.bat`，自动完成：

1. 检测 Python 环境
2. 创建 venv 虚拟环境（首次）
3. 安装缺失依赖（自动切换国内镜像源）
4. 启动 Streamlit，浏览器自动打开

### 方式二：手动启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 设计规范

| 元素 | 值 |
|------|------|
| 品牌红 | #DA291C |
| 品牌金 | #FFC72C |
| 健康绿 | #00A04A |
| 预警黄 | #F5A623 |
| 背景 | #FFFFFF |
| 圆角 | 14px |
| 字体 | Inter + PingFang SC |

---

## 图表布局约定

- **图例位置**：全部统一为左上角（`xanchor="left", x=0`，外层顶部 `y=1.02`）
  - 原点：Plotly modebar（放大/缩小/重置）默认在右上角，会遮挡图例 hover 点击
- **子图标题**（tab_channel / tab_drilldown）：使用 `fig.add_annotation` + `yref="paper"` 外移到顶部居中（`y=1.12`）
  - 原因：Plotly `layout.title.y` 强制 [0,1] 区间，无法外移；用 annotation 解决
  - `margin.t` 设为 55 同时容纳 annotation + legend 两层

## 更新日志

- **2026-08-25** — 图例布局统一：5 处右上→左上；`tab_channel.py` / `tab_drilldown.py` 子图标题改用 `add_annotation` 外移，避开与图例的视觉粘连。涉及 4 文件 17+/9- 行
- **2026-08-19** — 监控 Tab 重构：DAU 健康度上提到 CTR 之上，渠道卡片改 grid 修复宽度不一致
- **2026-07-29** — 趋势 / 渠道 Tab 双轴图 + 均值虚线
- **2026-07-22** — 券维度 Tab + DAU 第二个 sheet 解析
- **2026-07-06** — 初版上线
