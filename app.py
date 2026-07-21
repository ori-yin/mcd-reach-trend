# -*- coding: utf-8 -*-
"""CNN触达分析 — MCD Reach Trend Dashboard (入口)"""
import base64
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from config import CARD, BORDER, RADIUS, TEXT_SUB, inject_css
from data import load_csv, load_xlsx, compute_ctr, read_dau_sheet
from tabs import tab_overview, tab_channel, tab_drilldown, tab_funnel, tab_health, tab_coupon

st.set_page_config(page_title="CNN触达分析", layout="wide", page_icon="static/favicon.png")
inject_css()

# ===
# upload
# ===
if "df_loaded" not in st.session_state:
    with st.expander("上传数据", expanded=True):
        uploaded = st.file_uploader(
            "上传文件", type=["csv", "xlsx"],
            label_visibility="visible", help="CSV 支持 UTF-8/GBK 编码；XLSX 完整保留 emoji"
        )
        if uploaded:
            is_xlsx = uploaded.name.lower().endswith('.xlsx')
            _gif_b64 = base64.b64encode((Path(__file__).parent / "static" / "loading.gif").read_bytes()).decode()
            _loading = st.empty()
            _loading.markdown(f'<div style="text-align:center;padding:24px 0;"><img src="data:image/gif;base64,{_gif_b64}" width="200" /></div>', unsafe_allow_html=True)
            try:
                _raw = uploaded.read()
                uploaded.seek(0)  # 重置游标供后续读取
                if is_xlsx:
                    df = load_xlsx(uploaded)
                    dau_df = read_dau_sheet(_raw)
                else:
                    df = load_csv(uploaded)
                    dau_df = pd.DataFrame()
                st.session_state["df_loaded"] = True
                st.session_state["df_ref"] = uploaded
                st.session_state["df"] = df
                st.session_state["dau_df"] = dau_df
            except ValueError as e:
                _loading.empty()
                st.error(str(e))
                st.stop()
            _loading.empty()
            st.caption(f'✅ 已加载 {df.shape[0]} 行 | {df["发送日期"].min().strftime("%m/%d")} - {df["发送日期"].max().strftime("%m/%d")}')
            st.rerun()
    st.stop()
else:
    df = st.session_state["df"]
    dau_raw = st.session_state.get("dau_df", pd.DataFrame())

# ═══════════════════════════════════════════════════════════════
# 侧边栏筛选器
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    _svg_b64 = base64.b64encode((Path(__file__).parent / "static" / "mcdonalds.svg").read_bytes()).decode()
    st.markdown(f'<div style="text-align:center;padding:12px 0 16px 0;"><img src="data:image/svg+xml;base64,{_svg_b64}" width="120" /></div><hr style="margin:0 0 24px 0; border:none; border-top:1px solid #E8E8E8;">', unsafe_allow_html=True)

    min_d = df["发送日期"].min().date()
    max_d = df["发送日期"].max().date()
    st.markdown('<div class="sidebar-filter-title">现期</div>', unsafe_allow_html=True)
    current_date = st.date_input(
        "", value=max_d,
        min_value=min_d, max_value=max_d, label_visibility="collapsed", key="current"
    )
    st.markdown('<div class="sidebar-filter-title">基期</div>', unsafe_allow_html=True)
    base_range = st.date_input(
        "", value=(min_d, max_d),
        min_value=min_d, max_value=max_d, label_visibility="collapsed", key="base"
    )
    st.markdown('<div class="sidebar-filter-title">渠道</div>', unsafe_allow_html=True)
    channels_all = ["全部"] + sorted(df["渠道"].dropna().unique().tolist())
    sel_channel = st.selectbox("", channels_all, label_visibility="collapsed", key="ch")
    st.markdown('<div class="sidebar-filter-title">计划类型</div>', unsafe_allow_html=True)
    plans_all = ["全部"] + sorted(df["计划类型"].dropna().unique().tolist())
    sel_plan = st.selectbox("", plans_all, label_visibility="collapsed", key="pl")
    st.markdown('<div class="sidebar-filter-title">Owner</div>', unsafe_allow_html=True)
    owners_all = ["全部"] + sorted(df["owner"].dropna().unique().tolist())
    sel_owner = st.selectbox("", owners_all, label_visibility="collapsed", key="ow")
    st.markdown('<div class="sidebar-filter-title">是否用券</div>', unsafe_allow_html=True)
    coupon_all = ["全部"] + sorted(df["是否用券"].dropna().unique().tolist()) if "是否用券" in df.columns else ["全部"]
    sel_coupon = st.selectbox("", coupon_all, label_visibility="collapsed", key="cp")

