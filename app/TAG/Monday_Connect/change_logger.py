"""
Change Logger Module
Tracks all data changes from Monday.com syncs
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class ChangeLogger:
    """Logs all changes made during Monday.com to Excel syncs"""

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the change logger

        Args:
            log_dir: Directory to store log files. Defaults to current directory.
        """
        self.log_dir = log_dir or os.path.dirname(__file__)
        self.log_file = os.path.join(self.log_dir, "sync_changelog.json")
        self.current_sync_id = None
        self.changes: List[Dict[str, Any]] = []

    def start_sync(self) -> str:
        """Start a new sync session and return the sync ID"""
        self.current_sync_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.changes = []
        return self.current_sync_id

    def log_change(
        self,
        source_board: str,
        target_sheet: str,
        unit: str,
        field: str,
        old_value: Any,
        new_value: Any,
        monday_item_id: str = "",
        row_index: int = -1
    ):
        """
        Log a single field change

        Args:
            source_board: Name of the Monday.com board
            target_sheet: Name of the Excel sheet being updated
            unit: Unit identifier (e.g., "1", "2", "A")
            field: Field/column name that changed
            old_value: Previous value in Excel
            new_value: New value from Monday.com
            monday_item_id: Monday.com item ID for reference
            row_index: Row index in Excel where change occurred
        """
        change = {
            "timestamp": datetime.now().isoformat(),
            "sync_id": self.current_sync_id,
            "source": source_board,
            "sheet": target_sheet,
            "unit": str(unit),
            "field": field,
            "old_value": self._serialize_value(old_value),
            "new_value": self._serialize_value(new_value),
            "monday_item_id": monday_item_id,
            "row_index": row_index
        }
        self.changes.append(change)

    def _serialize_value(self, value: Any) -> str:
        """Convert value to string for JSON serialization"""
        import numpy as np
        if pd.isna(value) or value is None:
            return ""
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, (np.integer, np.floating)):
            return str(value)
        return str(value)

    def end_sync(self, success: bool = True, error_message: str = "") -> Dict[str, Any]:
        """
        End the current sync session and save the log

        Args:
            success: Whether the sync completed successfully
            error_message: Error message if sync failed

        Returns:
            Summary of the sync session
        """
        summary = self._generate_summary(success, error_message)
        self._save_log(summary)
        return summary

    def _generate_summary(self, success: bool, error_message: str) -> Dict[str, Any]:
        """Generate a summary of all changes in the current sync"""
        sheets_updated = list(set(c["sheet"] for c in self.changes))
        fields_changed = {}
        for change in self.changes:
            field = change["field"]
            fields_changed[field] = fields_changed.get(field, 0) + 1

        return {
            "sync_id": self.current_sync_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error_message": error_message,
            "total_changes": len(self.changes),
            "sheets_updated": sheets_updated,
            "fields_changed": fields_changed,
            "changes": self.changes
        }

    def _save_log(self, summary: Dict[str, Any]):
        """Save the sync log to file"""
        import numpy as np

        # Custom JSON encoder for numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.int64)):
                    return int(obj)
                if isinstance(obj, (np.floating, np.float64)):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)

        # Load existing logs
        existing_logs = self.load_all_logs()

        # Add new sync
        existing_logs.append(summary)

        # Keep only last 100 syncs to prevent file from growing too large
        if len(existing_logs) > 100:
            existing_logs = existing_logs[-100:]

        # Save to file with numpy-safe encoder
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    def load_all_logs(self) -> List[Dict[str, Any]]:
        """Load all sync logs from file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    def get_recent_syncs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent sync summaries"""
        logs = self.load_all_logs()
        return logs[-limit:][::-1]  # Return most recent first

    def get_sync_details(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific sync session"""
        logs = self.load_all_logs()
        for log in logs:
            if log.get("sync_id") == sync_id:
                return log
        return None

    def get_changes_for_sheet(self, sheet_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all recent changes for a specific sheet"""
        logs = self.load_all_logs()
        changes = []
        for log in reversed(logs):
            for change in log.get("changes", []):
                if change.get("sheet") == sheet_name:
                    changes.append(change)
                    if len(changes) >= limit:
                        return changes
        return changes

    def get_changes_as_dataframe(self, limit: int = 100) -> pd.DataFrame:
        """Get recent changes as a pandas DataFrame for display"""
        logs = self.load_all_logs()
        all_changes = []

        for log in reversed(logs):
            for change in log.get("changes", []):
                all_changes.append({
                    "Timestamp": change.get("timestamp", "")[:19].replace("T", " "),
                    "Sheet": change.get("sheet", ""),
                    "Unit": change.get("unit", ""),
                    "Field": change.get("field", ""),
                    "Old Value": change.get("old_value", ""),
                    "New Value": change.get("new_value", ""),
                    "Monday ID": change.get("monday_item_id", "")
                })
                if len(all_changes) >= limit:
                    break
            if len(all_changes) >= limit:
                break

        return pd.DataFrame(all_changes) if all_changes else pd.DataFrame()

    def clear_logs(self):
        """Clear all sync logs"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
