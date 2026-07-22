WITH params AS (
    SELECT
        DATE_FORMAT(CURRENT_DATE - INTERVAL '1' DAY, '%Y%m%d') AS bi_date,    -- 12点后用昨天的快照，12点前改前天
        (CURRENT_DATE - INTERVAL '1' DAY) AS end_date,      -- 昨天
        (CURRENT_DATE - INTERVAL '29' DAY) AS start_date    -- 当前实际是近28天发送日期
),

-- ① plan_id → message_id 映射
plan_msg_mapping AS (
    SELECT
        plan_id,
        MAX(message_id) AS message_id
    FROM hive.dwd_consumer.t_cnn_execute_result_d
    WHERE plan_id IS NOT NULL
      AND message_id IS NOT NULL
    GROUP BY plan_id
),

-- ② plan_id → 消息内容
plan_content AS (
    SELECT
        pmm.plan_id,
        msg.title,
        msg.content
    FROM plan_msg_mapping pmm
    LEFT JOIN hive.dwd_consumer.t_cnn_message_d msg
        ON pmm.message_id = msg.id
),

-- 常规 Plan 聚合
normal_agg AS (
    SELECT
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)) AS send_date,
        '常规Plan' AS plan_type,
        main.channel_name,
        main.plan_id,
        main.plan_title,
        CAST(main.strategy_owner AS VARCHAR) AS budget_owner,
        CASE
            WHEN main.coupon_push_couponid IS NULL OR TRIM(main.coupon_push_couponid) = '' THEN '否'
            ELSE '是'
        END AS coupon_tag,

        COUNT(DISTINCT main.mid) AS plan_cus_sum,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.app_push_flag = 1
               OR main.sms_push_flag = 1
               OR main.rgm_push_flag = 1
               OR main.wechat_push_flag = 1
               OR main.wechat_service_push_flag = 1
        ) AS success_cus,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.ctr_flag = 1
        ) AS click_cus,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.ctr_flag = 1
              AND main.tracking_period_lc_gc > 0
        ) AS click_buy_cus,

        SUM(main.tracking_period_lc_gc) AS related_order_cnt,
        SUM(main.tracking_period_lc_sales) AS related_order_amount

    FROM hive.ads_consumer.t_cnn_normal_plan_result_detail_d main
    CROSS JOIN params p
    WHERE main.bi_dt = p.bi_date
      AND CAST(main.list_date AS DATE) BETWEEN p.start_date AND p.end_date - INTERVAL '1' DAY
      AND main.channel_name IS NOT NULL
    GROUP BY
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)),
        main.channel_name,
        main.plan_id,
        main.plan_title,
        CAST(main.strategy_owner AS VARCHAR),
        CASE
            WHEN main.coupon_push_couponid IS NULL OR TRIM(main.coupon_push_couponid) = '' THEN '否'
            ELSE '是'
        END
),

-- AARR Plan 聚合
aarr_agg AS (
    SELECT
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)) AS send_date,
        'AARRPlan' AS plan_type,
        main.channel_name,
        main.plan_id,
        main.plan_title,
        CAST(main.strategy_owner AS VARCHAR) AS budget_owner,
        CASE
            WHEN main.coupon_push_couponid IS NULL OR TRIM(main.coupon_push_couponid) = '' THEN '否'
            ELSE '是'
        END AS coupon_tag,

        COUNT(DISTINCT main.mid) AS plan_cus_sum,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.app_push_flag = 1
               OR main.sms_push_flag = 1
               OR main.rgm_push_flag = 1
               OR main.wechat_push_flag = 1
               OR main.wechat_service_push_flag = 1
        ) AS success_cus,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.ctr_flag = 1
        ) AS click_cus,

        COUNT(DISTINCT main.mid) FILTER (
            WHERE main.ctr_flag = 1
              AND main.tracking_period_lc_gc > 0
        ) AS click_buy_cus,

        SUM(main.tracking_period_lc_gc) AS related_order_cnt,
        SUM(main.tracking_period_lc_sales) AS related_order_amount

    FROM hive.ads_consumer.t_spp_cnn_result_detail_d main
    CROSS JOIN params p
    WHERE main.bi_dt = p.bi_date
      AND CAST(main.list_date AS DATE) BETWEEN p.start_date AND p.end_date - INTERVAL '1' DAY
      AND main.channel_name IS NOT NULL
    GROUP BY
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)),
        main.channel_name,
        main.plan_id,
        main.plan_title,
        CAST(main.strategy_owner AS VARCHAR),
        CASE
            WHEN main.coupon_push_couponid IS NULL OR TRIM(main.coupon_push_couponid) = '' THEN '否'
            ELSE '是'
        END
),

-- 合并
final_union AS (
    SELECT * FROM normal_agg
    UNION ALL
    SELECT * FROM aarr_agg
)

SELECT
    fu.send_date AS "发送日期",
    fu.plan_type AS "计划类型",
    fu.channel_name AS "渠道",
    fu.plan_id AS "Plan ID",
    fu.plan_title AS "Plan名称",
    fu.budget_owner AS "预算owner",
    fu.coupon_tag AS "是否用券",
    fu.plan_cus_sum AS "预计触达",
    fu.success_cus AS "触达成功",
    fu.click_cus AS "点击人次",
    fu.click_buy_cus AS "点击后下单人次",
    fu.related_order_cnt AS "订单GC",
    fu.related_order_amount AS "订单Sales",
    pc.title AS "消息标题",
    pc.content AS "消息内容"
FROM final_union fu
LEFT JOIN plan_content pc
    ON fu.plan_id = pc.plan_id
ORDER BY fu.send_date DESC, fu.plan_type, fu.channel_name;