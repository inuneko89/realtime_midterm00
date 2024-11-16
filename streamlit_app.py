import streamlit as st
import pandas as pd
import pinotdb
import plotly.express as px
from datetime import datetime, timedelta
from pytz import timezone

# Function to get data from Pinot
def get_data_from_pinot(query):
    try:
        conn = pinotdb.connect(
            host='13.229.112.104',
            port=8099,
            path='/query/sql',
            scheme='http',
            timeout=500
        )
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error connecting: {e}")
        return None

# Function to create a metric card
def create_metric_card(label, value):
    st.markdown(f"""
    <div style="background-color: #F4E1D2; padding: 10px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); text-align: center;">
        <h3 style="color: #6D4C41;">{label}</h3>
        <p style="font-size: 24px; font-weight: bold; color: #3E2723;">{value}</p>
    </div>
    """, unsafe_allow_html=True)

# Function to plot average price by coffee type
def plot_average_price_by_coffee_type(df):
    avg_price_df = df.groupby('COFFEE_TYPES')['TOTAL_PRICE'].mean().reset_index()
    fig = px.bar(avg_price_df, x='COFFEE_TYPES', y='TOTAL_PRICE', title='Average Price by Coffee Type', 
                 color='COFFEE_TYPES', color_discrete_sequence=['#8D6E63', '#A1887F', '#D7CCC8', '#5D4037'])
    return fig

# Function to plot order status distribution
def plot_order_status_distribution(df):
    status_df = df['STATUS'].value_counts().reset_index()
    status_df.columns = ['Status', 'Count']
    fig = px.pie(status_df, names='Status', values='Count', title='Order Status Distribution', 
                 color_discrete_sequence=['#8D6E63', '#A1887F', '#D7CCC8'])
    return fig

# Function to plot quantity distribution
def plot_quantity_distribution(df):
    fig = px.histogram(df, x='QUANTITY', title='Quantity Distribution', nbins=10, color_discrete_sequence=['#8D6E63'])
    return fig

# Function to plot order count by coffee type
def plot_order_count_by_coffee_type(df):
    count_df = df.groupby('COFFEE_TYPES')['ORDERID'].count().reset_index()
    fig = px.bar(count_df, x='COFFEE_TYPES', y='ORDERID', title='Order Count by Coffee Type',
                 color_discrete_sequence=['#8D6E63', '#A1887F', '#D7CCC8', '#5D4037'])
    return fig

# Main app
def main():
    st.set_page_config(layout="wide", page_title="Coffee Shop Dashboard", page_icon="☕")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            background-color: #F1F8E9;
        }
        .stButton>button {
            background-color: #8D6E63;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            border: none;
        }
        .stSelectbox {
            color: #6D4C41;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <h1 style='text-align: center; color: #3E2723; padding: 20px 0;'>
            ☕ Coffee Shop Dashboard
        </h1>
    """, unsafe_allow_html=True)

    # Filters in a single row
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_coffee_type = st.selectbox("Coffee Type", 
                                          ['All'] + ['Espresso', 'Cappuccino', 'Latte', 'Americano'])
    with col2:
        selected_date = st.date_input("Select Date", datetime.now())
    with col3:
        show_all_data = st.checkbox("Show All Data", value=True)
        
    selected_date_str = selected_date.strftime('%Y-%m-%d')

    # Set timezone (assuming Bangkok time)
    local_tz = timezone("Asia/Bangkok")
    selected_date_local = local_tz.localize(datetime.combine(selected_date, datetime.min.time()))

    # Construct query with timezone adjustment
    query = f"""
    SELECT ORDERID, USERID, ORDER_TIMESTAMP, COFFEE_TYPES, QUANTITY, TOTAL_PRICE, STATUS
    FROM COFFEECITY
    WHERE ORDER_TIMESTAMP >= '{selected_date_local.strftime('%Y-%m-%d %H:%M:%S')}'
    AND ORDER_TIMESTAMP < '{(selected_date_local + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')}'
    """
    
    # Fetch data based on selected filters
    df = get_data_from_pinot(query)
    
    if df is None or df.empty:
        st.error("No data available for the selected date.")
        return

    df['ORDER_TIMESTAMP'] = pd.to_datetime(df['ORDER_TIMESTAMP'])
    
    # Apply coffee type filter if selected
    if selected_coffee_type != 'All':
        df = df[df['COFFEE_TYPES'] == selected_coffee_type]

    # Key Metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
    with metric_col1:
        total_orders = len(df)
        create_metric_card("Total Orders", total_orders)
        
    with metric_col2:
        total_revenue = df['TOTAL_PRICE'].sum()
        create_metric_card("Total Revenue", f"฿{total_revenue:,.0f}")
            
    with metric_col3:
        avg_order_value = df['TOTAL_PRICE'].mean()
        create_metric_card("Average Order Value", f"฿{avg_order_value:,.0f}")
            
    with metric_col4:
        total_items = df['QUANTITY'].sum()
        create_metric_card("Total Items Sold", total_items)

    # Display charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_average_price_by_coffee_type(df))
        st.plotly_chart(plot_order_status_distribution(df))
            
    with col2:
        st.plotly_chart(plot_quantity_distribution(df))
        st.plotly_chart(plot_order_count_by_coffee_type(df))

    # Show raw data if checkbox is checked
    if show_all_data:
        st.dataframe(df)

if __name__ == "__main__":
    main()
