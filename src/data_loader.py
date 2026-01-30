import pandas as pd
import os
from typing import List, Dict, Optional

class DataLoader:
    REQUIRED_COLUMNS = ["Marketplace", "Zip Code", "ASIN", "Keyword"]

    @staticmethod
    def load_file(file_path: str) -> List[Dict]:
        """
        Loads a job file (CSV or Excel) and returns a list of dictionaries.
        Each dictionary represents a task row.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path, dtype=str)
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path, dtype=str)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

        # Normalize column names (strip whitespace, title case)
        df.columns = [c.strip() for c in df.columns]

        # Check missing columns
        missing_cols = [col for col in DataLoader.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Drop rows where any required field is empty
        df = df.dropna(subset=DataLoader.REQUIRED_COLUMNS)

        # Convert to list of dicts
        tasks = df[DataLoader.REQUIRED_COLUMNS].to_dict('records')

        # Clean data
        cleaned_tasks = []
        for task in tasks:
            cleaned_tasks.append({
                "marketplace": str(task["Marketplace"]).strip(),
                "zip_code": str(task["Zip Code"]).strip(),
                "asin": str(task["ASIN"]).strip(),
                "keyword": str(task["Keyword"]).strip()
            })

        return cleaned_tasks
