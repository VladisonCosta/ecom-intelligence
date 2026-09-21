-- =========================================================
-- Ecom Intelligence
-- Data Quality Checks
-- =========================================================

-- 1. Orders referencing nonexistent customers
SELECT COUNT(*) AS orphan_orders
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- 2. Order items referencing nonexistent orders
SELECT COUNT(*) AS orphan_order_items_orders
FROM order_items oi
LEFT JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 3. Order items referencing nonexistent products
SELECT COUNT(*) AS orphan_order_items_products
FROM order_items oi
LEFT JOIN products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;


-- 4. Order items referencing nonexistent sellers
SELECT COUNT(*) AS orphan_order_items_sellers
FROM order_items oi
LEFT JOIN sellers s
    ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL;


-- 5. Payments referencing nonexistent orders
SELECT COUNT(*) AS orphan_payments
FROM order_payments op
LEFT JOIN orders o
    ON op.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 6. Reviews referencing nonexistent orders
SELECT COUNT(*) AS orphan_reviews
FROM order_reviews r
LEFT JOIN orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 7. Invalid review scores
SELECT COUNT(*) AS invalid_review_scores
FROM order_reviews
WHERE review_score NOT BETWEEN 1 AND 5;


-- 8. Invalid monetary values
SELECT COUNT(*) AS invalid_order_item_values
FROM order_items
WHERE price < 0
   OR freight_value < 0;


-- 9. Invalid payment values
SELECT COUNT(*) AS invalid_payment_values
FROM order_payments
WHERE payment_value < 0;


-- 10. Product categories without English translation
SELECT
    p.product_category_name,
    COUNT(*) AS products
FROM products p
LEFT JOIN product_category_translation t
    ON p.product_category_name = t.product_category_name
WHERE p.product_category_name IS NOT NULL
  AND t.product_category_name IS NULL
GROUP BY p.product_category_name
ORDER BY products DESC;