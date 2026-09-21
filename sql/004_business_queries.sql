-- =========================================================
-- Ecom Intelligence
-- Business Analysis Queries
-- =========================================================


-- 1. Executive KPIs

SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    ROUND(SUM(product_value), 2) AS gmv,
    ROUND(AVG(product_value), 2) AS average_order_value,
    ROUND(AVG(review_score), 2) AS average_review_score
FROM vw_order_metrics
WHERE order_status NOT IN ('canceled', 'unavailable');


-- 2. Monthly sales evolution

SELECT *
FROM vw_monthly_sales
ORDER BY month;


-- 3. Top 10 categories by revenue

SELECT *
FROM vw_category_performance
ORDER BY revenue DESC
LIMIT 10;


-- 4. Top 10 states by GMV

SELECT
    customer_state,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_unique_id) AS customers,
    ROUND(SUM(product_value), 2) AS gmv,
    ROUND(AVG(product_value), 2) AS average_order_value
FROM vw_order_metrics
WHERE order_status NOT IN ('canceled', 'unavailable')
GROUP BY customer_state
ORDER BY gmv DESC
LIMIT 10;


-- 5. Top sellers by revenue

SELECT *
FROM vw_seller_performance
ORDER BY revenue DESC
LIMIT 10;


-- 6. Delivery performance

SELECT
    COUNT(*) AS delivered_orders,

    ROUND(
        AVG(delivery_days)::numeric,
        2
    ) AS average_delivery_days,

    ROUND(
        100.0 *
        COUNT(*) FILTER (WHERE delivered_late) /
        NULLIF(COUNT(*), 0),
        2
    ) AS late_delivery_percentage

FROM vw_delivery_performance;


-- 7. Review score: late vs on-time deliveries

SELECT
    delivered_late,

    COUNT(*) AS orders,

    ROUND(
        AVG(review_score)::numeric,
        2
    ) AS average_review_score

FROM vw_delivery_performance

WHERE review_score IS NOT NULL

GROUP BY delivered_late;


-- 8. Repeat customers

SELECT
    COUNT(*) FILTER (WHERE orders = 1) AS one_time_customers,

    COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,

    ROUND(
        100.0 *
        COUNT(*) FILTER (WHERE orders > 1) /
        NULLIF(COUNT(*), 0),
        2
    ) AS repeat_customer_percentage

FROM vw_customer_metrics;


-- 9. Freight impact

SELECT
    ROUND(SUM(product_value), 2) AS product_value,
    ROUND(SUM(freight_value), 2) AS freight_value,

    ROUND(
        100.0 * SUM(freight_value) /
        NULLIF(SUM(product_value), 0),
        2
    ) AS freight_to_product_percentage

FROM vw_order_metrics

WHERE order_status NOT IN ('canceled', 'unavailable');


-- 10. Highest-value customers

SELECT
    customer_unique_id,
    orders,
    total_spent,
    average_order_value
FROM vw_customer_metrics
ORDER BY total_spent DESC
LIMIT 10;