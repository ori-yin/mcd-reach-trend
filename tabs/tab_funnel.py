# -*- coding: utf-8 -*-
"""Tab4: 漏斗分析"""
import pandas as pd
import streamlit as st
from streamlit import column_config as cc
import plotly.graph_objects as go
from config import RED, GOLD, TEXT
from components import kpi_card


def render(dff):
    """渲染漏斗分析 Tab"""
    top_val   = int(dff["预计触达"].sum())
    reach_val = int(dff["触达成功"].sum())
    click_val = int(dff["点击人次"].sum())
    order_val = int(dff["点击后下单人次"].sum())
    reach_rate = round(reach_val / top_val * 100, 2) if top_val > 0 else 0.0
    ctr_val    = round(click_val / reach_val * 100, 2) if reach_val > 0 else 0.0
    cvr_val    = round(order_val / click_val * 100, 2) if click_val > 0 else 0.0
    total_cvr  = round(order_val / top_val * 100, 2) if top_val > 0 else 0.0

    st.markdown('<div class="section-title">核心转化指标</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("预计触达", f"{top_val:,}"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("触达率", f"{reach_rate:.2f}%"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("触达成功", f"{reach_val:,}"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("CTR", f"{ctr_val:.2f}%"), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_card("点击下单率", f"{cvr_val:.2f}%"), unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="section-title">整体转化漏斗</div>', unsafe_allow_html=True)
    stages_all = ["预计触达", "触达成功", "点击人次", "下单人次"]
    vals_all   = [top_val, reach_val, click_val, order_val]
    base = vals_all[0]
    norm_all = [round(v / base * 100, 2) for v in vals_all]
    text_fmt = []
    for v, p in zip(vals_all, norm_all):
        if v >= 1_000_000:
            vs = f"{v/1_000_000:.1f}M"
        elif v >= 1_000:
            vs = f"{v/1_000:.1f}K"
        else:
            vs = f"{v:,.0f}"
        text_fmt.append(vs)
    fig4 = go.Figure(go.Funnel(
        y=stages_all, x=norm_all, textposition="outside", text=text_fmt,
        marker=dict(color=[RED, GOLD, "#00A04A", "#006400"], line=dict(color="white", width=2)),
        hovertemplate="%{y}<br>绝对值: %{text}<br>上一步: %{percentPrevious:.2f}%<br>总转化: %{percentInitial:.2f}%<extra></extra>",
        customdata=[vals_all],
    ))
    fig4.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=TEXT),
        height=360, margin=dict(l=60, r=40, t=10, b=30),
        showlegend=False, xaxis_tickformat=".0f%%",
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.divider()

    st.markdown('<div class="section-title">各步转化详情</div>', unsafe_allow_html=True)
    funnel_rows = [
        {"阶段": "预计触达", "绝对人数": f"{top_val:,}", "上一步转化": "-", "相对第一步": "100.00%"},
        {"阶段": "触达成功", "绝对人数": f"{reach_val:,}", "上一步转化": f"{reach_rate:.2f}%", "相对第一步": f"{reach_rate:.2f}%"},
        {"阶段": "点击人次", "绝对人数": f"{click_val:,}", "上一步转化": f"{ctr_val:.2f}%", "相对第一步": f"{round(click_val/top_val*100,2):.2f}%"},
        {"阶段": "下单人次", "绝对人数": f"{order_val:,}", "上一步转化": f"{cvr_val:.2f}%", "相对第一步": f"{total_cvr:.2f}%"},
    ]
    funnel_df = pd.DataFrame(funnel_rows)
    drop_rows = [
        {"流失环节": "预计触达 → 触达成功", "流失人数": f"{top_val - reach_val:,}", "流失率": f"{100 - reach_rate:.2f}%"},
        {"流失环节": "触达成功 → 点击人次", "流失人数": f"{reach_val - click_val:,}", "流失率": f"{100 - ctr_val:.2f}%"},
        {"流失环节": "点击人次 → 下单人次", "流失人数": f"{click_val - order_val:,}", "流失率": f"{100 - cvr_val:.2f}%"},
    ]
    drop_df = pd.DataFrame(drop_rows)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("**转化率明细**", unsafe_allow_html=False)
        fc = {"阶段": cc.TextColumn("阶段", width="small"), "绝对人数": cc.TextColumn("绝对人数", width="small"), "上一步转化": cc.TextColumn("上一步转化", width="small"), "相对第一步": cc.TextColumn("相对第一步", width="small")}
        st.dataframe(funnel_df, use_container_width=True, hide_index=True, column_config=fc)
    with t2:
        st.markdown("**各步流失人数**", unsafe_allow_html=False)
        dc = {"流失环节": cc.TextColumn("流失环节", width="medium"), "流失人数": cc.TextColumn("流失人数", width="small"), "流失率": cc.TextColumn("流失率", width="small")}
        st.dataframe(drop_df, use_container_width=True, hide_index=True, column_config=dc)
