import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database import get_engine


st.set_page_config(
    page_title="E-commerce Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HELPERS
# ============================================================

@st.cache_resource
def load_engine():
    return get_engine()


@st.cache_data(ttl=300)
def load_dataframe(query):
    engine = load_engine()

    with engine.connect() as connection:
        return pd.read_sql(text(query), connection)


def format_brl(value):
    """Format numeric values using Brazilian currency notation."""
    value = float(value)

    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.2f} mi".replace(".", ",")

    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f} mil".replace(".", ",")

    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_integer(value):
    return f"{int(value):,}".replace(",", ".")


# ============================================================
# DATA
# ============================================================

kpis = load_dataframe(
    """
    SELECT
        COUNT(*) AS total_orders,
        COUNT(DISTINCT customer_unique_id) AS unique_customers,
        SUM(product_value) AS gmv,
        AVG(product_value) AS average_order_value,
        AVG(review_score) AS average_review_score
    FROM vw_order_metrics
    WHERE order_status NOT IN ('canceled', 'unavailable');
    """
).iloc[0]


monthly_sales = load_dataframe(
    """
    SELECT
        month,
        orders,
        customers,
        gmv,
        average_order_value,
        freight_value
    FROM vw_monthly_sales
    ORDER BY month;
    """
)


categories = load_dataframe(
    """
    SELECT
        category,
        orders,
        items_sold,
        revenue,
        average_item_price,
        freight_value
    FROM vw_category_performance
    ORDER BY revenue DESC;
    """
)


states = load_dataframe(
    """
    SELECT
        customer_state,
        COUNT(*) AS orders,
        COUNT(DISTINCT customer_unique_id) AS customers,
        SUM(product_value) AS gmv
    FROM vw_order_metrics
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_state
    ORDER BY gmv DESC;
    """
)


delivery = load_dataframe(
    """
    SELECT
        delivered_late,
        COUNT(*) AS orders,
        AVG(review_score) AS average_review_score
    FROM vw_delivery_performance
    WHERE review_score IS NOT NULL
    GROUP BY delivered_late
    ORDER BY delivered_late;
    """
)


delivery_kpis = load_dataframe(
    """
    SELECT
        COUNT(*) AS delivered_orders,
        AVG(delivery_days) AS average_delivery_days,

        100.0 *
        COUNT(*) FILTER (WHERE delivered_late) /
        NULLIF(COUNT(*), 0) AS late_delivery_percentage

    FROM vw_delivery_performance;
    """
).iloc[0]


customers = load_dataframe(
    """
    SELECT
        COUNT(*) FILTER (WHERE orders = 1) AS one_time_customers,
        COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,

        100.0 *
        COUNT(*) FILTER (WHERE orders > 1) /
        NULLIF(COUNT(*), 0) AS repeat_customer_percentage

    FROM vw_customer_metrics;
    """
).iloc[0]


# Make sure month is a datetime column.
monthly_sales["month"] = pd.to_datetime(monthly_sales["month"])


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("E-commerce Intelligence")

st.sidebar.caption(
    "Analytics dashboard powered by PostgreSQL"
)

st.sidebar.divider()

st.sidebar.subheader("Filters")

min_date = monthly_sales["month"].min().date()
max_date = monthly_sales["month"].max().date()

