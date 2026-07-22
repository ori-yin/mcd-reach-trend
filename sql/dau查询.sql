WITH params AS (
    SELECT
        DATE_FORMAT(CURRENT_DATE - INTERVAL '1' DAY, '%Y%m%d') AS bi_date,
        CURRENT_DATE - INTERVAL '1' DAY AS end_date,
        CURRENT_DATE - INTERVAL '20' DAY AS start_date
),

-- 常规Plan点击用户
normal_click AS (
    SELECT
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)) AS send_date,
        main.channel_name,
        main.mid
    FROM hive.ads_consumer.t_cnn_normal_plan_result_detail_d main
    CROSS JOIN params p
    WHERE main.bi_dt = p.bi_date
      AND CAST(main.list_date AS DATE)
            BETWEEN p.start_date
                AND p.end_date - INTERVAL '1' DAY
      AND main.channel_name IS NOT NULL
      AND main.ctr_flag = 1
      AND main.mid IS NOT NULL
),

-- AARR Plan点击用户
aarr_click AS (
    SELECT
        DATE_ADD('day', 1, CAST(main.list_date AS DATE)) AS send_date,
        main.channel_name,
        main.mid
    FROM hive.ads_consumer.t_spp_cnn_result_detail_d main
    CROSS JOIN params p
    WHERE main.bi_dt = p.bi_date
      AND CAST(main.list_date AS DATE)
            BETWEEN p.start_date
                AND p.end_date - INTERVAL '1' DAY
      AND main.channel_name IS NOT NULL
      AND main.ctr_flag = 1
      AND main.mid IS NOT NULL
),

-- 合并来源
click_union AS (
    SELECT send_date, channel_name, mid
    FROM normal_click

    UNION ALL

    SELECT send_date, channel_name, mid
    FROM aarr_click
)

-- 总DAU
SELECT
    send_date AS "日期",
    'ALL' AS "渠道",
    COUNT(DISTINCT mid) AS "DAU"
FROM click_union
GROUP BY send_date

UNION ALL

-- 分渠道DAU
SELECT
    send_date AS "日期",
    channel_name AS "渠道",
    COUNT(DISTINCT mid) AS "DAU"
FROM click_union
GROUP BY
    send_date,
    channel_name

ORDER BY
    1 DESC,
    2;