import pytest
import os
import pandas as pd
from src.data_loader import DataLoader

def test_load_csv(tmp_path):
    # Create a dummy CSV
    data = {
        "Marketplace": ["US", "US"],
        "Zip Code": ["10001", "90210"],
        "ASIN": ["B001", "B002"],
        "Keyword": ["key1", "key2"]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_job.csv"
    df.to_csv(file_path, index=False)

    tasks = DataLoader.load_file(str(file_path))
    assert len(tasks) == 2
    assert tasks[0]["zip_code"] == "10001"
    assert tasks[1]["keyword"] == "key2"

def test_load_excel(tmp_path):
    # Create a dummy Excel
    data = {
        "Marketplace": ["US"],
        "Zip Code": ["10001"],
        "ASIN": ["B001"],
        "Keyword": ["key1"]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_job.xlsx"
    df.to_excel(file_path, index=False)

    tasks = DataLoader.load_file(str(file_path))
    assert len(tasks) == 1
    assert tasks[0]["asin"] == "B001"

def test_missing_columns(tmp_path):
    # Missing Zip Code
    data = {
        "Marketplace": ["US"],
        "ASIN": ["B001"],
        "Keyword": ["key1"]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "bad_job.csv"
    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        DataLoader.load_file(str(file_path))
