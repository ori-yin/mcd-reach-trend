# -*- coding: utf-8 -*-
"""Tab1: 趋势"""
import streamlit as st
from streamlit import column_config as cc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import RED, GOLD, TEXT, TEXT_SUB, axis_mk, axis_rate, AXIS_TITLE_SIZE, add_ctr_mean_line, add_mean_line


def render(daily, daily_coupon=None, dau_daily=None):
    """渲染趋势 Tab

    Args:
        daily: 日汇总（触达/点击/Sales/Plan）
        daily_coupon: 按券维度的日汇总（可选）
        dau_daily: DAU 日序列 (DataFrame with 日期/DAU or empty)
    """
    st.markdown('<div class="section-title">趋势概览</div>', unsafe_allow_html=True)

    def kpi_delta(col, label, is_ctr=False):
        cur = daily.iloc[-1][col]
        if len(daily) > 1:
            prev = daily.iloc[-2][col]
            delta = cur - prev
            sign = "+" if delta > 0 else ""
            cls = "kpi-change-up" if delta > 0 else "kpi-change-down"
            arrow = "\u25b2" if delta > 0 else "\u25bc"
            if is_ctr:
                delta_str = f"{delta:+.2f} PP"
            else:
                pct = abs((delta / prev * 100) if prev != 0 else 0)
                delta_str = f"{sign}{delta:,.0f} ({arrow}{pct:.1f}%)"
        else:
            delta_str = "-"
            cls = ""
        if is_ctr:
            val_str = f"{cur:.2f}%"
        else:
            val_str = f"{cur:,.0f}"
        sub = '<span style="font-size:11px;color:#999">\u73af\u6bd4\u6628\u65e5</span>'
        return (f"<div class=\"kpi-card\">"
                f"<div class=\"kpi-value\">{val_str}</div>"
                f"<div class=\"kpi-label\">{label}<br>{sub}</div>"
                f'<div class="{cls}">{delta_str}</div></div>')

    def kpi_dau():
        """DAU KPI 卡片（latest + 环比昨日），与上方 kpi_delta 同款样式"""
        if dau_daily is None or dau_daily.empty:
            return ""
        cur_dau = dau_daily["DAU"].iloc[-1]
        if len(dau_daily) > 1:
            prev_dau = dau_daily["DAU"].iloc[-2]
            delta = cur_dau - prev_dau
            sign = "+" if delta > 0 else ""
            arrow = "▲" if delta > 0 else "▼"
            delta_pct = abs(delta / prev_dau * 100) if prev_dau != 0 else 0
            cls = "kpi-change-up" if delta > 0 else "kpi-change-down"
            delta_str = f"{sign}{delta:,.0f} ({arrow}{delta_pct:.1f}%)"
        else:
            delta_str = "-"
            cls = ""
        return (f'<div class="kpi-card">'
                f'<div class="kpi-value">{int(cur_dau):,}</div>'
                f'<div class="kpi-label">DAU<br><span style="font-size:11px;color:#999">环比昨日</span></div>'
                f'<div class="{cls}">{delta_str}</div></div>')

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(kpi_delta("\u89e6\u8fbe\u6210\u529f", "\u89e6\u8fbe\u6210\u529f"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_delta("CTR", "CTR", is_ctr=True), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_delta("\u8ba2\u5355Sales", "\u8ba2\u5355Sales"), unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_delta("Plan\u6570\u91cf", "Plan \u6570\u91cf"), unsafe_allow_html=True)
    with col5:
        dau_html = kpi_dau()
        if dau_html:
            st.markdown(dau_html, unsafe_allow_html=True)

    # DAU 趋势（XLSX 第二个 sheet；样式与下方日趋势对齐）
    st.markdown('<div class="section-title">DAU \u8d8b\u52bf</div>', unsafe_allow_html=True)
    if dau_daily is None or dau_daily.empty:
        st.caption("未检测到 DAU 数据（DAU 通常在 XLSX 第二个 sheet，第一列日期，第二列 DAU）")
    else:
        fig_dau = go.Figure()
        fig_dau.add_trace(go.Scatter(
            x=dau_daily["日期"], y=dau_daily["DAU"],
            name="DAU", mode="lines+markers",
            line=dict(color=GOLD, width=2.5), marker=dict(size=6, color=GOLD),
            hovertemplate="DAU: %{y:,.0f}<extra></extra>",
        ))
        fig_dau.update_layout(
            paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font=dict(color=TEXT),
            margin=dict(l=0, r=0, t=10, b=0), height=300,
            xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
            yaxis=axis_mk(dau_daily["DAU"]),
            showlegend=False, hovermode="x unified",
        )
        fig_dau.update_yaxes(title_text="<b>DAU</b>", title_font=dict(color=GOLD, size=AXIS_TITLE_SIZE), showgrid=False)
        # DAU 算术均值虚线（基期日均）
        add_mean_line(fig_dau, dau_daily["DAU"], color=GOLD, label_prefix="\u5747\u503c DAU", fmt="{:,.0f}")
        st.plotly_chart(fig_dau, use_container_width=True)

    # 双轴图
    st.markdown('<div class="section-title">\u65e5\u8d8b\u52bf</div>', unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=daily["\u53d1\u9001\u65e5\u671f"], y=daily["\u89e6\u8fbe\u6210\u529f"],
               name="\u89e6\u8fbe\u6210\u529f", marker_color=RED, opacity=0.9,
               hovertemplate="\u89e6\u8fbe\u6210\u529f: %{y:,.0f}<extra></extra>"),
        secondary_y=False)
    fig.add_trace(
        go.Scatter(x=daily["\u53d1\u9001\u65e5\u671f"], y=daily["CTR"],
                   name="CTR (%)", mode="lines+markers",
                   line=dict(color=GOLD, width=2.5), marker=dict(size=6),
                   hovertemplate="CTR: %{y:.2f}%<extra></extra>"),
        secondary_y=True)
    fig.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font=dict(color=TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=10, b=0), height=300,
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
        yaxis=axis_mk(daily["\u89e6\u8fbe\u6210\u529f"]),
        yaxis2=axis_rate(daily["CTR"]),
        hovermode="x unified")
    fig.update_yaxes(title_text="<b>\u89e6\u8fbe\u6210\u529f</b>", secondary_y=False, title_font=dict(color=RED, size=AXIS_TITLE_SIZE), showgrid=False)
    fig.update_yaxes(title_text="<b>CTR (%)</b>", secondary_y=True, title_font=dict(color=GOLD, size=AXIS_TITLE_SIZE), showgrid=False)
    # CTR 加权均值虚线（基期总点击/总触达）
    add_ctr_mean_line(fig, daily, color=GOLD)
    st.plotly_chart(fig, use_container_width=True)

    # 每日明细表
    st.markdown('<div class="section-title">\u6bcf\u65e5\u660e\u7ec6</div>', unsafe_allow_html=True)
    display = daily.copy()
    display["\u53d1\u9001\u65e5\u671f"] = display["\u53d1\u9001\u65e5\u671f"].dt.strftime("%Y%m%d")
    for col in ["\u89e6\u8fbe\u6210\u529f", "\u70b9\u51fb\u4eba\u6b21", "\u8ba2\u5355Sales", "Plan\u6570\u91cf"]:
        display[col] = display[col].map("{:,}".format)
    display["CTR"] = display["CTR"].map("{:.2f}%".format)
    col_cfg = {
        "\u53d1\u9001\u65e5\u671f": cc.TextColumn("\u53d1\u9001\u65e5\u671f", width="small"),
        "\u89e6\u8fbe\u6210\u529f": cc.TextColumn("\u89e6\u8fbe\u6210\u529f", width="small"),
        "\u70b9\u51fb\u4eba\u6b21": cc.TextColumn("\u70b9\u51fb\u4eba\u6b21", width="small"),
        "\u8ba2\u5355Sales": cc.TextColumn("\u8ba2\u5355Sales", width="small"),
        "Plan\u6570\u91cf": cc.TextColumn("Plan\u6570\u91cf", width="small"),
        "CTR": cc.TextColumn("CTR", width="small"),
    }
    st.dataframe(display, use_container_width=True, hide_index=True,
                 column_config=col_cfg, height=(len(display) * 37 + 37))
