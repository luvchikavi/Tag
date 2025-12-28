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
from datetime import datetime
from dotenv import load_dotenv

from monday_connector import MondayConnector, load_sample_data_from_excel
from monday_sync import MondaySync, create_sync_instance
from change_logger import ChangeLogger

# Load environment variables
load_dotenv()

# Monday.com API Token (can also be set via .env file)
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN", "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYwMTM4MjQ2OSwiYWFpIjoxMSwidWlkIjo2MTY0NDEzOSwiaWFkIjoiMjAyNS0xMi0yOFQxNTo0MDo1Mi4yMjVaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjM2NzMyOTgsInJnbiI6ImV1YzEifQ.-rwpvYCc9YCxYJ_y5oTgfM8AC9jJvRmw4rjPe1mK9Q4")

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


def load_workplan_dashboard():
    """Load the WorkPlan Dashboard - Overview & Project sheet"""
    excel_path = os.path.join(os.path.dirname(__file__), "WorkPlan 2026.xlsx")
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path, sheet_name='Dashboard - Overview & Project')
        return df
    return pd.DataFrame()


def render_workplan_dashboard():
    """Render the WorkPlan Dashboard tab"""
    st.subheader("WorkPlan 2026 - Dashboard Overview")

    df = load_workplan_dashboard()
    if df.empty:
        st.warning("WorkPlan file not found")
        return

    # Helper function to safely get value
    def get_val(row, col):
        if row < len(df) and col < len(df.columns):
            val = df.iloc[row, col]
            return val if pd.notna(val) else 0
        return 0

    # ============================================
    # SECTION 1: Overall KPIs Summary Cards
    # ============================================
    st.markdown("### 2026 Forecast Overview")

    # Key metrics from 2026 Forecast column
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        units_forecast = get_val(4, 11)
        units_budget = get_val(4, 12)
        st.metric("Units (Forecast)", format_cell_value(units_forecast),
                  delta=f"Budget: {format_cell_value(units_budget)}")

    with col2:
        income_forecast = get_val(7, 11)
        income_budget = get_val(7, 12)
        st.metric("Income (Forecast)", format_cell_value(income_forecast),
                  delta=f"Budget: {format_cell_value(income_budget)}")

    with col3:
        schematics = get_val(14, 12)
        st.metric("Schematics Approval", format_cell_value(schematics), delta="Budget")

    with col4:
        construction = get_val(16, 12)
        st.metric("Construction Start", format_cell_value(construction), delta="Budget")

    st.markdown("---")

    # ============================================
    # SECTION 2: KPI Comparison Table
    # ============================================
    st.markdown("### Key Performance Indicators")

    # Build comprehensive KPI table
    kpi_rows = [
        (4, "Units"),
        (5, "Units (TU)"),
        (7, "Income"),
        (8, "Income (TU)"),
        (10, "€ / Sq. M."),
        (12, "Sales Launch"),
        (13, "Marketing"),
        (14, "Schematics Approval"),
        (15, "Tender"),
        (16, "Construction Start"),
        (17, "Handover"),
        (18, "Deeds"),
    ]

    kpi_data = []
    for row_idx, kpi_name in kpi_rows:
        if row_idx < len(df):
            kpi_data.append({
                'KPI': kpi_name,
                'Month Actual': format_cell_value(get_val(row_idx, 3)),
                'Month Budget': format_cell_value(get_val(row_idx, 4)),
                'Month Gap': str(get_val(row_idx, 5)) if get_val(row_idx, 5) != 0 else '-',
                'YTD Actual': format_cell_value(get_val(row_idx, 7)),
                'YTD Budget': format_cell_value(get_val(row_idx, 8)),
                'YTD Gap': str(get_val(row_idx, 9)) if get_val(row_idx, 9) != 0 else '-',
                '2026 Forecast': format_cell_value(get_val(row_idx, 11)),
                '2026 Budget': format_cell_value(get_val(row_idx, 12)),
            })

    if kpi_data:
        kpi_df = pd.DataFrame(kpi_data)
        st.dataframe(kpi_df, use_container_width=True, hide_index=True, height=450)

    st.markdown("---")

    # ============================================
    # SECTION 3: Project Specific Section
    # ============================================
    project_name = df.iloc[20, 2] if len(df) > 20 and pd.notna(df.iloc[20, 2]) else "Project"
    st.markdown(f"### Project: {project_name}")

    # Project KPIs
    proj_kpi_rows = [
        (25, "Units"),
        (27, "Income"),
        (29, "€ / Sq. M."),
        (31, "Sales Launch"),
        (32, "Marketing"),
        (33, "Schematics Approval"),
        (34, "Tender"),
        (35, "Construction Start"),
        (36, "Construction %"),
        (37, "Handover"),
        (38, "Deeds"),
    ]

    proj_data = []
    for row_idx, kpi_name in proj_kpi_rows:
        if row_idx < len(df):
            proj_data.append({
                'KPI': kpi_name,
                'Month Actual': format_cell_value(get_val(row_idx, 3)),
                'Month Budget': format_cell_value(get_val(row_idx, 4)),
                'Month Gap': str(get_val(row_idx, 5)) if get_val(row_idx, 5) != 0 else '-',
                'YTD Actual': format_cell_value(get_val(row_idx, 7)),
                'YTD Budget': format_cell_value(get_val(row_idx, 8)),
                '2026 Forecast': format_cell_value(get_val(row_idx, 11)),
                '2026 Budget': format_cell_value(get_val(row_idx, 12)),
            })

    if proj_data:
        proj_df = pd.DataFrame(proj_data)
        st.dataframe(proj_df, use_container_width=True, hide_index=True, height=400)

    st.markdown("---")

    # ============================================
    # SECTION 4: Visual Charts
    # ============================================
    st.markdown("### Budget vs Forecast Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # 2026 Budget chart for key milestones
        milestone_data = {
            'Milestone': ['Schematics', 'Tender', 'Construction Start', 'Handover', 'Deeds'],
            'Budget': [
                float(get_val(14, 12)) if get_val(14, 12) else 0,
                float(get_val(15, 12)) if get_val(15, 12) else 0,
                float(get_val(16, 12)) if get_val(16, 12) else 0,
                float(get_val(17, 12)) if get_val(17, 12) else 0,
                float(get_val(18, 12)) if get_val(18, 12) else 0,
            ]
        }
        milestone_df = pd.DataFrame(milestone_data)

        fig = px.bar(
            milestone_df,
            x='Milestone',
            y='Budget',
            title='2026 Budget by Milestone (Units)',
            color='Budget',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Progress pie chart (example with sample data)
        progress_data = {
            'Status': ['Completed', 'In Progress', 'Planned'],
            'Units': [0, 0, 760 + 625 + 371 + 523 + 523]  # Sum of budgets
        }
        fig = px.pie(
            pd.DataFrame(progress_data),
            values='Units',
            names='Status',
            title='Overall Progress Status',
            color_discrete_sequence=['#2ecc71', '#f39c12', '#3498db']
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # SECTION 5: Raw Data Expander
    # ============================================
    with st.expander("View Raw Data"):
        formatted_df = format_dataframe(df)
        st.dataframe(formatted_df, use_container_width=True, hide_index=True, height=400)


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
    total_revenue = pd.to_numeric(projects_df[total_revenue_col[0]], errors='coerce').sum() if total_revenue_col else 0

    # Predicted income
    predicted_col = [c for c in projects_df.columns if 'Predicted' in c]
    predicted_income = pd.to_numeric(projects_df[predicted_col[0]], errors='coerce').sum() if predicted_col else 0

    # Average price
    avg_price_col = [c for c in projects_df.columns if 'Average price' in c]
    avg_price = pd.to_numeric(projects_df[avg_price_col[0]], errors='coerce').mean() if avg_price_col else 0

    # 2025 Targets
    targets_col = [c for c in projects_df.columns if 'Sales targets for 2025' in c]
    targets_2025 = pd.to_numeric(projects_df[targets_col[0]], errors='coerce').sum() if targets_col else 0

    signed_col = [c for c in projects_df.columns if 'CPCV Signed in 2025' in c]
    signed_2025 = pd.to_numeric(projects_df[signed_col[0]], errors='coerce').sum() if signed_col else 0

    year_goal_pct = signed_2025 / targets_2025 if targets_2025 > 0 else 0

    # Sales percentage
    sales_pct = units_sold / total_units if total_units > 0 else 0

    # Display KPIs - Row 1: Units Overview
    st.subheader("Units Overview")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="Total Units", value=format_number(total_units))
    with col2:
        st.metric(label="Units Sold (CPCV)", value=format_number(units_sold), delta=f"{sales_pct:.2%} sold")
    with col3:
        st.metric(label="Blocked", value=format_number(units_blocked))
    with col4:
        st.metric(label="Reserved", value=format_number(units_reserved))
    with col5:
        st.metric(label="Available Inventory", value=format_number(inventory))

    # Row 2: Financial Overview
    st.subheader("Financial Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Revenue (CPCV)", value=format_currency(total_revenue))
    with col2:
        st.metric(label="Predicted Income", value=format_currency(predicted_income))
    with col3:
        st.metric(label="Avg Price per Unit", value=format_currency(avg_price))
    with col4:
        # Average €/m²
        sqm_col = [c for c in projects_df.columns if '€/m²' in c and 'SOLD' in c]
        if sqm_col:
            avg_sqm = pd.to_numeric(projects_df[sqm_col[0]], errors='coerce').mean()
            st.metric(label="Avg €/m² (Sold)", value=format_currency(avg_sqm))

    # Row 3: 2025 Sales Performance
    st.subheader("2025 Sales Performance")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="2025 Sales Target", value=format_number(targets_2025))
    with col2:
        st.metric(label="CPCV Signed in 2025", value=format_number(signed_2025))
    with col3:
        st.metric(label="% of Year Goal", value=f"{year_goal_pct:.2%}")
    with col4:
        remaining = targets_2025 - signed_2025
        st.metric(label="Remaining to Target", value=format_number(remaining))


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
        # Display comprehensive table with all key columns
        st.markdown("#### Units & Inventory")
        units_cols = ['Project', 'Total Units', '# Units CPCV', '% Sold',
                      '#  Blocked', '# Reserved', 'Inventory balance']
        available_units_cols = [c for c in units_cols if c in projects_df.columns]
        units_df = projects_df[available_units_cols].copy()

        # Format columns
        for col in units_df.columns:
            if col == 'Project':
                continue
            elif col == '% Sold':
                units_df[col] = pd.to_numeric(units_df[col], errors='coerce')
                units_df[col] = units_df[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "0%")
            else:
                units_df[col] = pd.to_numeric(units_df[col], errors='coerce')
                units_df[col] = units_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")

        st.dataframe(units_df, use_container_width=True, hide_index=True, height=350)

        # Financial table
        st.markdown("#### Financial Metrics")
        fin_cols = ['Project', 'Total revenue  (from CPCV units)', 'Predicted  Income',
                    'Average price per unit (of the CPCV units)', '€/m²  SOLD/CPCV', 'BP €/M²']
        available_fin_cols = [c for c in fin_cols if c in projects_df.columns]
        fin_df = projects_df[available_fin_cols].copy()

        # Rename columns for display
        col_rename = {
            'Total revenue  (from CPCV units)': 'Revenue (CPCV)',
            'Predicted  Income': 'Predicted Income',
            'Average price per unit (of the CPCV units)': 'Avg Price/Unit',
            '€/m²  SOLD/CPCV': '€/m² Sold',
            'BP €/M²': 'BP €/m²'
        }
        fin_df = fin_df.rename(columns={k: v for k, v in col_rename.items() if k in fin_df.columns})

        # Format financial columns
        for col in fin_df.columns:
            if col != 'Project':
                fin_df[col] = pd.to_numeric(fin_df[col], errors='coerce')
                fin_df[col] = fin_df[col].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "-")

        st.dataframe(fin_df, use_container_width=True, hide_index=True, height=350)

        # 2025 Targets table
        st.markdown("#### 2025 Sales Performance")
        target_cols = ['Project', 'Sales targets for 2025', 'CPCV Signed in 2025', '% of year goals', 'Conclusion']
        available_target_cols = [c for c in target_cols if c in projects_df.columns]
        target_df = projects_df[available_target_cols].copy()

        # Rename and format
        target_rename = {
            'Sales targets for 2025': '2025 Target',
            'CPCV Signed in 2025': 'Signed 2025',
            '% of year goals': '% of Goal',
            'Conclusion': 'Target Date'
        }
        target_df = target_df.rename(columns={k: v for k, v in target_rename.items() if k in target_df.columns})

        for col in target_df.columns:
            if col == 'Project' or col == 'Target Date':
                continue
            elif col == '% of Goal':
                target_df[col] = pd.to_numeric(target_df[col], errors='coerce')
                target_df[col] = target_df[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "-")
            else:
                target_df[col] = pd.to_numeric(target_df[col], errors='coerce')
                target_df[col] = target_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")

        st.dataframe(target_df, use_container_width=True, hide_index=True, height=350)

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


