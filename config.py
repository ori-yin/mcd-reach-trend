# -*- coding: utf-8 -*-
"""设计规范常量与 CSS 注入"""
import numpy as np
import streamlit as st

# ─── 颜色与样式常量 ───
BG = "#FAFAFA"
CARD = "#FFFFFF"
BORDER = "#E8E8E8"
TEXT = "#1a1a1a"
TEXT_SUB = "#666666"
TEXT_DIM = "#999999"
RED = "#DA291C"
GOLD = "#FFC72C"
GREEN = "#00A04A"
YELLOW = "#F5A623"
SIDEBAR_BG = "#FFFFFF"
SIDEBAR_TEXT = "#1a1a1a"
RADIUS = "8px"

# ─── 坐标轴格式化 helper（满百万→M，满千→K，从0开始） ───
AXIS_TITLE_SIZE = 11


def _add_hline_with_label(fig, y_val, color, label_text, secondary=False):
    """在 figure 上加一条水平虚线 + 右上方标注（两个 mean_line helper 共用）。"""
    fig.add_hline(
        y=y_val,
        line_dash="dash",
        line_color=color,
        line_width=1.5,
        opacity=0.7,
        secondary_y=secondary,
    )
    fig.add_annotation(
        xref="x domain", x=1, xanchor="right",
        yref="y2" if secondary else "y", y=y_val, yanchor="bottom",
        text=label_text, showarrow=False,
        font=dict(size=10, color=color),
    )


def add_ctr_mean_line(fig, df, click_col="点击人次", reach_col="触达成功",
                      color="#888888", label_prefix="均值"):
    """CTR 加权均值虚线（=总点击/总触达×100），绑到 y2。"""
    if df is None or df.empty:
        return
    total_reach = float(df[reach_col].sum())
    if total_reach <= 0:
        return
    weighted_ctr = float(df[click_col].sum()) / total_reach * 100
    _add_hline_with_label(fig, weighted_ctr, color,
                          f"{label_prefix} {weighted_ctr:.2f}%", secondary=True)


def add_mean_line(fig, series, color="#888888", label_prefix="均值",
                  fmt="{:,.0f}", secondary=False):
    """算术均值虚线。默认绑主 y 轴；secondary=True 绑 y2。"""
    if series is None or len(series) == 0:
        return
    mean_val = float(series.mean())
    _add_hline_with_label(fig, mean_val, color,
                          f"{label_prefix} {fmt.format(mean_val)}", secondary=secondary)


def _fmt_mk(v):
    """单值 M/K 格式：满百万→M、满千→K。"""
    # 999500+ 视为 M（避免 999999 → "1000.00K" 这种割裂显示）
    if abs(v) >= 999_500:
        return f"{v/1_000_000:.2f}M"
    elif abs(v) >= 1_000:
        return f"{v/1_000:.2f}K"
    return f"{v:,.0f}"


def _nice_ticks(max_val, target_n=5):
    """在 [0, max_val] 内生成约 target_n 个漂亮刻度。"""
    if max_val <= 0:
        return [0]
    raw_step = max(max_val / target_n, 1)
    magnitude = 10 ** np.floor(np.log10(raw_step))
    for mult in [1, 2, 2.5, 5, 10]:
        step = mult * magnitude
        if step >= raw_step:
            break
    n = int(np.ceil(max_val / step))
    return [i * step for i in range(n + 1)]


def axis_mk(series, target_n=5):
    """生成 y 轴配置 dict（满百万→M、满千→K、从 0 开始）。可直接传入 yaxis=axis_mk(s)。"""
    if hasattr(series, "max"):
        max_val = float(series.max()) if len(series) > 0 else 0.0
    else:
        max_val = float(series)
    ticks = _nice_ticks(max_val, target_n)
    upper = ticks[-1] * 1.05 if ticks[-1] > 0 else 1.0
    return dict(
        tickvals=ticks,
        ticktext=[_fmt_mk(v) for v in ticks],
        range=[0, upper],
        showgrid=False,
        tickfont=dict(color=TEXT_SUB),
    )


def axis_rate(max_val, with_pct=True):
    """生成率值 y 轴配置 dict（百分比、从 0 开始）。"""
    if hasattr(max_val, "max"):
        m = float(max_val.max()) if len(max_val) > 0 else 0.0
    else:
        m = float(max_val)
    upper = (m * 1.2) if m > 0 else 1.0
    cfg = dict(
        range=[0, upper],
        showgrid=False,
        tickfont=dict(color=TEXT_SUB),
    )
    if with_pct:
        cfg["ticksuffix"] = "%"
    return cfg


def inject_css():
    """注入全局 CSS 样式"""
    st.markdown(f"""
<style>
  html, body, .stApp {{
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
    background: {BG} !important; color: {TEXT} !important;
  }}
  .st-emotion-cache-1kyxreq {{ background: transparent !important; border-bottom: 1px solid {BORDER} !important; }}
  [data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER};
    border-top: 3px solid {GOLD};
    min-width: 260px !important; max-width: 260px !important;
  }}
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label {{
    color: {TEXT_SUB} !important; font-weight: 600 !important; font-size: 12px !important;
  }}
  [data-testid="stSidebar"] .stDateInput label {{
    color: {TEXT_SUB} !important; font-weight: 600 !important; font-size: 12px !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background: #FFFFFF !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px !important;
  }}
  [data-testid="stSidebar"] .stDateInput > div > div {{
    background: #FFFFFF !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px !important;
  }}
  [data-testid="stSidebar"] .stRadio label {{
    color: {TEXT} !important;
  }}
  .sidebar-filter-title {{
    font-size: 12px; font-weight: 600; letter-spacing: 0.02em;
    color: {TEXT_SUB};
    margin: 14px 0 4px 0;
  }}
  .block-container {{ padding: 2.5rem 2.5rem 2rem 2.5rem !important; background: {BG} !important; max-width: 100% !important; }}
  .stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid {BORDER}; }}
  .stTabs [data-baseweb="tab"] {{
    color: {TEXT_DIM} !important; font-weight: 500; font-size: 14px; padding: 10px 24px;
    border-radius: 0; border-bottom: 2px solid transparent;
  }}
  .stTabs [data-baseweb="tab"]:hover {{ color: {TEXT} !important; }}
  .stTabs [aria-selected="true"] {{
    color: {TEXT} !important; border-bottom: 2px solid {RED} !important; font-weight: 600;
  }}
  hr {{ border-color: {BORDER} !important; }}
  .section-title {{
    font-size: 14px; font-weight: 600; color: {TEXT};
    margin: 20px 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid {BORDER};
  }}
  .kpi-card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: {RADIUS};
    padding: 18px 20px; text-align: center;
  }}
  .kpi-value {{
    font-size: 24px; font-weight: 700; color: {TEXT};
    letter-spacing: -0.02em; line-height: 1.1;
  }}
  .kpi-label {{
    font-size: 12px; color: {TEXT_SUB}; font-weight: 500;
    letter-spacing: 0.02em; margin-top: 4px;
  }}
  .kpi-change-up {{ color: {GREEN} !important; font-size: 12px; font-weight: 600; }}
  .kpi-change-down {{ color: {RED} !important; font-size: 12px; font-weight: 600; }}
  .health-badge-large {{
    display: inline-block; width: 18px; height: 18px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
  }}
  .health-label {{
    font-size: 12px; color: {TEXT_SUB}; font-weight: 500;
    letter-spacing: 0.02em; margin-top: 2px;
  }}
</style>
""", unsafe_allow_html=True)
