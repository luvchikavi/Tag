"""
Sales Dashboard - Monday.com Integration
Construction & Development Company - Portugal
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from dotenv import load_dotenv

from monday_connector import MondayConnector, load_sample_data_from_excel

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        max-width: 95%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    section[data-testid="stSidebar"] {
        width: 280px !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #1f77b4;
    }
    div[data-testid="stMetricDelta"] > div {
        color: #2ecc71;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    h2, h3 {
        color: #2c3e50;
    }
    .stSelectbox label {
        color: #1f77b4;
        font-weight: 600;
    }
    [data-testid="stDataFrame"] {
        width: 100% !important;
    }
    [data-testid="stDataFrame"] > div {
        width: 100% !important;
        overflow-x: auto !important;
    }
    iframe[title="streamlit_dataframe.dataframe"] {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)


def format_currency(value):
    """Format number as Euro currency"""
    if pd.isna(value) or value == 0:
        return "€0"
    return f"€{value:,.0f}"


def format_percentage(value):
    """Format number as percentage"""
    if pd.isna(value):
        return "0%"
    return f"{value:.2%}"


def format_number(value):
    """Format number with comma separators and max 2 decimal places"""
    if pd.isna(value):
        return "0"
    if isinstance(value, float):
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"
    return f"{value:,}"


def format_cell_value(value):
    """Format a cell value for display in dataframes"""
    if pd.isna(value):
        return ""
    # Handle numeric types (including numpy)
    if isinstance(value, (int, float, np.integer, np.floating)):
        num_val = float(value)
        # Check if it's effectively an integer
        if num_val == int(num_val):
            return f"{int(num_val):,}"
        else:
            return f"{num_val:,.2f}"
    return str(value)


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format all numeric values in a dataframe for display"""
    formatted_df = df.copy()
    for col in formatted_df.columns:
        formatted_df[col] = formatted_df[col].apply(
            lambda x: format_cell_value(x) if isinstance(x, (int, float, np.integer, np.floating)) else (str(x) if pd.notna(x) else "")
        )
    return formatted_df


def load_data(use_monday: bool = False):
    """Load data from Monday.com or Excel file"""
    if use_monday and os.getenv("MONDAY_API_TOKEN"):
        try:
            connector = MondayConnector()
            board_id = os.getenv("MONDAY_BOARD_ID")
            if board_id:
                return connector.get_board_data_as_dataframe(board_id)
        except Exception as e:
            st.error(f"Error connecting to Monday.com: {e}")

    # Fall back to Excel file
    excel_path = os.path.join(os.path.dirname(__file__), "Sales.xlsx")
    if os.path.exists(excel_path):
        return load_sample_data_from_excel(excel_path)
    return None


def get_excel_sheets():
    """Get list of all sheets in the Excel file"""
    excel_path = os.path.join(os.path.dirname(__file__), "Sales.xlsx")
    if os.path.exists(excel_path):
        xl = pd.ExcelFile(excel_path)
        return xl.sheet_names
    return []


def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    """Load data from a specific Excel sheet"""
    excel_path = os.path.join(os.path.dirname(__file__), "Sales.xlsx")
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        # Clean column names
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        return df
    return pd.DataFrame()