def render_monday_sync_tab():
    """Render the Monday.com sync tab with controls and change log"""
    st.subheader("Monday.com Data Sync")

    # Initialize sync components
    try:
        sync = create_sync_instance(MONDAY_API_TOKEN)
        logger = ChangeLogger(os.path.dirname(__file__))
        sync_available = True
    except Exception as e:
        st.error(f"Sync not available: {e}")
        sync_available = False
        return

    # Sync Status Section
    st.markdown("### Sync Status")

    status = sync.get_sync_status()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        last_sync = status.get("last_sync_time", "Never")
        if last_sync and last_sync != "Never":
            last_sync = last_sync[:19].replace("T", " ")
        st.metric("Last Sync", last_sync if last_sync else "Never")

    with col2:
        success = status.get("last_sync_success")
        status_text = "Success" if success else ("Failed" if success is False else "N/A")
        st.metric("Last Status", status_text)

    with col3:
        st.metric("Changes Applied", status.get("last_sync_changes", 0))

    with col4:
        st.metric("Total Syncs", status.get("total_logged_syncs", 0))

    st.markdown("---")

    # Sync Controls Section
    st.markdown("### Sync Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Preview Changes", use_container_width=True, type="secondary"):
            with st.spinner("Fetching data from Monday.com..."):
                try:
                    changes_df, summary = sync.preview_changes()

                    if changes_df.empty:
                        st.success("No changes detected. Excel is up to date with Monday.com.")
                    else:
                        st.warning(f"Found {len(changes_df)} potential changes")
                        st.session_state["pending_changes"] = changes_df
                        st.session_state["pending_summary"] = summary
                except Exception as e:
                    st.error(f"Error previewing changes: {e}")

    with col2:
        if st.button("Sync Now", use_container_width=True, type="primary"):
            with st.spinner("Syncing data from Monday.com to Excel..."):
                try:
                    summary = sync.sync_data_base_clients(dry_run=False)

                    if summary.get("errors"):
                        st.error(f"Sync completed with errors: {'; '.join(summary['errors'])}")
                    else:
                        st.success(f"Sync completed! {summary['total_changes']} changes applied.")

                    # Clear cached data to reload from updated Excel
                    st.cache_data.clear()

                    # Clear pending changes
                    if "pending_changes" in st.session_state:
                        del st.session_state["pending_changes"]
                    if "pending_summary" in st.session_state:
                        del st.session_state["pending_summary"]

                except Exception as e:
                    st.error(f"Sync failed: {e}")

    with col3:
        if st.button("Clear Change Log", use_container_width=True):
            logger.clear_logs()
            st.success("Change log cleared")
            st.rerun()

    # Show pending changes if available
    if "pending_changes" in st.session_state and not st.session_state["pending_changes"].empty:
        st.markdown("### Pending Changes Preview")
        st.info("These changes will be applied when you click 'Sync Now'")

        pending_df = st.session_state["pending_changes"]
        st.dataframe(pending_df, use_container_width=True, hide_index=True, height=300)

        summary = st.session_state.get("pending_summary", {})
        st.markdown(f"""
        **Summary:**
        - Items checked: {summary.get('total_items_checked', 0)}
        - Sheets to update: {', '.join(summary.get('sheets_processed', []))}
        - Total changes: {summary.get('total_changes', 0)}
        """)

    st.markdown("---")

    # Change Log Section
    st.markdown("### Change Log")

    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        log_limit = st.selectbox("Show last:", [25, 50, 100, 200], index=1)

    # Load and display change log
    changes_df = logger.get_changes_as_dataframe(limit=log_limit)

    if changes_df.empty:
        st.info("No changes logged yet. Run a sync to start tracking changes.")
    else:
        # Add filtering
        with col2:
            sheets = ["All"] + list(changes_df["Sheet"].unique())
            selected_sheet = st.selectbox("Filter by Sheet:", sheets)

        if selected_sheet != "All":
            changes_df = changes_df[changes_df["Sheet"] == selected_sheet]

        st.dataframe(changes_df, use_container_width=True, hide_index=True, height=400)

        # Download option
        csv = changes_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Change Log",
            data=csv,
            file_name=f"change_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    st.markdown("---")

    # Recent Syncs Section
    st.markdown("### Recent Sync Sessions")

    recent_syncs = logger.get_recent_syncs(limit=10)

    if not recent_syncs:
        st.info("No sync sessions recorded yet.")
    else:
        sync_data = []
        for sync_session in recent_syncs:
            sync_data.append({
                "Sync ID": sync_session.get("sync_id", ""),
                "Time": sync_session.get("timestamp", "")[:19].replace("T", " "),
                "Status": "Success" if sync_session.get("success") else "Failed",
                "Changes": sync_session.get("total_changes", 0),
                "Sheets": ", ".join(sync_session.get("sheets_updated", [])),
                "Error": sync_session.get("error_message", "")[:50] if sync_session.get("error_message") else ""
            })

        sync_df = pd.DataFrame(sync_data)
        st.dataframe(sync_df, use_container_width=True, hide_index=True, height=300)

    # Data Source Info
    st.markdown("---")
    st.markdown("### Data Sources")

    with st.expander("Monday.com Boards Being Synced"):
        st.markdown("""
        **Data Base_Clients (Board ID: 1964802890)**
        - Groups: Sales_Horizon, Sal D'Ouro_Coast
        - Fields synced: Status, Broker, Date of CPCV, Client, Nationality

        **Target Excel Sheets:**
        - Sales_Horizon → SAL D'OURO HORIZON (9)
        - Sal D'Ouro_Coast → SAL D'OURO COAST (10)

        **Matching Strategy:**
        - Units are matched by Fraction (A, B, C...) or Unit number
        """)


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

    # Sync Status
    st.sidebar.subheader("Sync Status")
    try:
        sync = create_sync_instance(MONDAY_API_TOKEN)
        status = sync.get_sync_status()
        last_sync = status.get("last_sync_time", "Never")
        if last_sync and last_sync != "Never":
            last_sync = last_sync[:16].replace("T", " ")
        st.sidebar.text(f"Last sync: {last_sync}")
        st.sidebar.text(f"Changes: {status.get('last_sync_changes', 0)}")

        # Quick sync button
        if st.sidebar.button("Quick Sync", use_container_width=True):
            with st.spinner("Syncing..."):
                summary = sync.sync_data_base_clients(dry_run=False)
                if summary.get("errors"):
                    st.sidebar.error("Sync had errors")
                else:
                    st.sidebar.success(f"{summary['total_changes']} changes")
                st.cache_data.clear()
                st.rerun()
    except Exception as e:
        st.sidebar.warning("Sync unavailable")

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
    - Monday.com sync
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
    tab_dashboard, tab_workplan, tab_sheets, tab_sync = st.tabs([
        "📊 Sales Dashboard",
        "📋 WorkPlan 2026",
        "📁 Project Sheets",
        "🔄 Monday.com Sync"
    ])

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

    with tab_workplan:
        render_workplan_dashboard()

    with tab_sheets:
        render_sheet_viewer()

    with tab_sync:
        render_monday_sync_tab()

    # Footer
    st.markdown("---")
    st.caption("Built and Designed by Drishti Consulting | © All Rights Reserved 2025")


if __name__ == "__main__":
    main()
