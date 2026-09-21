-- =========================================================
-- Ecom Intelligence
-- Analytical Views
-- =========================================================


-- ---------------------------------------------------------
-- Order-level financial metrics
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_order_metrics AS
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    COALESCE(items.items_count, 0) AS items_count,
    COALESCE(items.product_value, 0) AS product_value,
    COALESCE(items.freight_value, 0) AS freight_value,
    COALESCE(payments.payment_value, 0) AS payment_value,

    reviews.review_score,

    CASE
        WHEN o.order_delivered_customer_date IS NOT NULL
         AND o.order_delivered_customer_date >
             o.order_estimated_delivery_date
        THEN TRUE
        ELSE FALSE
    END AS delivered_late

FROM orders o

JOIN customers c
    ON o.customer_id = c.customer_id

LEFT JOIN (
    SELECT
        order_id,
        COUNT(*) AS items_count,
        SUM(price) AS product_value,
        SUM(freight_value) AS freight_value
    FROM order_items
    GROUP BY order_id
) items
    ON o.order_id = items.order_id

LEFT JOIN (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM order_payments
    GROUP BY order_id
) payments
    ON o.order_id = payments.order_id

LEFT JOIN (
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
) reviews
    ON o.order_id = reviews.order_id;


-- ---------------------------------------------------------
-- Monthly sales performance
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_monthly_sales AS
SELECT
    DATE_TRUNC('month', order_purchase_timestamp)::date AS month,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_unique_id) AS customers,
    ROUND(SUM(product_value), 2) AS gmv,
    ROUND(AVG(product_value), 2) AS average_order_value,
    ROUND(SUM(freight_value), 2) AS freight_value
FROM vw_order_metrics
WHERE order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------
-- Category performance
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'unknown'
    ) AS category,

    COUNT(DISTINCT oi.order_id) AS orders,
    SUM(oi.order_item_id * 0 + 1) AS items_sold,
    ROUND(SUM(oi.price), 2) AS revenue,
    ROUND(AVG(oi.price), 2) AS average_item_price,
    ROUND(SUM(oi.freight_value), 2) AS freight_value

FROM order_items oi

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN product_category_translation t
    ON p.product_category_name = t.product_category_name

JOIN orders o
    ON oi.order_id = o.order_id

WHERE o.order_status NOT IN ('canceled', 'unavailable')

GROUP BY 1;


-- ---------------------------------------------------------
-- Customer metrics
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_customer_metrics AS
SELECT
    customer_unique_id,

    COUNT(*) AS orders,

    ROUND(SUM(product_value), 2) AS total_spent,

    ROUND(AVG(product_value), 2) AS average_order_value,

    MIN(order_purchase_timestamp) AS first_purchase,

    MAX(order_purchase_timestamp) AS last_purchase

FROM vw_order_metrics

WHERE order_status NOT IN ('canceled', 'unavailable')

GROUP BY customer_unique_id;


-- ---------------------------------------------------------
-- Seller performance
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_seller_performance AS
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,

    COUNT(DISTINCT oi.order_id) AS orders,
    COUNT(*) AS items_sold,

    ROUND(SUM(oi.price), 2) AS revenue,

    ROUND(AVG(oi.price), 2) AS average_item_price,

    ROUND(SUM(oi.freight_value), 2) AS freight_value

FROM sellers s

JOIN order_items oi
    ON s.seller_id = oi.seller_id

JOIN orders o
    ON oi.order_id = o.order_id

WHERE o.order_status NOT IN ('canceled', 'unavailable')

GROUP BY
    s.seller_id,
    s.seller_city,
    s.seller_state;


-- ---------------------------------------------------------
-- Delivery performance
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW vw_delivery_performance AS
SELECT
    order_id,
    customer_state,

    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,

    EXTRACT(
        EPOCH FROM (
            order_delivered_customer_date -
            order_purchase_timestamp
        )
    ) / 86400.0 AS delivery_days,

    delivered_late,

    review_score

FROM vw_order_metrics

WHERE order_delivered_customer_date IS NOT NULL;