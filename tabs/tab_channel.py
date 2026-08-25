# -*- coding: utf-8 -*-
"""Tab2: 渠道分析"""
import numpy as np
import streamlit as st
from streamlit import column_config as cc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import RED, GOLD, TEXT, TEXT_SUB, axis_mk, axis_rate, AXIS_TITLE_SIZE, add_ctr_mean_line
from data import compute_ctr


def render(dff):
    """渲染渠道分析 Tab"""
    st.markdown('<div class="section-title">触达分渠道趋势</div>', unsafe_allow_html=True)

    # 按渠道+日期聚合
    ch_data = dff.groupby(["发送日期", "渠道"]).agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
        订单Sales=("订单Sales", "sum"),
        Plan数量=("plan_id", "nunique"),
    ).reset_index()
    ch_data["CTR"] = compute_ctr(ch_data)

    channels = sorted(ch_data["渠道"].unique())

    # 每个渠道一张双轴图
    for ch in channels:
        sub = ch_data[ch_data["渠道"] == ch].sort_values("发送日期")
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
            text=f"<b>{ch}</b>", xref="paper", yref="paper",
            x=0.5, y=1.12, xanchor="center", yanchor="bottom",
            showarrow=False, font=dict(size=14, color=TEXT),
        )
        fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=55, b=0), height=250,
            xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
            yaxis=axis_mk(sub["触达成功"]),
            yaxis2=axis_rate(sub["CTR"]),
            hovermode="x unified")
        fig.update_yaxes(title_text="<b>触达成功</b>", secondary_y=False, title_font=dict(color=RED, size=AXIS_TITLE_SIZE), showgrid=False)
        fig.update_yaxes(title_text="<b>CTR (%)</b>", secondary_y=True, title_font=dict(color=GOLD, size=AXIS_TITLE_SIZE), showgrid=False)
        # CTR 加权均值虚线（该渠道基期总点击/总触达）
        add_ctr_mean_line(fig, sub, color=GOLD)
        st.plotly_chart(fig, use_container_width=True)

    # 渠道贡献度
    st.markdown('<div class="section-title">渠道贡献度</div>', unsafe_allow_html=True)
    ch_sum = dff.groupby("渠道").agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
        订单Sales=("订单Sales", "sum"),
        Plan数量=("plan_id", "nunique"),
    ).reset_index()
    ch_sum["CTR"] = compute_ctr(ch_sum)
    total_reach = ch_sum["触达成功"].sum()
    ch_sum["触达占比"] = (ch_sum["触达成功"] / total_reach * 100).round(1)
    ch_sum["触达成功_fmt"] = ch_sum["触达成功"].map("{:,}".format)
    ch_sum["订单Sales_fmt"] = ch_sum["订单Sales"].map("{:,}".format)
    ch_sum["CTR_fmt"] = ch_sum["CTR"].map("{:.2f}%".format)
    ch_sum["占比_fmt"] = ch_sum["触达占比"].map("{:.1f}%".format)
    ch_display = ch_sum[["渠道", "触达成功_fmt", "CTR_fmt", "订单Sales_fmt", "Plan数量", "占比_fmt"]].rename(
        columns={"触达成功_fmt": "触达成功", "CTR_fmt": "CTR", "订单Sales_fmt": "订单Sales", "占比_fmt": "触达占比"}
    )
    col_cfg = {
        "渠道": cc.TextColumn("渠道", width="small"),
        "触达成功": cc.TextColumn("触达成功", width="small"),
        "CTR": cc.TextColumn("CTR", width="small"),
        "订单Sales": cc.TextColumn("订单Sales", width="small"),
        "Plan数量": cc.TextColumn("Plan数量", width="small"),
        "触达占比": cc.TextColumn("触达占比", width="small"),
    }
    st.dataframe(ch_display, use_container_width=True, hide_index=True, column_config=col_cfg)
