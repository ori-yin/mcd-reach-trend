# -*- coding: utf-8 -*-
"""Tab5: Plan分析 · 健康度"""
import numpy as np
import streamlit as st
from streamlit import column_config as cc
import plotly.graph_objects as go
from config import RED, GREEN, TEXT, TEXT_SUB
from components import pct_band, kpi_card_with_bar
from data import compute_ctr

def _fmt_num(v):
    """Format large numbers: >1M shows M, >1K shows K"""
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    elif abs(v) >= 1_000:
        return f"{v/1_000:.2f}K"
    else:
        return f"{v:,.0f}"


def _quantiles(s):
    """返回 (p5, p25, p50, p75, p95) 五分位数元组"""
    return tuple(s.quantile(q) for q in (0.05, 0.25, 0.50, 0.75, 0.95))


def render(df_base, df_current, dau_daily):
    """渲染监控 Tab

    Args:
        df_base: 基期数据（用于计算分位数和日均值）
        df_current: 现期数据（单日，用于展示当前值）
        dau_daily: DAU 日序列（已按渠道筛选），用于 DAU 健康度模块
    """

    st.markdown('<div class="section-title">健康度总览</div>', unsafe_allow_html=True)

    # ==================== 分位数阈值：基于全历史数据 ====================
    all_daily = df_base.groupby("发送日期").agg(
        预计触达=("预计触达", "sum"),
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
        订单GC=("订单GC", "sum"),
        订单Sales=("订单Sales", "sum"),
        Plan数量=("plan_id", "nunique"),
    ).reset_index()
    all_daily["单Plan触达效率"] = (
        all_daily["触达成功"] / all_daily["Plan数量"].replace(0, np.nan)
    ).fillna(0)
    all_daily["触达成功率"] = (
        all_daily["触达成功"] / all_daily["预计触达"].astype(float).replace(0, np.nan) * 100
    ).round(2).fillna(0)
    all_daily["GC转化"] = (
        all_daily["订单GC"] / all_daily["点击人次"].astype(float).replace(0, np.nan) * 100
    ).round(2).fillna(0)
    all_daily["CTR"] = compute_ctr(all_daily)
    ch_ctr_daily = df_base.groupby(["发送日期", "渠道"]).agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
    ).reset_index()
    ch_ctr_daily["CTR"] = compute_ctr(ch_ctr_daily)
    # 五分位数 (p5, p25, p50, p75, p95)
    ctr_p5, ctr_p25, ctr_p50, ctr_p75, ctr_p95 = _quantiles(all_daily["CTR"])
    rr_p5, rr_p25, rr_p50, rr_p75, rr_p95 = _quantiles(all_daily["触达成功率"])
    gc_p5, gc_p25, gc_p50, gc_p75, gc_p95 = _quantiles(all_daily["GC转化"])
    reach_p5, reach_p25, reach_p50, reach_p75, reach_p95 = _quantiles(all_daily["触达成功"])
    click_p5, click_p25, click_p50, click_p75, click_p95 = _quantiles(all_daily["点击人次"])
    sales_p5, sales_p25, sales_p50, sales_p75, sales_p95 = _quantiles(all_daily["订单Sales"])

    ch_ctr_thresholds = {}
    for ch in ch_ctr_daily["渠道"].unique():
        sub = ch_ctr_daily[ch_ctr_daily["渠道"] == ch]
        ctr_series = sub["CTR"]
        if len(ctr_series) >= 3:
            # 加权 CTR = 总点击 / 总触达
            total_click = sub["点击人次"].sum()
            total_reach = sub["触达成功"].sum()
            weighted_ctr = round(total_click / total_reach * 100, 2) if total_reach > 0 else 0
            ch_ctr_thresholds[ch] = {
                "p5":  ctr_series.quantile(0.05),
                "p25": ctr_series.quantile(0.25),
                "p50": ctr_series.quantile(0.50),
                "p75": ctr_series.quantile(0.75),
                "p95": ctr_series.quantile(0.95),
                "mean": weighted_ctr,
            }
        else:
            ch_ctr_thresholds[ch] = {"p5": 0, "p25": 0, "p50": 0, "p75": 999, "p95": 999, "mean": 0}

    # ==================== 现期值：基于 df_current（单日） ====================
    cur_exp_reach = int(df_current["预计触达"].sum()) if "预计触达" in df_current.columns else 0
    cur_reach = int(df_current["触达成功"].sum())
    cur_click = int(df_current["点击人次"].sum())
    cur_gc = int(df_current["订单GC"].sum()) if "订单GC" in df_current.columns else 0
    cur_sales = int(df_current["订单Sales"].sum()) if "订单Sales" in df_current.columns else 0
    # 计算率值
    cur_ctr = round(cur_click / cur_reach * 100, 2) if cur_reach > 0 else 0
    cur_reach_rate = round(cur_reach / cur_exp_reach * 100, 2) if cur_exp_reach > 0 else 0
    cur_gc_rate = round(cur_gc / cur_click * 100, 2) if cur_click > 0 else 0
    # 各指标健康度状态
    reach_band = pct_band(cur_reach, reach_p5, reach_p25, reach_p75, reach_p95)
    click_band = pct_band(cur_click, click_p5, click_p25, click_p75, click_p95)
    ctr_band = pct_band(cur_ctr, ctr_p5, ctr_p25, ctr_p75, ctr_p95)
    rr_band = pct_band(cur_reach_rate, rr_p5, rr_p25, rr_p75, rr_p95)
    gc_band = pct_band(cur_gc_rate, gc_p5, gc_p25, gc_p75, gc_p95)
    sales_band = pct_band(cur_sales, sales_p5, sales_p25, sales_p75, sales_p95)
    # 现期分渠道 CTR
    cur_ch_ctr = df_current.groupby("渠道").agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
    ).reset_index()
    cur_ch_ctr["CTR"] = compute_ctr(cur_ch_ctr)



    # ==================== 均值计算 ====================
    avg_reach = float(all_daily["触达成功"].mean())
    avg_click = float(all_daily["点击人次"].mean())
    avg_ctr = round(float(all_daily["点击人次"].sum()) / float(all_daily["触达成功"].sum()) * 100, 2) if all_daily["触达成功"].sum() > 0 else 0
    avg_rr = round(float(all_daily["触达成功"].sum()) / float(all_daily["预计触达"].sum()) * 100, 2) if all_daily["预计触达"].sum() > 0 else 0
    avg_gc = round(float(all_daily["订单GC"].sum()) / float(all_daily["点击人次"].sum()) * 100, 2) if all_daily["点击人次"].sum() > 0 else 0
    avg_sales = float(all_daily["订单Sales"].mean())

    # ==================== 渲染 6 张卡片 ====================
    def _vs_txt(cur, avg, unit="", is_pct=False):
        delta = cur - avg
        color = "#00A04A" if delta > 0 else "#DA291C"
        sign = "+" if delta > 0 else ("-" if delta < 0 else "")
        if is_pct:
            avg_s = f"{avg:.2f}%"
            delta_s = f"{sign}{abs(delta):.2f}pp"
        else:
            avg_s = _fmt_num(avg)
            delta_s = sign + _fmt_num(abs(delta))
        return f'<div style="font-size:11px;color:{TEXT_SUB};margin-top:4px;opacity:0.7;">vs 基期日均 {avg_s}&nbsp; <span style="color:{color};">{delta_s}</span></div>'

    card1 = kpi_card_with_bar("触达成功", reach_band, _fmt_num(cur_reach), _vs_txt(cur_reach, avg_reach), cur_reach, reach_p5, reach_p25, reach_p50, reach_p75, reach_p95)
    card2 = kpi_card_with_bar("点击人次", click_band, _fmt_num(cur_click), _vs_txt(cur_click, avg_click), cur_click, click_p5, click_p25, click_p50, click_p75, click_p95)
    card3 = kpi_card_with_bar("CTR", ctr_band, f"{cur_ctr:.2f}%", _vs_txt(cur_ctr, avg_ctr, is_pct=True), cur_ctr, ctr_p5, ctr_p25, ctr_p50, ctr_p75, ctr_p95, unit="%")
    card4 = kpi_card_with_bar("触达成功率", rr_band, f"{cur_reach_rate:.2f}%", _vs_txt(cur_reach_rate, avg_rr, is_pct=True), cur_reach_rate, rr_p5, rr_p25, rr_p50, rr_p75, rr_p95, unit="%")
    card5 = kpi_card_with_bar("GC转化", gc_band, f"{cur_gc_rate:.2f}%", _vs_txt(cur_gc_rate, avg_gc, is_pct=True), cur_gc_rate, gc_p5, gc_p25, gc_p50, gc_p75, gc_p95, unit="%")
    card6 = kpi_card_with_bar("订单Sales", sales_band, _fmt_num(cur_sales), _vs_txt(cur_sales, avg_sales), cur_sales, sales_p5, sales_p25, sales_p50, sales_p75, sales_p95)

    # 第一行：触达成功 / 点击人次 / CTR
    row1 = f'<div style="display:flex;gap:12px;margin-bottom:12px;align-items:stretch">{card1}{card2}{card3}</div>'
    st.markdown(row1, unsafe_allow_html=True)
    # 第二行：触达成功率 / GC转化 / 订单Sales
    row2 = f'<div style="display:flex;gap:12px;margin-bottom:16px;align-items:stretch">{card4}{card5}{card6}</div>'
    st.markdown(row2, unsafe_allow_html=True)


    # ═══════════════════════════════════════════════════════════════
    # DAU 健康度模块（位于 CTR 分渠道之上，DAU 是上游流量大盘，先于 CTR 看更顺）
    # ═══════════════════════════════════════════════════════════════
    if not dau_daily.empty:
        # ── DAU 健康度（分渠道；总卡删除：其数字=分渠道之和，冗余） ──
        st.markdown('<div class="section-title">DAU 健康度</div>', unsafe_allow_html=True)
        cur_date_ts = df_current["发送日期"].iloc[0] if not df_current.empty else None
        ch_dau_daily = dau_daily.groupby(["日期", "渠道"])["DAU"].sum().reset_index()
        ch_dau_thresholds = {}
        for ch in ch_dau_daily["渠道"].unique():
            sub = ch_dau_daily[ch_dau_daily["渠道"] == ch]
            dau_series = sub["DAU"]
            if len(dau_series) >= 3:
                n_days_ch = sub["日期"].nunique()
                mean_dau = float(sub["DAU"].sum() / n_days_ch) if n_days_ch > 0 else 0
                ch_dau_thresholds[ch] = {
                    "p5":   dau_series.quantile(0.05),
                    "p25":  dau_series.quantile(0.25),
                    "p50":  dau_series.quantile(0.50),
                    "p75":  dau_series.quantile(0.75),
                    "p95":  dau_series.quantile(0.95),
                    "mean": round(mean_dau, 2),
                }
            else:
                ch_dau_thresholds[ch] = {"p5": 0, "p25": 0, "p50": 0, "p75": 9e15, "p95": 9e15, "mean": 0}

        cur_ch_dau = dau_daily[dau_daily["日期"] == cur_date_ts]
        cur_ch_dau_agg = cur_ch_dau.groupby("渠道")["DAU"].sum().reset_index()
        ch_dau_cards_html = []
        for ch in sorted(ch_dau_daily["渠道"].unique()):
            thr = ch_dau_thresholds[ch]
            ch_row = cur_ch_dau_agg[cur_ch_dau_agg["渠道"] == ch]
            if ch_row.empty:
                continue
            ch_dau_val = float(ch_row["DAU"].iloc[0])
            ch_band = pct_band(ch_dau_val, thr["p5"], thr["p25"], thr["p75"], thr["p95"])
            avg_txt = f'<div style="font-size:11px;color:{TEXT_SUB};margin-top:4px;opacity:0.7;">vs 基期日均 {_fmt_num(thr["mean"])}</div>'
            card_html = kpi_card_with_bar(
                ch, ch_band, _fmt_num(ch_dau_val), avg_txt,
                ch_dau_val, thr["p5"], thr["p25"], thr["p50"], thr["p75"], thr["p95"]
            )
            ch_dau_cards_html.append(card_html)
        # 每行最多 3 个渠道卡片，与 CTR 分渠道同款排版
        for i in range(0, len(ch_dau_cards_html), 3):
            row_cards = ch_dau_cards_html[i:i+3]
            while len(row_cards) < 3:
                row_cards.append('<div></div>')
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:12px;align-items:stretch">'
                + ''.join(row_cards)
                + '</div>',
                unsafe_allow_html=True,
            )

    # ==================== 分渠道 CTR 分布条 ====================
    st.markdown('<div class="section-title">CTR 分渠道健康状态</div>', unsafe_allow_html=True)
    ch_cards_html = []
    for ch in sorted(ch_ctr_daily["渠道"].unique()):
        thr = ch_ctr_thresholds[ch]
        ch_row = cur_ch_ctr[cur_ch_ctr["渠道"] == ch]
        if ch_row.empty:
            continue
        ch_ctr_val = float(ch_row["CTR"].iloc[0])
        ch_band = pct_band(ch_ctr_val, thr["p5"], thr["p25"], thr["p75"], thr["p95"])
        avg_txt = f'<div style="font-size:11px;color:{TEXT_SUB};margin-top:4px;opacity:0.7;">vs 基期日均 {thr["mean"]:.2f}%</div>'
        card_html = kpi_card_with_bar(
            ch, ch_band, f"{ch_ctr_val:.2f}%", avg_txt,
            ch_ctr_val, thr["p5"], thr["p25"], thr["p50"], thr["p75"], thr["p95"], unit="%"
        )
        ch_cards_html.append(card_html)
    # 每行最多3个渠道卡片
    for i in range(0, len(ch_cards_html), 3):
        row_cards = ch_cards_html[i:i+3]
        # 如果不足3个，补空div保持对齐
        while len(row_cards) < 3:
            row_cards.append('<div></div>')
        row_html = (
            f'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:12px;align-items:stretch">'
            + ''.join(row_cards)
            + '</div>'
        )
        st.markdown(row_html, unsafe_allow_html=True)


    # ==================== 异常指标归因 ====================
    # 检测哪些指标异常
    anomalies = []
    metric_info = [
        ("触达成功", reach_band, "触达成功", False),
        ("点击人次", click_band, "点击人次", False),
        ("CTR", ctr_band, None, True),
        ("触达成功率", rr_band, None, True),
        ("GC转化", gc_band, None, True),
        ("订单Sales", sales_band, "订单Sales", False),
    ]
    for name, band, col, is_rate in metric_info:
        if band in ("red", "yellow"):
            anomalies.append((name, band, col, is_rate))

    if anomalies:
        st.markdown('<div class="section-title">异常指标归因</div>', unsafe_allow_html=True)
        # 预算:基期天数 + 率值指标共用的渠道聚合(循环内只算 val,避免重复 groupby)
        n_days = df_base["发送日期"].nunique()
        if any(is_rate for _, _, _, is_rate in anomalies):
            ch_cur = df_current.groupby("渠道").agg(
                触达成功=("触达成功", "sum"),
                点击人次=("点击人次", "sum"),
                预计触达=("预计触达", "sum"),
                订单GC=("订单GC", "sum"),
            ).reset_index()
            ch_base = df_base.groupby("渠道").agg(
                触达成功=("触达成功", "sum"),
                点击人次=("点击人次", "sum"),
                预计触达=("预计触达", "sum"),
                订单GC=("订单GC", "sum"),
            ).reset_index()

        for metric_name, band, col, is_rate in anomalies:
            dot_color = "#DA291C" if band == "red" else "#F5A623"
            st.markdown(f'<span style="font-weight:700;">{metric_name}</span> <span style="color:{dot_color};font-size:16px;">&#11044;</span>', unsafe_allow_html=True)

            if is_rate or col is None:
                # 率值指标：按渠道拆解（ch_cur/ch_base/n_days 已在循环外预算）
                if metric_name == "CTR":
                    ch_cur["val"] = compute_ctr(ch_cur)
                    ch_base["val"] = compute_ctr(ch_base)
                elif metric_name == "触达成功率":
                    ch_cur["val"] = (ch_cur["触达成功"] / ch_cur["预计触达"].replace(0, np.nan) * 100).round(2).fillna(0)
                    ch_base["val"] = (ch_base["触达成功"] / ch_base["预计触达"].replace(0, np.nan) * 100).round(2).fillna(0)
                elif metric_name == "GC转化":
                    ch_cur["val"] = (ch_cur["订单GC"] / ch_cur["点击人次"].replace(0, np.nan) * 100).round(2).fillna(0)
                    ch_base["val"] = (ch_base["订单GC"] / ch_base["点击人次"].replace(0, np.nan) * 100).round(2).fillna(0)
                merged = ch_cur[["渠道", "val"]].merge(ch_base[["渠道", "val"]], on="渠道", suffixes=("_cur", "_base"))
                merged["delta"] = (merged["val_cur"] - merged["val_base"]).round(2)
                merged = merged.sort_values("delta")
                _chart_max = merged["delta"].abs().max() * 1.3 if not merged.empty else 1
                colors = ["#DA291C" if d < 0 else "#00A04A" for d in merged["delta"]]

                fig = go.Figure(go.Bar(
                    y=merged["渠道"], x=merged["delta"], orientation="h",
                    marker_color=colors,
                    text=merged["delta"].apply(lambda v: f"{v:+.2f}pp"),
                    textposition="outside", textfont=dict(size=11),
                    hovertemplate="%{y}<br>现期: %{customdata[0]:.2f}%<br>基期: %{customdata[1]:.2f}%<br>差异: %{x:+.2f}pp<extra></extra>",
                    customdata=merged[["val_cur", "val_base"]].values,
                ))
                fig.update_layout(
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
                    height=max(120, len(merged) * 28), margin=dict(l=100, r=100, t=5, b=5),
                    bargap=0.4,
                    xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#E5E5E5", zerolinewidth=1, visible=True, showticklabels=False, range=[-_chart_max, _chart_max]),
                    yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 绝对值指标：按渠道 + Owner 拆解（n_days 已在循环外预算）
                # 按渠道
                ch_cur_val = df_current.groupby("渠道")[col].sum().reset_index()
                ch_base_avg = (df_base.groupby("渠道")[col].sum() / n_days).reset_index() if n_days > 0 else ch_cur_val.copy()
                ch_base_avg.columns = ["渠道", "base_avg"]
                ch_merged = ch_cur_val.merge(ch_base_avg, on="渠道")
                ch_merged["delta"] = (ch_merged[col] - ch_merged["base_avg"]).round(0)
                ch_merged = ch_merged.sort_values("delta")
                # Owner deltas (pre-compute for shared range)
                ow_cur_val = df_current.groupby("owner")[col].sum().reset_index()
                ow_base_avg = (df_base.groupby("owner")[col].sum() / n_days).reset_index() if n_days > 0 else ow_cur_val.copy()
                ow_base_avg.columns = ["owner", "base_avg"]
                ow_merged = ow_cur_val.merge(ow_base_avg, on="owner")
                ow_merged["delta"] = (ow_merged[col] - ow_merged["base_avg"]).round(0)
                ow_merged = ow_merged.sort_values("delta")
                # Per-chart symmetric range (zeroline centered via equal margins)
                _ch_max = ch_merged["delta"].abs().max() * 1.3 if not ch_merged.empty else 1
                _ow_max = ow_merged["delta"].abs().max() * 1.3 if not ow_merged.empty else 1
                colors = ["#DA291C" if d < 0 else "#00A04A" for d in ch_merged["delta"]]

                fig = go.Figure(go.Bar(
                    y=ch_merged["渠道"], x=ch_merged["delta"], orientation="h",
                    marker_color=colors,
                    text=ch_merged["delta"].apply(lambda v: f"{'+' if v>0 else ''}{v/1000:.1f}K" if abs(v)>=1000 else f"{'+' if v>0 else ''}{v:.0f}"),
                    textposition="outside", textfont=dict(size=11),
                    hovertemplate="%{y}<br>现期: %{customdata[0]:,.0f}<br>基期日均: %{customdata[1]:,.0f}<br>差异: %{x:+,.0f}<extra></extra>",
                    customdata=ch_merged[[col, "base_avg"]].values,
                ))
                fig.update_layout(
                    title=dict(text="按渠道", font=dict(size=12, color=TEXT_SUB), x=0),
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
                    height=max(120, len(ch_merged) * 28), margin=dict(l=100, r=100, t=25, b=5),
                    bargap=0.4,
                    xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#E5E5E5", zerolinewidth=1, visible=True, showticklabels=False, range=[-_ch_max, _ch_max]),
                    yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

                # 按 Owner
                colors = ["#DA291C" if d < 0 else "#00A04A" for d in ow_merged["delta"]]

                fig2 = go.Figure(go.Bar(
                    y=ow_merged["owner"], x=ow_merged["delta"], orientation="h",
                    marker_color=colors,
                    text=ow_merged["delta"].apply(lambda v: f"{'+' if v>0 else ''}{v/1000:.1f}K" if abs(v)>=1000 else f"{'+' if v>0 else ''}{v:.0f}"),
                    textposition="outside", textfont=dict(size=11),
                    hovertemplate="%{y}<br>差异: %{x:+,.0f}<extra></extra>",
                ))
                fig2.update_layout(
                    title=dict(text="按 Owner", font=dict(size=12, color=TEXT_SUB), x=0),
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
                    height=max(120, len(ow_merged) * 28), margin=dict(l=100, r=100, t=25, b=5),
                    bargap=0.4,
                    xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#E5E5E5", zerolinewidth=1, visible=True, showticklabels=False, range=[-_ow_max, _ow_max]),
                    yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True)
