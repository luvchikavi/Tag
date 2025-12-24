"""
Monday.com API Connector Module
Handles all communication with Monday.com API
"""

import requests
import pandas as pd
from typing import Optional, Dict, List, Any
import os
from dotenv import load_dotenv

load_dotenv()


class MondayConnector:
    """Connector class for Monday.com API"""

    API_URL = "https://api.monday.com/v2"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the Monday.com connector

        Args:
            api_token: Monday.com API token. If not provided, reads from MONDAY_API_TOKEN env var
        """
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")
        if not self.api_token:
            raise ValueError("API token is required. Set MONDAY_API_TOKEN env variable or pass api_token parameter.")

        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against Monday.com API

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            JSON response from the API
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.API_URL,
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_boards(self) -> List[Dict]:
        """Get all boards accessible to the user"""
        query = """
        query {
            boards(limit: 100) {
                id
                name
                description
                state
                workspace {
                    id
                    name
                }
            }
        }
        """
        result = self._execute_query(query)
        return result.get("data", {}).get("boards", [])

    def get_board_columns(self, board_id: str) -> List[Dict]:
        """Get all columns for a specific board"""
        query = """
        query($boardId: [ID!]) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                    settings_str
                }
            }
        }
        """
        result = self._execute_query(query, {"boardId": [board_id]})
        boards = result.get("data", {}).get("boards", [])
        if boards:
            return boards[0].get("columns", [])
        return []

    def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict]:
        """
        Get all items from a board

        Args:
            board_id: The ID of the board
            limit: Maximum number of items to retrieve

        Returns:
            List of items with their column values
        """
        query = """
        query($boardId: [ID!], $limit: Int) {
            boards(ids: $boardId) {
                items_page(limit: $limit) {
                    items {
                        id
                        name
                        group {
                            id
                            title
                        }
                        column_values {
                            id
                            type
                            text
                            value
                        }
                    }
                }
            }
        }
        """
        result = self._execute_query(query, {"boardId": [board_id], "limit": limit})
        boards = result.get("data", {}).get("boards", [])
        if boards:
            return boards[0].get("items_page", {}).get("items", [])
        return []

    def get_board_data_as_dataframe(self, board_id: str, column_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Get board data and convert to pandas DataFrame

        Args:
            board_id: The ID of the board
            column_mapping: Optional mapping of Monday column IDs to desired column names

        Returns:
            DataFrame with board data
        """
        items = self.get_board_items(board_id)

        if not items:
            return pd.DataFrame()

        rows = []
        for item in items:
            row = {
                "id": item["id"],
                "name": item["name"],
                "group": item.get("group", {}).get("title", "")
            }

            for col_value in item.get("column_values", []):
                col_id = col_value["id"]
                col_name = column_mapping.get(col_id, col_id) if column_mapping else col_id
                row[col_name] = col_value.get("text", "")

            rows.append(row)

        return pd.DataFrame(rows)

    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            query = "query { me { id name } }"
            result = self._execute_query(query)
            return "data" in result and "me" in result["data"]
        except Exception:
            return False

    def get_user_info(self) -> Dict:
        """Get current user information"""
        query = """
        query {
            me {
                id
                name
                email
                account {
                    id
                    name
                }
            }
        }
        """
        result = self._execute_query(query)
        return result.get("data", {}).get("me", {})


def load_sample_data_from_excel(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Load sample data from Excel file for development/demo purposes

    Args:
        file_path: Path to the Sales.xlsx file

    Returns:
        Dictionary with DataFrames for different sections
    """
    # Read the main data
    df = pd.read_excel(file_path)

    # Clean column names - strip whitespace and normalize newlines
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]

    # Project overview data (rows 0-17)
    project_columns = [
        'Project', 'Total Units', '# Units CPCV', '% Sold', '#  Blocked',
        '# Reserved', 'Inventory balance', 'Total revenue  (from CPCV units)',
        'Predicted  Income', 'Average price per unit (of the CPCV units)',
        '€/m²  SOLD/CPCV', '€/m²  Blocked', '€/m² Reserved', 'BP €/M²',
        'Conclusion', 'Sales targets for 2025', 'CPCV Signed in 2025', '% of year goals'
    ]

    # Filter columns that exist
    available_cols = [c for c in project_columns if c in df.columns]
    projects_df = df[available_cols].iloc[:18].dropna(subset=['Project']).copy()

    # Clean column names for output
    projects_df.columns = [c.strip() for c in projects_df.columns]

    # Monthly sales data (starting from row 26)
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']

    # Extract monthly data - rows 27-43 contain monthly breakdown by project
    monthly_data = []
    for idx in range(27, 44):
        if idx < len(df) and pd.notna(df.iloc[idx]['Project']):
            project_name = df.iloc[idx]['Project']
            if project_name != 'TOTAL P/ MONTH':  # Skip total row
                row_data = {'Project': project_name}
                for i, month in enumerate(months):
                    col_idx = i + 1
                    if col_idx < len(df.columns):
                        val = df.iloc[idx].iloc[col_idx]
                        row_data[month] = val if pd.notna(val) else 0
                monthly_data.append(row_data)

    monthly_df = pd.DataFrame(monthly_data)

    # Broker data (starting from row 49)
    broker_data = []
    brokers = ['GlobalKey', 'Tranquildiscovery', 'Empril', 'ChaveNova', 'JLL', 'Réplica', 'Venda Directa']

    for idx in range(50, 65):
        if idx < len(df) and pd.notna(df.iloc[idx]['Project']):
            row_data = {'Project': df.iloc[idx]['Project']}
            for i, broker in enumerate(brokers):
                col_idx = i + 1
                if col_idx < len(df.columns):
                    row_data[broker] = df.iloc[idx].iloc[col_idx]
            broker_data.append(row_data)

    broker_df = pd.DataFrame(broker_data)

    return {
        'projects': projects_df,
        'monthly': monthly_df,
        'brokers': broker_df
    }