# ─── 应用筛选 ───
dff = df
# 渠道/计划类型/Owner 筛选（同时影响基期和现期）
if sel_channel != "全部":
    dff = dff[dff["渠道"] == sel_channel]
if sel_plan != "全部":
    dff = dff[dff["计划类型"] == sel_plan]
if sel_owner != "全部":
    dff = dff[dff["owner"] == sel_owner]
if sel_coupon != "全部" and "是否用券" in dff.columns:
    dff = dff[dff["是否用券"] == sel_coupon]
# 基期数据
df_base = dff.copy()
if isinstance(base_range, (list, tuple)) and len(base_range) == 2:
    sd, ed = base_range
    if pd.notna(sd) and pd.notna(ed):
        df_base = df_base[
            (df_base["发送日期"] >= pd.to_datetime(sd))
            & (df_base["发送日期"] <= pd.to_datetime(ed))
        ]
# 现期数据（单日）
df_current = dff[dff["发送日期"] == pd.to_datetime(current_date)]
if df_base.empty:
    st.warning("基期范围无匹配数据")
    st.stop()
if df_current.empty:
    st.warning("现期日期无匹配数据，请选择有数据的日期")
    st.stop()

# ─── 日汇总（基期，用于趋势图等） ───
daily = df_base.groupby("发送日期").agg(
    触达成功=("触达成功", "sum"),
    点击人次=("点击人次", "sum"),
    订单Sales=("订单Sales", "sum"),
    Plan数量=("plan_id", "count"),
).reset_index()
daily["CTR"] = compute_ctr(daily)

# ─── 日汇总（按券维度，用于券分析图） ───
if "是否用券" in df_base.columns:
    daily_coupon = df_base.groupby(["发送日期", "是否用券"]).agg(
        触达成功=("触达成功", "sum"),
        点击人次=("点击人次", "sum"),
        Plan数量=("plan_id", "count"),
    ).reset_index()
    daily_coupon["CTR"] = compute_ctr(daily_coupon)
else:
    daily_coupon = None

# ─── DAU 日序列（跟随基期日期范围；不受渠道/计划/Owner/券筛子影响） ───
if not dau_raw.empty:
    dau_daily = dau_raw.copy()
    if isinstance(base_range, (list, tuple)) and len(base_range) == 2:
        sd, ed = base_range
        if pd.notna(sd) and pd.notna(ed):
            dau_daily = dau_daily[
                (dau_daily["日期"] >= pd.to_datetime(sd))
                & (dau_daily["日期"] <= pd.to_datetime(ed))
            ]
    dau_daily = dau_daily.sort_values("日期").reset_index(drop=True)
else:
    dau_daily = dau_raw

# ═══════════════════════════════════════════════════════════════
# Tab 主体
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["监控", "趋势", "渠道", "owner", "漏斗", "券"]
)
with tab1:
    tab_health.render(df_base, df_current)
with tab2:
    tab_overview.render(daily, daily_coupon, dau_daily)
with tab3:
    tab_channel.render(df_base)
with tab4:
    tab_drilldown.render(df_base)
with tab5:
    tab_funnel.render(df_base)
with tab6:
    tab_coupon.render(daily_coupon)