def render_sheet_viewer():
    """Render the Excel sheet viewer section"""
    st.subheader("Project Details - Excel Sheets")

    sheets = get_excel_sheets()
    if not sheets:
        st.warning("No Excel sheets found")
        return

    # Sheet selector
    selected_sheet = st.selectbox(
        "Select a sheet to view:",
        sheets,
        index=0
    )

    if selected_sheet:
        with st.spinner(f"Loading {selected_sheet}..."):
            df = load_sheet_data(selected_sheet)

        if df.empty:
            st.warning("No data in this sheet")
            return

        # Show sheet info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", format_number(len(df)))
        with col2:
            st.metric("Columns", format_number(len(df.columns)))
        with col3:
            # Count non-empty cells
            non_empty = df.notna().sum().sum()
            st.metric("Data Points", format_number(non_empty))

        # Filter options for project sheets (not the main sales report)
        if selected_sheet != "sales report - general":
            st.markdown("#### Filters")

            filter_cols = st.columns(3)

            # Status filter if available
            status_col = None
            for col in df.columns:
                if 'status' in col.lower() or 'estado' in col.lower():
                    status_col = col
                    break

            filtered_df = df.copy()

            with filter_cols[0]:
                if status_col and status_col in df.columns:
                    statuses = df[status_col].dropna().unique().tolist()
                    if statuses:
                        selected_status = st.multiselect(
                            "Filter by Status:",
                            options=statuses,
                            default=[]
                        )
                        if selected_status:
                            filtered_df = filtered_df[filtered_df[status_col].isin(selected_status)]

            with filter_cols[1]:
                if 'Floor' in df.columns:
                    floors = df['Floor'].dropna().unique().tolist()
                    if floors:
                        # Convert all to string for sorting to avoid type errors
                        floors_str = sorted([str(f) for f in floors if pd.notna(f)])
                        selected_floors = st.multiselect(
                            "Filter by Floor:",
                            options=floors_str,
                            default=[]
                        )
                        if selected_floors:
                            filtered_df = filtered_df[filtered_df['Floor'].astype(str).isin(selected_floors)]

            with filter_cols[2]:
                if 'Layout' in df.columns:
                    layouts = df['Layout'].dropna().unique().tolist()
                    if layouts:
                        # Convert all to string for sorting to avoid type errors
                        layouts_str = sorted([str(l) for l in layouts if pd.notna(l)])
                        selected_layouts = st.multiselect(
                            "Filter by Layout:",
                            options=layouts_str,
                            default=[]
                        )
                        if selected_layouts:
                            filtered_df = filtered_df[filtered_df['Layout'].astype(str).isin(selected_layouts)]

            # Show filtered count
            if len(filtered_df) != len(df):
                st.info(f"Showing {len(filtered_df)} of {len(df)} rows")

            df = filtered_df

        # Format all columns for display
        display_df = format_dataframe(df)

        # Display the dataframe
        st.markdown("#### Data")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

        # Download option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"{selected_sheet.replace(' ', '_')}.csv",
            mime="text/csv"
        )


def render_kpi_cards(data: dict):
    """Render main KPI cards at the top of the dashboard"""
    projects_df = data.get('projects', pd.DataFrame())

    if projects_df.empty:
        st.warning("No project data available")
        return

    # Calculate KPIs
    total_units = pd.to_numeric(projects_df['Total Units'], errors='coerce').sum()
    units_sold = pd.to_numeric(projects_df['# Units CPCV'], errors='coerce').sum()
    units_blocked = pd.to_numeric(projects_df['#  Blocked'], errors='coerce').sum()
    units_reserved = pd.to_numeric(projects_df['# Reserved'], errors='coerce').sum()
    inventory = pd.to_numeric(projects_df['Inventory balance'], errors='coerce').sum()

    # Revenue
    total_revenue_col = [c for c in projects_df.columns if 'Total revenue' in c]
    if total_revenue_col:
        total_revenue = pd.to_numeric(projects_df[total_revenue_col[0]], errors='coerce').sum()
    else:
        total_revenue = 0

    # Predicted income
    predicted_col = [c for c in projects_df.columns if 'Predicted' in c]
    if predicted_col:
        predicted_income = pd.to_numeric(projects_df[predicted_col[0]], errors='coerce').sum()
    else:
        predicted_income = 0

    # Sales percentage
    sales_pct = units_sold / total_units if total_units > 0 else 0

    # Display KPIs
    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Units",
            value=format_number(total_units),
            delta=None
        )

    with col2:
        st.metric(
            label="Units Sold (CPCV)",
            value=format_number(units_sold),
            delta=f"{sales_pct:.2%} sold"
        )

    with col3:
        st.metric(
            label="Blocked",
            value=format_number(units_blocked)
        )

    with col4:
        st.metric(
            label="Reserved",
            value=format_number(units_reserved)
        )

    with col5:
        st.metric(
            label="Available Inventory",
            value=format_number(inventory)
        )

    # Second row of KPIs
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Revenue (CPCV)",
            value=format_currency(total_revenue)
        )

    with col2:
        st.metric(
            label="Predicted Income",
            value=format_currency(predicted_income)
        )

    with col3:
        avg_price_col = [c for c in projects_df.columns if 'Average price' in c]
        if avg_price_col:
            avg_prices = pd.to_numeric(projects_df[avg_price_col[0]], errors='coerce')
            avg_price = avg_prices.mean()
            st.metric(
                label="Avg Price per Unit",
                value=format_currency(avg_price)
            )


