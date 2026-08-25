# -*- coding: utf-8 -*-
"""Tab3: Owner分析"""
import numpy as np
import streamlit as st
from streamlit import column_config as cc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import RED, GOLD, TEXT, TEXT_SUB, axis_mk, axis_rate, AXIS_TITLE_SIZE, add_ctr_mean_line
from data import compute_ctr


def render(dff):
    """渲染Owner分析 Tab"""

    # ==================== 计划类型饼图 ====================
    st.markdown('<div class="section-title">计划类型占比</div>', unsafe_allow_html=True)
    plan_sum = dff.groupby("计划类型").agg(
        触达成功=("触达成功", "sum"),
    ).reset_index().sort_values("触达成功", ascending=False)

    colors_pie = ["#DA291C", "#FFC72C", "#00A04A", "#888888", "#CC8800", "#6B5B95"]
    fig_pie = go.Figure(go.Pie(
        labels=plan_sum["计划类型"],
        values=plan_sum["触达成功"],
        hole=0.4,
        marker=dict(colors=colors_pie[:len(plan_sum)]),
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="%{label}<br>触达: %{value:,.0f}<br>占比: %{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        paper_bgcolor="#FFFFFF", font=dict(color=TEXT),
        height=300, margin=dict(l=20, r=20, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # ==================== Owner 投放排行 ====================
    st.markdown('<div class="section-title">Owner 投放排行</div>', unsafe_allow_html=True)

    owner_sum = dff.groupby("owner").agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
    ).reset_index()
    owner_sum["CTR"] = compute_ctr(owner_sum)
    owner_sum = owner_sum.sort_values("触达成功", ascending=True)  # ascending for horizontal bar

    n_owners = len(owner_sum)
    fig_owner = go.Figure()
    fig_owner.add_trace(go.Bar(
        y=owner_sum["owner"], x=owner_sum["触达成功"],
        orientation="h", marker_color=RED, opacity=0.85,
        text=owner_sum.apply(lambda r: (f"{r['触达成功']/1_000_000:.2f}M" if r['触达成功'] >= 1_000_000 else (f"{r['触达成功']/1_000:.2f}K" if r['触达成功'] >= 1_000 else f"{r['触达成功']:,.0f}")) + f"  CTR {r['CTR']:.2f}%", axis=1),
        textposition="outside",
        textfont=dict(size=11, color=TEXT_SUB),
        hovertemplate="%{y}<br>触达: %{x:,.0f}<br>CTR: " + owner_sum["CTR"].apply(lambda v: f"{v:.2f}%") + "<extra></extra>",
    ))
    fig_owner.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
        margin=dict(l=0, r=140, t=10, b=0),
        height=max(350, n_owners * 30),
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB, size=11)),
        showlegend=False,
    )
    st.plotly_chart(fig_owner, use_container_width=True)

    # ==================== Owner 趋势下钻 ====================
    st.markdown('<div class="section-title">Owner 趋势下钻</div>', unsafe_allow_html=True)
    _owner_reach = dff.groupby("owner")["触达成功"].sum().sort_values(ascending=False)
    all_owners = _owner_reach.index.tolist()
    sel_owners = st.multiselect("选择 Owner", all_owners, default=[], key="drill_owners", label_visibility="collapsed")

    if sel_owners:
        owner_daily = dff[dff["owner"].isin(sel_owners)].groupby(["发送日期", "owner"]).agg(
            触达成功=("触达成功", "sum"),
            点击人次=("点击人次", "sum"),
        ).reset_index()
        owner_daily["CTR"] = compute_ctr(owner_daily)

        for ow in sel_owners:
            sub = owner_daily[owner_daily["owner"] == ow].sort_values("发送日期")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(x=sub["发送日期"], y=sub["触达成功"],
                       name="触达成功", marker_color=RED, opacity=0.85,
                       hovertemplate="触达: %{y:,.0f}<extra></extra>"),
                secondary_y=False)
            fig.add_trace(
                go.Scatter(x=sub["发送日期"], y=sub["CTR"],
                           name="CTR (%)", mode="lines+markers",
                           line=dict(color=GOLD, width=2.5), marker=dict(size=5),
                           hovertemplate="CTR: %{y:.2f}%<extra></extra>"),
                secondary_y=True)
            fig.add_annotation(
                text=f"<b>{ow}</b>", xref="paper", yref="paper",
                x=0.5, y=1.12, xanchor="center", yanchor="bottom",
                showarrow=False, font=dict(size=14, color=TEXT),
            )
            fig.update_layout(
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                margin=dict(l=0, r=0, t=55, b=0), height=220,
                xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
                yaxis=axis_mk(sub["触达成功"]),
                yaxis2=axis_rate(sub["CTR"]),
                hovermode="x unified")
            fig.update_yaxes(title_text="<b>触达</b>", secondary_y=False, title_font=dict(color=RED, size=AXIS_TITLE_SIZE), showgrid=False)
            fig.update_yaxes(title_text="<b>CTR</b>", secondary_y=True, title_font=dict(color=GOLD, size=AXIS_TITLE_SIZE), showgrid=False)
            # CTR 加权均值虚线（该 Owner 基期总点击/总触达）
            add_ctr_mean_line(fig, sub, color=GOLD)
            st.plotly_chart(fig, use_container_width=True)

