"""
Unit Tests for Manifest Parser (Excel & CSV)
"""
import io
import pandas as pd
from app.services.excel_parser import ManifestParser


def test_parse_valid_csv():
    csv_data = """id,address,parcel_weight,service_time,window_start,window_end
1,"Andheri East, Mumbai",25,15,08:00:00,10:00:00
2,"Bandra West, Mumbai",15,10,09:00:00,12:00:00
3,"Dadar West, Mumbai",20,12,14:00:00,16:00:00
"""
    orders, errors, warnings = ManifestParser.parse_file(csv_data.encode("utf-8"), "manifest.csv")
    assert len(errors) == 0
    assert len(orders) == 3
    assert orders[0]["external_order_id"] == "1"
    assert orders[0]["raw_address"] == "Andheri East, Mumbai"
    assert orders[0]["parcel_weight_kg"] == 25.0
    assert orders[0]["window_start_minutes"] == 480  # 08:00
    assert orders[0]["window_end_minutes"] == 600    # 10:00


def test_parse_valid_excel():
    df = pd.DataFrame({
        "order_id": ["ORD-101", "ORD-102"],
        "delivery_address": ["Khar West, Mumbai", "Powai, Mumbai"],
        "weight_kg": [18.5, 30.0],
        "slot_start": ["10:30", "14:00"],
        "slot_end": ["12:30", "17:00"]
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    orders, errors, warnings = ManifestParser.parse_file(buffer.getvalue(), "manifest.xlsx")

    assert len(errors) == 0
    assert len(orders) == 2
    assert orders[0]["external_order_id"] == "ORD-101"
    assert orders[0]["parcel_weight_kg"] == 18.5
    assert orders[0]["window_start_minutes"] == 630  # 10:30
    assert orders[0]["window_end_minutes"] == 750    # 12:30


def test_parse_missing_address_and_coordinates():
    csv_data = """id,parcel_weight
1,25
"""
    orders, errors, warnings = ManifestParser.parse_file(csv_data.encode("utf-8"), "bad_manifest.csv")
    assert len(errors) > 0
    assert len(orders) == 0


def test_parse_with_pre_geocoded_coordinates():
    csv_data = """id,latitude,longitude,parcel_weight
1,19.1193,72.8450,12
2,19.0616,72.8360,15
"""
    orders, errors, warnings = ManifestParser.parse_file(csv_data.encode("utf-8"), "coords_manifest.csv")
    assert len(errors) == 0
    assert len(orders) == 2
    assert orders[0]["latitude"] == 19.1193
    assert orders[0]["longitude"] == 72.8450