date_range = st.sidebar.date_input(
    "Sales period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

top_n = st.sidebar.slider(
    "Categories displayed",
    min_value=5,
    max_value=20,
    value=10,
)

st.sidebar.divider()

st.sidebar.markdown(
    """
    **Data pipeline**

    Olist CSV  
    ↓  
    Python ETL  
    ↓  
    PostgreSQL  
    ↓  
    SQL Analytics  
    ↓  
    Streamlit
    """
)

st.sidebar.caption(
    "Portfolio Data Engineering & Analytics Project"
)


# ============================================================
# FILTERS
# ============================================================

filtered_monthly = monthly_sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered_monthly = filtered_monthly[
        (filtered_monthly["month"].dt.date >= start_date)
        & (filtered_monthly["month"].dt.date <= end_date)
    ]


top_categories = categories.head(top_n).copy()
top_states = states.head(10).copy()


# ============================================================
# HEADER
# ============================================================

st.title("E-commerce Intelligence")

st.markdown(
    """
    **Sales, customer and logistics intelligence from a real Brazilian
    e-commerce dataset.**
    """
)

st.caption(
    "End-to-end analytics project built with Python, PostgreSQL, "
    "SQL, Pandas, Plotly and Streamlit."
)

st.divider()


# ============================================================
# EXECUTIVE KPIs
# ============================================================

st.subheader("Executive Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "GMV",
    format_brl(kpis["gmv"]),
)

col2.metric(
    "Orders",
    format_integer(kpis["total_orders"]),
)

col3.metric(
    "Customers",
    format_integer(kpis["unique_customers"]),
)

col4.metric(
    "Average Order",
    format_brl(kpis["average_order_value"]),
)

col5.metric(
    "Average Review",
    f"{float(kpis['average_review_score']):.2f} / 5",
)


# ============================================================
# SALES PERFORMANCE
# ============================================================

st.divider()

st.subheader("Sales Performance")

sales_col1, sales_col2 = st.columns([2, 1])

with sales_col1:

    fig_sales = px.area(
        filtered_monthly,
        x="month",
        y="gmv",
        markers=True,
        labels={
            "month": "Month",
            "gmv": "GMV (R$)",
        },
    )

    fig_sales.update_layout(
        title="Monthly GMV",
        xaxis_title=None,
        yaxis_title="Revenue (R$)",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_sales,
        width="stretch",
    )


with sales_col2:

    fig_orders = px.line(
        filtered_monthly,
        x="month",
        y="orders",
        markers=True,
        labels={
            "month": "Month",
            "orders": "Orders",
        },
    )

    fig_orders.update_layout(
        title="Monthly Order Volume",
        xaxis_title=None,
        yaxis_title="Orders",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_orders,
        width="stretch",
    )


# ============================================================
# MARKET PERFORMANCE
# ============================================================

st.divider()

st.subheader("Market Performance")

category_col, state_col = st.columns(2)


with category_col:

    category_chart = top_categories.sort_values(
        "revenue",
        ascending=True,
    )

    fig_categories = px.bar(
        category_chart,
        x="revenue",
        y="category",
        orientation="h",
        labels={
            "revenue": "Revenue (R$)",
            "category": "Category",
        },
        hover_data={
            "orders": True,
            "items_sold": True,
        },
    )

    fig_categories.update_layout(
        title=f"Top {top_n} Categories by Revenue",
        yaxis_title=None,
    )

    st.plotly_chart(
        fig_categories,
        width="stretch",
    )


with state_col:

    state_chart = top_states.sort_values(
        "gmv",
        ascending=True,
    )

    fig_states = px.bar(
        state_chart,
        x="gmv",
        y="customer_state",
        orientation="h",
        labels={
            "gmv": "GMV (R$)",
            "customer_state": "State",
        },
        hover_data={
            "orders": True,
            "customers": True,
        },
    )

    fig_states.update_layout(
        title="Top 10 States by GMV",
        yaxis_title=None,
    )

    st.plotly_chart(
        fig_states,
        width="stretch",
    )


# ============================================================
# LOGISTICS
# ============================================================

st.divider()

st.subheader("Logistics & Customer Experience")

delivery_col1, delivery_col2, delivery_col3 = st.columns(3)

delivery_col1.metric(
    "Delivered Orders",
    format_integer(delivery_kpis["delivered_orders"]),
)

delivery_col2.metric(
    "Average Delivery Time",
    f"{float(delivery_kpis['average_delivery_days']):.2f} days",
)

delivery_col3.metric(
    "Late Deliveries",
    f"{float(delivery_kpis['late_delivery_percentage']):.2f}%",
)


delivery_chart = delivery.copy()

delivery_chart["delivery_status"] = delivery_chart[
    "delivered_late"
].map(
    {
        False: "On time",
        True: "Late",
    }
)


fig_reviews = px.bar(
    delivery_chart,
    x="delivery_status",
    y="average_review_score",
    text_auto=".2f",
    labels={
        "delivery_status": "Delivery Status",
        "average_review_score": "Average Review Score",
    },
)

fig_reviews.update_layout(
    title="Impact of Delivery Delays on Customer Reviews",
    xaxis_title=None,
)

fig_reviews.update_yaxes(
    range=[0, 5]
)

st.plotly_chart(
    fig_reviews,
    width="stretch",
)


# ============================================================
# CUSTOMER RETENTION
# ============================================================

st.divider()

st.subheader("Customer Retention")

customer_col1, customer_col2, customer_col3 = st.columns(3)

customer_col1.metric(
    "One-time Customers",
    format_integer(customers["one_time_customers"]),
)

customer_col2.metric(
    "Repeat Customers",
    format_integer(customers["repeat_customers"]),
)

customer_col3.metric(
    "Repeat Customer Rate",
    f"{float(customers['repeat_customer_percentage']):.2f}%",
)


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

st.divider()

st.subheader("Business Insights")

top_category = categories.iloc[0]
top_state = states.iloc[0]

on_time_review = delivery.loc[
    delivery["delivered_late"] == False,
    "average_review_score",
]

late_review = delivery.loc[
    delivery["delivered_late"] == True,
    "average_review_score",
]


if not on_time_review.empty and not late_review.empty:
    review_difference = (
        float(on_time_review.iloc[0])
        - float(late_review.iloc[0])
    )
else:
    review_difference = 0


insight1, insight2 = st.columns(2)

with insight1:

    st.info(
        f"""
        **Revenue concentration**

        `{top_category['category']}` is the highest-revenue product
        category in the dataset, generating
        **{format_brl(top_category['revenue'])}**.
        """
    )

    st.info(
        f"""
        **Customer retention**

        Only **{float(customers['repeat_customer_percentage']):.2f}%**
        of customers placed more than one order.
        """
    )


with insight2:

    st.info(
        f"""
        **Geographic performance**

        `{top_state['customer_state']}` leads the analyzed states with
        **{format_brl(top_state['gmv'])}** in GMV.
        """
    )

    st.info(
        f"""
        **Delivery experience**

        Late deliveries represent
        **{float(delivery_kpis['late_delivery_percentage']):.2f}%**
        of delivered orders.

        On-time deliveries receive an average review score approximately
        **{review_difference:.2f} points higher** than late deliveries.
        """
    )


# ============================================================
# DATA EXPLORER
# ============================================================

st.divider()

st.subheader("Data Explorer")

tab1, tab2, tab3 = st.tabs(
    [
        "Categories",
        "States",
        "Monthly Sales",
    ]
)

with tab1:
    st.dataframe(
        categories,
        width="stretch",
        hide_index=True,
    )

with tab2:
    st.dataframe(
        states,
        width="stretch",
        hide_index=True,
    )

with tab3:
    st.dataframe(
        monthly_sales,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data source: Brazilian E-Commerce Public Dataset by Olist | "
    "Pipeline: Python + PostgreSQL + SQL | "
    "Visualization: Streamlit + Plotly"
)