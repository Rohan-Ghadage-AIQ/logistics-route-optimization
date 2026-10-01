"""
Robust Excel & CSV Manifest Parser
Extracts order items with schema normalization, robust type casting, and validation errors.
"""
from typing import List, Dict, Any, Tuple, Optional
import io
import pandas as pd
from app.utils.time_utils import parse_time_to_minutes
from app.utils.logger import logger


# Mapping of canonical internal fields to potential variations in user spreadsheets
COLUMN_ALIASES: Dict[str, List[str]] = {
    "external_order_id": [
        "id", "order_id", "order id", "station_id", "station id", 
        "order_no", "order no", "tracking_no", "shipment_id", "delivery_id"
    ],
    "raw_address": [
        "address", "delivery_address", "delivery address", "destination", 
        "location", "customer_address", "drop_location", "full_address"
    ],
    "parcel_weight_kg": [
        "parcel_weight", "parcel weight", "weight", "weight_kg", "weight (kg)", 
        "demand", "quantity", "load", "kg"
    ],
    "service_time_minutes": [
        "service_time", "service time", "duration", "service_duration", 
        "stop_time", "service_time_min", "stop_duration"
    ],
    "window_start": [
        "window_start", "window start", "delivery_window_start", "time_window_start",
        "slot_start", "start_time", "earliest_time", "opening_time", "from_time"
    ],
    "window_end": [
        "window_end", "window end", "delivery_window_end", "time_window_end",
        "slot_end", "end_time", "latest_time", "deadline", "to_time"
    ],
    "latitude": [
        "latitude", "lat", "y", "drop_latitude", "lat_deg"
    ],
    "longitude": [
        "longitude", "lon", "lng", "x", "drop_longitude", "lon_deg"
    ]
}


class ManifestParser:
    """Parses, validates, and normalizes Excel/CSV logistics manifests."""

    @staticmethod
    def _find_column_name(df_columns: List[str], target_field: str) -> Optional[str]:
        """Finds matching column in DataFrame using case-insensitive alias lookup."""
        normalized_cols = {col.strip().lower(): col for col in df_columns}
        for alias in COLUMN_ALIASES.get(target_field, []):
            if alias.lower() in normalized_cols:
                return normalized_cols[alias.lower()]
        return None

    @classmethod
    def parse_file(cls, file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """
        Parses binary file bytes into normalized list of order dictionaries.
        Returns: (parsed_orders, errors, warnings)
        """
        errors: List[str] = []
        warnings: List[str] = []
        parsed_orders: List[Dict[str, Any]] = []

        # Step 1: Read into pandas DataFrame
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                return [], [f"Unsupported file format '{filename}'. Please upload a CSV or Excel (.xlsx/.xls) file."], []
        except Exception as e:
            return [], [f"Failed to read file: {str(e)}"], []

        if df.empty:
            return [], ["The uploaded manifest file is completely empty."], []

        # Drop completely empty rows
        df = df.dropna(how="all")

        # Step 2: Map columns
        col_id = cls._find_column_name(df.columns.tolist(), "external_order_id")
        col_address = cls._find_column_name(df.columns.tolist(), "raw_address")
        col_weight = cls._find_column_name(df.columns.tolist(), "parcel_weight_kg")
        col_service = cls._find_column_name(df.columns.tolist(), "service_time_minutes")
        col_wstart = cls._find_column_name(df.columns.tolist(), "window_start")
        col_wend = cls._find_column_name(df.columns.tolist(), "window_end")
        col_lat = cls._find_column_name(df.columns.tolist(), "latitude")
        col_lon = cls._find_column_name(df.columns.tolist(), "longitude")

        # Validation: Must have either Address or Coordinates
        if not col_address and not (col_lat and col_lon):
            errors.append("Manifest must contain an 'address' column or both 'latitude' and 'longitude' columns.")
            return [], errors, warnings

        # Step 3: Iterate and parse rows
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel 1-based indexing with header

            # Order ID
            if col_id and pd.notna(row[col_id]):
                order_id = str(row[col_id]).strip()
                if order_id.endswith(".0"):  # Handle pandas float conversion of int IDs
                    order_id = order_id[:-2]
            else:
                order_id = f"ORDER-{idx + 1}"
                warnings.append(f"Row {row_num}: Missing order ID, generated '{order_id}'.")

            # Address & Coords
            raw_addr = str(row[col_address]).strip() if col_address and pd.notna(row[col_address]) else ""
            lat = None
            lon = None

            if col_lat and pd.notna(row[col_lat]):
                try:
                    lat = float(row[col_lat])
                except ValueError:
                    warnings.append(f"Row {row_num}: Invalid latitude '{row[col_lat]}'. Will geocode address instead.")

            if col_lon and pd.notna(row[col_lon]):
                try:
                    lon = float(row[col_lon])
                except ValueError:
                    warnings.append(f"Row {row_num}: Invalid longitude '{row[col_lon]}'. Will geocode address instead.")

            if not raw_addr and (lat is None or lon is None):
                errors.append(f"Row {row_num}: Row has neither a valid address nor valid (lat, lon) coordinates.")
                continue

            # Weight
            weight = 10.0
            if col_weight and pd.notna(row[col_weight]):
                try:
                    w = float(row[col_weight])
                    if w > 0:
                        weight = w
                    else:
                        warnings.append(f"Row {row_num}: Weight must be > 0. Defaulted to 10 kg.")
                except ValueError:
                    warnings.append(f"Row {row_num}: Invalid weight '{row[col_weight]}'. Defaulted to 10 kg.")

            # Service Time
            service_mins = 10
            if col_service and pd.notna(row[col_service]):
                try:
                    s = int(row[col_service])
                    if s >= 1:
                        service_mins = s
                except ValueError:
                    pass

            # Time Windows
            w_start_val = row[col_wstart] if col_wstart and pd.notna(row[col_wstart]) else 0
            w_end_val = row[col_wend] if col_wend and pd.notna(row[col_wend]) else 1440

            win_start = parse_time_to_minutes(w_start_val, default=0)
            win_end = parse_time_to_minutes(w_end_val, default=1440)

            # Sanity check on time window
            if win_end < win_start:
                # Could be cross midnight or swapped
                win_end += 1440

            parsed_orders.append({
                "external_order_id": order_id,
                "raw_address": raw_addr or f"Location ({lat}, {lon})",
                "latitude": lat,
                "longitude": lon,
                "parcel_weight_kg": weight,
                "service_time_minutes": service_mins,
                "window_start_minutes": win_start,
                "window_end_minutes": win_end
            })

        logger.info(f"Parsed {len(parsed_orders)} orders from {filename} ({len(errors)} errors, {len(warnings)} warnings)")
        return parsed_orders, errors, warnings
