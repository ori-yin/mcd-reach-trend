# -*- coding: utf-8 -*-
"""可复用 HTML 组件生成函数"""
from config import RED, GREEN, YELLOW, GOLD, CARD, BORDER, RADIUS, TEXT, TEXT_SUB


def pct_band(val, p5, p25, p75, p95):
    """根据分位数区间返回红/黄/绿状态"""
    if val < p5 or val > p95:
        return "red"
    elif val < p25 or val > p75:
        return "yellow"
    else:
        return "green"


def dot_span(band):
    c = {"green": GREEN, "yellow": YELLOW, "red": RED}[band]
    return f'<span style="color:{c};font-size:20px;margin-right:5px;">&#11044;</span>'


DOT_MAP = {"green": dot_span("green"), "yellow": dot_span("yellow"), "red": dot_span("red")}
LABEL_MAP = {"green": "正常", "yellow": "预警", "red": "异常"}


def kpi_card_with_bar(name, band, val, sub, current, p5, p25, p50, p75, p95, unit=""):
    """KPI 卡片 + 内嵌分位数分布条（合二为一）"""
    c = {"green": GREEN, "yellow": YELLOW, "red": RED}[band]
    lbl = LABEL_MAP[band]
    dot = DOT_MAP[band]
    # 计算分布条
    full_min = p5 * 0.8
    full_max = p95 * 1.2
    full_span = full_max - full_min
    if full_span <= 0:
        pos_pct = 50
        p5_pct, p25_pct, p50_pct, p75_pct, p95_pct = 10, 25, 50, 75, 90
    else:
        pos_pct = (current - full_min) / full_span * 100
        p5_pct = (p5 - full_min) / full_span * 100
        p25_pct = (p25 - full_min) / full_span * 100
        p50_pct = (p50 - full_min) / full_span * 100
        p75_pct = (p75 - full_min) / full_span * 100
        p95_pct = (p95 - full_min) / full_span * 100
        pos_pct = max(0, min(100, pos_pct))
        p5_pct = max(0, min(100, p5_pct))
        p25_pct = max(0, min(100, p25_pct))
        p50_pct = max(0, min(100, p50_pct))
        p75_pct = max(0, min(100, p75_pct))
        p95_pct = max(0, min(100, p95_pct))
    vc = RED if current < p5 or current > p95 else (YELLOW if current < p25 or current >= p75 else GREEN)
    def fmt(v):
        if unit == "%":
            return f"{v:.2f}%"
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.2f}M"
        elif abs(v) >= 1_000:
            return f"{v/1_000:.2f}K"
        return f"{v:,.0f}"
    tooltip = f"P5:{fmt(p5)} | P25:{fmt(p25)} | P50:{fmt(p50)} | P75:{fmt(p75)} | P95:{fmt(p95)}"
    bar_html = (
        f'<div title="{tooltip}" style="position:relative;height:6px;background:#EDEDED;border-radius:3px;overflow:visible;margin-top:12px;">'
        f'<div style="position:absolute;left:0%;width:{p5_pct:.1f}%;top:0;bottom:0;background:rgba(218,41,28,0.25);border-radius:3px 0 0 3px;"></div>'
        f'<div style="position:absolute;left:{p5_pct:.1f}%;width:{p25_pct - p5_pct:.1f}%;top:0;bottom:0;background:rgba(255,199,44,0.3);"></div>'
        f'<div style="position:absolute;left:{p25_pct:.1f}%;width:{p75_pct - p25_pct:.1f}%;top:0;bottom:0;background:rgba(0,160,74,0.25);"></div>'
        f'<div style="position:absolute;left:{p75_pct:.1f}%;width:{p95_pct - p75_pct:.1f}%;top:0;bottom:0;background:rgba(255,199,44,0.3);"></div>'
        f'<div style="position:absolute;left:{p95_pct:.1f}%;width:{100 - p95_pct:.1f}%;top:0;bottom:0;background:rgba(218,41,28,0.25);border-radius:0 3px 3px 0;"></div>'
        f'<div style="position:absolute;left:{pos_pct:.1f}%;top:50%;transform:translate(-50%,-50%);width:10px;height:10px;background:{vc};border-radius:50%;border:1.5px solid {CARD};box-shadow:0 1px 3px rgba(0,0,0,0.2);z-index:2;"></div>'
        f'</div>'
    )
    return (
        f'<div style="flex:1;background:{CARD};border:1px solid {BORDER};border-radius:{RADIUS};padding:16px 18px;display:flex;flex-direction:column;">'
        f'<div style="display:flex;align-items:center;gap:12px;flex:1;">'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:11px;font-weight:600;color:{TEXT_SUB};margin-bottom:6px;letter-spacing:0.1em;text-transform:uppercase;">{name}</div>'
        f'<div style="font-size:28px;font-weight:800;color:{TEXT};letter-spacing:-0.02em;line-height:1;margin-bottom:2px;">{val}</div>'
        f'{sub}</div>'
        f'<div style="text-align:center;min-width:60px;border-left:1px solid {BORDER};padding-left:10px;">'
        f'{dot}'
        f'</div>'
        f'</div>'
        f'{bar_html}'
        f'</div>'
    )


def kpi_card(name, val):
    """简单 KPI 卡片（无分布条）"""
    return (
        f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
        f'<div class="kpi-label">{name}</div></div>'
    )
