# -*- coding: utf-8 -*-
"""Tab6: 券分析（迁移自 tab_overview.py:97-289 的两张券图）"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import TEXT, TEXT_SUB, axis_mk, axis_rate, AXIS_TITLE_SIZE, add_ctr_mean_line


def _flatten_pivot_columns(pivot):
    """展平 pivot_table 多级列名（兼容 tuple/str）"""
    pivot.columns = [
        f"{col[0]}_{col[1]}" if isinstance(col, tuple) and col[1]
        else (col if isinstance(col, str) else col[0])
        for col in pivot.columns
    ]
    return pivot


def _is_coupon_yes(val):
    """判定 是否用券 值是否为"是" """
    s = str(val).lower().strip()
    if s in ("是", "true", "1", "yes"):
        return True
    if s in ("否", "false", "0", "no"):
        return False
    return val not in (0, "0", False)


def _safe_sum(df, cols):
    """对多列做 sum(axis=1) 自动跳过 None/缺失列；全空返回空 Series。"""
    valid = [c for c in cols if c]
    if not valid:
        return pd.Series(dtype=float)
    return df[valid].fillna(0).sum(axis=1)


def render(daily_coupon):
    """渲染券分析 Tab

    Args:
        daily_coupon: 按券维度日聚合数据（来自 app.py:120-128）
    """
    if daily_coupon is None or daily_coupon.empty:
        st.info("无券分析数据")
        return

    # 按是否用券拆分一次（避免重复 apply）
    _yes_mask = daily_coupon["是否用券"].apply(_is_coupon_yes)
    _yes_df = daily_coupon[_yes_mask]
    _no_df = daily_coupon[~_yes_mask]

    # ── 券分析趋势 ──
    st.markdown('<div class="section-title">券分析趋势</div>', unsafe_allow_html=True)

    try:
        # Pivot 成宽格式
        coupon_pivot = daily_coupon.pivot_table(
            index="发送日期", columns="是否用券",
            values=["触达成功", "CTR"], aggfunc="first"
        ).reset_index()

        # 展平多级列名
        coupon_pivot = _flatten_pivot_columns(coupon_pivot)

        # 确保列存在
        date_col = "发送日期"
        reach_yes = reach_no = ctr_yes = ctr_no = None

        # 自动检测列名：遍历 pivot 后的实际列
        coupon_values = daily_coupon["是否用券"].unique()
        for val in coupon_values:
            reach_col = f"触达成功_{val}"
            ctr_col = f"CTR_{val}"
            if _is_coupon_yes(val):
                if reach_col in coupon_pivot.columns:
                    reach_yes = reach_col
                if ctr_col in coupon_pivot.columns:
                    ctr_yes = ctr_col
            else:
                if reach_col in coupon_pivot.columns:
                    reach_no = reach_col
                if ctr_col in coupon_pivot.columns:
                    ctr_no = ctr_col

        # 填充缺失值为0
        for col in [reach_yes, reach_no, ctr_yes, ctr_no]:
            if col:
                coupon_pivot[col] = coupon_pivot[col].fillna(0)
    except Exception as e:
        st.warning(f"券分析数据处理异常: {e}")
        coupon_pivot = None
        reach_yes = reach_no = ctr_yes = ctr_no = None

    # pivot 失败时跳过图表渲染，但不阻断后续明细表
    if coupon_pivot is not None:
        # 颜色定义 - 麦当劳色系
        COLOR_COUPON = "#DA291C"       # 用券 - 麦当劳红
        COLOR_NO_COUPON = "#FFC72C"    # 不用券 - 麦当劳黄
        COLOR_CTR_COUPON = "#95BC46"   # 用券CTR - 绿色
        COLOR_CTR_NO_COUPON = "#3E9DC9"  # 不用券CTR - 蓝色

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])

        # 叠加柱状图：不用券在下，用券在上
        if reach_no:
            # 计算不用券占比百分比
            total_reach = coupon_pivot[reach_no].fillna(0) + (coupon_pivot[reach_yes].fillna(0) if reach_yes else 0)
            pct_no = (coupon_pivot[reach_no].fillna(0) / total_reach.replace(0, np.nan) * 100).round(1).fillna(0)
            pct_text = pct_no.apply(lambda x: f"{x:.1f}%" if x > 0 else "")

            fig2.add_trace(
                go.Bar(
                    x=coupon_pivot[date_col], y=coupon_pivot[reach_no],
                    name="不用券触达", marker_color=COLOR_NO_COUPON, opacity=0.9,
                    text=pct_text, textposition="inside", textfont=dict(size=11, color="#333"),
                    hovertemplate="不用券触达: %{y:,.0f}<extra></extra>"
                ),
                secondary_y=False
            )
        if reach_yes:
            fig2.add_trace(
                go.Bar(
                    x=coupon_pivot[date_col], y=coupon_pivot[reach_yes],
                    name="用券触达", marker_color=COLOR_COUPON, opacity=0.9,
                    hovertemplate="用券触达: %{y:,.0f}<extra></extra>"
                ),
                secondary_y=False
            )

        # CTR 折线
        if ctr_yes:
            fig2.add_trace(
                go.Scatter(
                    x=coupon_pivot[date_col], y=coupon_pivot[ctr_yes],
                    name="用券CTR", mode="lines+markers",
                    line=dict(color=COLOR_CTR_COUPON, width=2.5),
                    marker=dict(size=6),
                    hovertemplate="用券CTR: %{y:.2f}%<extra></extra>"
                ),
                secondary_y=True
            )
        if ctr_no:
            fig2.add_trace(
                go.Scatter(
                    x=coupon_pivot[date_col], y=coupon_pivot[ctr_no],
                    name="不用券CTR", mode="lines+markers",
                    line=dict(color=COLOR_CTR_NO_COUPON, width=2.5),
                    marker=dict(size=6),
                    hovertemplate="不用券CTR: %{y:.2f}%<extra></extra>"
                ),
                secondary_y=True
            )

        _reach_total = _safe_sum(coupon_pivot, [reach_yes, reach_no])
        _ctr_combined = pd.concat([coupon_pivot[c] for c in [ctr_yes, ctr_no] if c]) if (ctr_yes or ctr_no) else pd.Series([0])

        fig2.update_layout(
            barmode="stack",
            paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font=dict(color=TEXT),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=10, b=0), height=300,
            xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
            yaxis=axis_mk(_reach_total if len(_reach_total) else pd.Series([0])),
            yaxis2=axis_rate(_ctr_combined),
            hovermode="x unified"
        )
        fig2.update_yaxes(title_text="<b>触达成功</b>", secondary_y=False, title_font=dict(color=COLOR_COUPON, size=AXIS_TITLE_SIZE), showgrid=False)
        fig2.update_yaxes(title_text="<b>CTR (%)</b>", secondary_y=True, title_font=dict(color=COLOR_CTR_COUPON, size=AXIS_TITLE_SIZE), showgrid=False)

        # 用券 / 不用券 CTR 加权均值虚线
        for ctr_col, reach_col, color, prefix in [
            (ctr_yes, reach_yes, COLOR_CTR_COUPON,     "用券均值"),
            (ctr_no,  reach_no,  COLOR_CTR_NO_COUPON,  "不用券均值"),
        ]:
            if ctr_col and reach_col:
                sub = _yes_df if ctr_col is ctr_yes else _no_df
                add_ctr_mean_line(fig2, sub, color=color, label_prefix=prefix)

        st.plotly_chart(fig2, use_container_width=True)

        # ── Plan数量柱状图（按券维度）──
        st.markdown('<div class="section-title">Plan数量趋势</div>', unsafe_allow_html=True)

        # Pivot plan数据
        try:
            plan_pivot = daily_coupon.pivot_table(
                index="发送日期", columns="是否用券",
                values="Plan数量", aggfunc="first"
            ).reset_index()

            plan_pivot = _flatten_pivot_columns(plan_pivot)

            plan_date_col = "发送日期"
            plan_yes = None
            plan_no = None

            # 自动检测列名（单列values时pivot不加前缀，列名直接是"是"/"否"）
            coupon_values = daily_coupon["是否用券"].unique()
            for val in coupon_values:
                # 尝试两种列名格式：带前缀和不带前缀
                col_with_prefix = f"Plan数量_{val}"
                col_no_prefix = str(val)
                col_name = col_with_prefix if col_with_prefix in plan_pivot.columns else col_no_prefix
                if col_name not in plan_pivot.columns:
                    continue
                if _is_coupon_yes(val):
                    plan_yes = col_name
                else:
                    plan_no = col_name

            # 填充缺失值为0
            for col in [plan_yes, plan_no]:
                if col:
                    plan_pivot[col] = plan_pivot[col].fillna(0)

            fig3 = go.Figure()

            # 叠加柱状图：不用券在下，用券在上
            if plan_no:
                # 计算不用券占比百分比
                total_plan = plan_pivot[plan_no].fillna(0) + (plan_pivot[plan_yes].fillna(0) if plan_yes else 0)
                pct_plan_no = (plan_pivot[plan_no].fillna(0) / total_plan.replace(0, np.nan) * 100).round(1).fillna(0)
                pct_plan_text = pct_plan_no.apply(lambda x: f"{x:.1f}%" if x > 0 else "")

                fig3.add_trace(
                    go.Bar(
                        x=plan_pivot[plan_date_col], y=plan_pivot[plan_no],
                        name="不用券Plan", marker_color=COLOR_NO_COUPON, opacity=0.9,
                        text=pct_plan_text, textposition="inside", textfont=dict(size=11, color="#333"),
                        hovertemplate="不用券Plan: %{y:,.0f}<extra></extra>"
                    )
                )
            if plan_yes:
                fig3.add_trace(
                    go.Bar(
                        x=plan_pivot[plan_date_col], y=plan_pivot[plan_yes],
                        name="用券Plan", marker_color=COLOR_COUPON, opacity=0.9,
                        hovertemplate="用券Plan: %{y:,.0f}<extra></extra>"
                    )
                )

            _plan_total = _safe_sum(plan_pivot, [plan_yes, plan_no])

            fig3.update_layout(
                barmode="stack",
                paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font=dict(color=TEXT),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=10, b=0), height=280,
                xaxis=dict(showgrid=False, tickfont=dict(color=TEXT_SUB), tickformat="%Y%m%d"),
                yaxis=axis_mk(_plan_total if len(_plan_total) else pd.Series([0])),
                hovermode="x unified"
            )
            fig3.update_yaxes(title_text="<b>Plan数量</b>", title_font=dict(color=COLOR_COUPON, size=AXIS_TITLE_SIZE), showgrid=False)

            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Plan数量图表渲染异常: {e}")