def render_project_overview(data: dict):
    """Render project overview table and charts"""
    projects_df = data.get('projects', pd.DataFrame())

    if projects_df.empty:
        st.warning("No project data available")
        return

    st.subheader("Project Overview")

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Table View", "Sales Progress", "Revenue Analysis"])

    with tab1:
        # Display clean table with formatted numbers
        display_cols = ['Project', 'Total Units', '# Units CPCV', '% Sold',
                        '#  Blocked', '# Reserved', 'Inventory balance']
        available_display_cols = [c for c in display_cols if c in projects_df.columns]

        display_df = projects_df[available_display_cols].copy()

        # Format all numeric columns
        for col in display_df.columns:
            if col == 'Project':
                continue
            elif col == '% Sold':
                display_df[col] = pd.to_numeric(display_df[col], errors='coerce')
                display_df[col] = display_df[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "0%")
            else:
                display_df[col] = pd.to_numeric(display_df[col], errors='coerce')
                display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

    with tab2:
        # Sales progress chart
        chart_df = projects_df[['Project', 'Total Units', '# Units CPCV', '# Reserved', 'Inventory balance']].copy()
        for col in ['Total Units', '# Units CPCV', '# Reserved', 'Inventory balance']:
            if col in chart_df.columns:
                chart_df[col] = pd.to_numeric(chart_df[col], errors='coerce').fillna(0)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Sold (CPCV)',
            x=chart_df['Project'],
            y=chart_df['# Units CPCV'],
            marker_color='#2ecc71'
        ))

        fig.add_trace(go.Bar(
            name='Reserved',
            x=chart_df['Project'],
            y=chart_df['# Reserved'],
            marker_color='#f39c12'
        ))

        fig.add_trace(go.Bar(
            name='Available',
            x=chart_df['Project'],
            y=chart_df['Inventory balance'],
            marker_color='#3498db'
        ))

        fig.update_layout(
            barmode='stack',
            title='Units Status by Project',
            xaxis_title='Project',
            yaxis_title='Number of Units',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Revenue analysis
        revenue_col = [c for c in projects_df.columns if 'Total revenue' in c]
        predicted_col = [c for c in projects_df.columns if 'Predicted' in c]
        avg_price_col = [c for c in projects_df.columns if 'Average price' in c]

        if revenue_col and predicted_col:
            rev_df = projects_df[['Project'] + revenue_col + predicted_col].copy()
            rev_df.columns = ['Project', 'Current Revenue', 'Predicted Income']

            for col in ['Current Revenue', 'Predicted Income']:
                rev_df[col] = pd.to_numeric(rev_df[col], errors='coerce').fillna(0)

            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Current Revenue',
                x=rev_df['Project'],
                y=rev_df['Current Revenue'],
                marker_color='#27ae60',
                text=[f"€{v:,.0f}" for v in rev_df['Current Revenue']],
                textposition='outside'
            ))

            fig.add_trace(go.Bar(
                name='Predicted Income',
                x=rev_df['Project'],
                y=rev_df['Predicted Income'],
                marker_color='#95a5a6'
            ))

            fig.update_layout(
                barmode='group',
                title='Revenue vs Predicted Income by Project',
                xaxis_title='Project',
                yaxis_title='Amount (€)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

            # Revenue table with formatted numbers
            st.markdown("#### Revenue Details")
            rev_table = rev_df.copy()
            rev_table['Current Revenue'] = rev_table['Current Revenue'].apply(lambda x: f"€{x:,.0f}")
            rev_table['Predicted Income'] = rev_table['Predicted Income'].apply(lambda x: f"€{x:,.0f}")
            st.dataframe(rev_table, use_container_width=True, hide_index=True, height=300)


def render_monthly_sales(data: dict):
    """Render monthly sales tracking section"""
    monthly_df = data.get('monthly', pd.DataFrame())

    if monthly_df.empty:
        st.info("Monthly sales data not available")
        return

    st.subheader("Monthly Sales Tracking (CPCV 2025)")

    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']

    available_months = [m for m in months if m in monthly_df.columns]

    if not available_months:
        st.warning("No monthly data columns found")
        return

    tab1, tab2 = st.tabs(["Monthly Trend", "Project Breakdown"])

    with tab1:
        # Calculate monthly totals
        monthly_totals = []
        for month in available_months:
            total = pd.to_numeric(monthly_df[month], errors='coerce').sum()
            monthly_totals.append({'Month': month, 'Units Sold': total})

        totals_df = pd.DataFrame(monthly_totals)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=totals_df['Month'],
            y=totals_df['Units Sold'],
            mode='lines+markers+text',
            text=totals_df['Units Sold'].astype(int),
            textposition='top center',
            line=dict(color='#3498db', width=3),
            marker=dict(size=10)
        ))

        fig.update_layout(
            title='Monthly Sales Trend 2025',
            xaxis_title='Month',
            yaxis_title='Units Sold',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total YTD", format_number(totals_df['Units Sold'].sum()))
        with col2:
            st.metric("Best Month", totals_df.loc[totals_df['Units Sold'].idxmax(), 'Month'])
        with col3:
            st.metric("Best Month Sales", format_number(totals_df['Units Sold'].max()))
        with col4:
            st.metric("Monthly Average", format_number(totals_df['Units Sold'].mean()))

    with tab2:
        # Heatmap of sales by project and month
        heatmap_df = monthly_df.set_index('Project')[available_months]
        for col in heatmap_df.columns:
            heatmap_df[col] = pd.to_numeric(heatmap_df[col], errors='coerce').fillna(0)

        fig = px.imshow(
            heatmap_df,
            labels=dict(x="Month", y="Project", color="Units"),
            color_continuous_scale='Blues',
            aspect='auto'
        )

        fig.update_layout(
            title='Sales Heatmap by Project and Month',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # Monthly table with formatted numbers
        st.markdown("#### Monthly Sales Table")
        monthly_table = monthly_df.copy()
        for col in available_months:
            if col in monthly_table.columns:
                monthly_table[col] = pd.to_numeric(monthly_table[col], errors='coerce').fillna(0)
                monthly_table[col] = monthly_table[col].apply(lambda x: f"{int(x):,}" if x > 0 else "-")
        st.dataframe(monthly_table, use_container_width=True, hide_index=True, height=400)


def render_broker_performance(data: dict):
    """Render broker performance section"""
    broker_df = data.get('brokers', pd.DataFrame())

    if broker_df.empty:
        st.info("Broker data not available")
        return

    st.subheader("Broker Performance")

    brokers = ['GlobalKey', 'Tranquildiscovery', 'Empril', 'ChaveNova', 'JLL', 'Réplica', 'Venda Directa']
    available_brokers = [b for b in brokers if b in broker_df.columns]

    if not available_brokers:
        st.warning("No broker data columns found")
        return

    tab1, tab2 = st.tabs(["Broker Rankings", "Broker by Project"])

    with tab1:
        # Calculate broker totals
        broker_totals = []
        for broker in available_brokers:
            total = pd.to_numeric(broker_df[broker], errors='coerce').sum()
            broker_totals.append({'Broker': broker, 'Total Sales': total})

        broker_totals_df = pd.DataFrame(broker_totals)
        broker_totals_df = broker_totals_df.sort_values('Total Sales', ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=broker_totals_df['Broker'],
            x=broker_totals_df['Total Sales'],
            orientation='h',
            marker_color='#9b59b6',
            text=broker_totals_df['Total Sales'].astype(int),
            textposition='outside'
        ))

        fig.update_layout(
            title='Total Sales by Broker',
            xaxis_title='Units Sold',
            yaxis_title='Broker',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Pie chart
        col1, col2 = st.columns(2)

        with col1:
            fig_pie = px.pie(
                broker_totals_df,
                values='Total Sales',
                names='Broker',
                title='Market Share by Broker'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Top broker metrics
            top_broker = broker_totals_df.iloc[-1]
            total_all = broker_totals_df['Total Sales'].sum()

            st.metric("Top Broker", top_broker['Broker'])
            st.metric("Top Broker Sales", format_number(top_broker['Total Sales']))
            st.metric("Top Broker Share", f"{top_broker['Total Sales']/total_all:.2%}")

    with tab2:
        # Broker by project table with formatted numbers
        display_df = broker_df.copy()
        for col in available_brokers:
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').fillna(0)
            display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x != 0 else "-")

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)


def render_sidebar():
    """Render sidebar with settings and filters"""
    st.sidebar.title("Sales Dashboard")
    st.sidebar.markdown("---")

    # Refresh data button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")

    # Data source selection
    st.sidebar.subheader("Data Source")
    use_monday = st.sidebar.checkbox("Use Monday.com API", value=False)

    if use_monday:
        if not os.getenv("MONDAY_API_TOKEN"):
            st.sidebar.warning("API token not configured. Add MONDAY_API_TOKEN to .env file")
        else:
            st.sidebar.success("API token configured")

    st.sidebar.markdown("---")

    # Connection status
    st.sidebar.subheader("Connection Status")
    if use_monday and os.getenv("MONDAY_API_TOKEN"):
        try:
            connector = MondayConnector()
            if connector.test_connection():
                st.sidebar.success("Connected to Monday.com")
                user_info = connector.get_user_info()
                st.sidebar.text(f"User: {user_info.get('name', 'Unknown')}")
            else:
                st.sidebar.error("Connection failed")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)[:50]}")
    else:
        st.sidebar.info("Using Excel data")

    st.sidebar.markdown("---")

    # Info section
    st.sidebar.subheader("About")
    st.sidebar.markdown("""
    **Sales Dashboard**

    Real estate development sales tracking for Portuguese construction company.

    Data includes:
    - Project overview
    - Monthly sales tracking
    - Broker performance
    """)

    return use_monday


def main():
    """Main application entry point"""
    # Header
    st.markdown('<h1 class="main-header">Sales Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Real Estate Development - Portugal")
    st.markdown("---")

    # Sidebar
    use_monday = render_sidebar()

    # Main tabs
    tab_dashboard, tab_sheets = st.tabs(["📊 Sales Dashboard", "📁 Project Sheets"])

    with tab_dashboard:
        # Load data
        with st.spinner("Loading data..."):
            data = load_data(use_monday)

        if data is None:
            st.error("Could not load data. Please check the data source configuration.")
            return

        # Render dashboard sections
        render_kpi_cards(data)
        st.markdown("---")

        render_project_overview(data)
        st.markdown("---")

        render_monthly_sales(data)
        st.markdown("---")

        render_broker_performance(data)

    with tab_sheets:
        render_sheet_viewer()

    # Footer
    st.markdown("---")
    st.caption("Built and Designed by Drishti Consulting | © All Rights Reserved 2025")


if __name__ == "__main__":
    main()
