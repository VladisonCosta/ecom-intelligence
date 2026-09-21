from sqlalchemy import text

from database import get_engine


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def fetch_one(connection, query):
    return connection.execute(text(query)).mappings().one()


def executive_kpis(connection):
    query = """
        SELECT
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_unique_id) AS unique_customers,
            ROUND(SUM(product_value), 2) AS gmv,
            ROUND(AVG(product_value), 2) AS average_order_value,
            ROUND(AVG(review_score), 2) AS average_review_score
        FROM vw_order_metrics
        WHERE order_status NOT IN ('canceled', 'unavailable');
    """

    return fetch_one(connection, query)


def delivery_metrics(connection):
    query = """
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
    """

    return fetch_one(connection, query)


def customer_metrics(connection):
    query = """
        SELECT
            COUNT(*) FILTER (WHERE orders = 1)
                AS one_time_customers,

            COUNT(*) FILTER (WHERE orders > 1)
                AS repeat_customers,

            ROUND(
                100.0 *
                COUNT(*) FILTER (WHERE orders > 1) /
                NULLIF(COUNT(*), 0),
                2
            ) AS repeat_customer_percentage

        FROM vw_customer_metrics;
    """

    return fetch_one(connection, query)


def top_categories(connection):
    query = """
        SELECT
            category,
            orders,
            items_sold,
            revenue
        FROM vw_category_performance
        ORDER BY revenue DESC
        LIMIT 10;
    """

    return connection.execute(text(query)).mappings().all()


def main():
    engine = get_engine()

    with engine.connect() as connection:

        print_section("EXECUTIVE KPIs")

        kpis = executive_kpis(connection)

        print(f"Orders: {kpis['total_orders']:,}")
        print(f"Unique customers: {kpis['unique_customers']:,}")
        print(f"GMV: R$ {kpis['gmv']:,.2f}")
        print(
            f"Average order value: "
            f"R$ {kpis['average_order_value']:,.2f}"
        )
        print(
            f"Average review score: "
            f"{kpis['average_review_score']}"
        )

        print_section("DELIVERY")

        delivery = delivery_metrics(connection)

        print(
            f"Delivered orders: "
            f"{delivery['delivered_orders']:,}"
        )
        print(
            f"Average delivery time: "
            f"{delivery['average_delivery_days']} days"
        )
        print(
            f"Late deliveries: "
            f"{delivery['late_delivery_percentage']}%"
        )

        print_section("CUSTOMERS")

        customers = customer_metrics(connection)

        print(
            f"One-time customers: "
            f"{customers['one_time_customers']:,}"
        )
        print(
            f"Repeat customers: "
            f"{customers['repeat_customers']:,}"
        )
        print(
            f"Repeat customer rate: "
            f"{customers['repeat_customer_percentage']}%"
        )

        print_section("TOP 10 CATEGORIES")

        for index, category in enumerate(
            top_categories(connection),
            start=1,
        ):
            print(
                f"{index:>2}. "
                f"{category['category']:<35} "
                f"R$ {category['revenue']:>12,.2f}"
            )


if __name__ == "__main__":
    main()