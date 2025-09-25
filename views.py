import json
import pandas as pd
from django.shortcuts import render 
# render used for ------->Django shortcut to render a template with a context.

def dashboard(request):
    file_path = r"C:/Users/vmgenai/Desktop/dataset_warehouse_sustainability.xlsx"

    try:
        try:
            df = pd.read_excel(file_path, sheet_name="DashboardData")
        except ValueError:
            sheets = pd.read_excel(file_path, sheet_name=None)
            first_sheet_name = list(sheets.keys())[0]
            df = sheets[first_sheet_name]
    except Exception as e:
        return render(request, "analyzer/dashboard.html", {
            "years": [], "warehouses": [],
            "selected_year": None, "selected_warehouse": None,
            "data_by_year": json.dumps({}), "load_error": str(e),
            # dumps() stands for “dump string”. weare using to render the data
        })

    # Normalize columns two list of all Excel column names to bring original names from the excel.
    original_cols = list(df.columns)
    lowered = {str(c).strip().lower(): c for c in original_cols}
# substr_list is just a parameter name for the function.
# substr is short for “substring” — a part of a string.
    def find_column(substr_list):
        for substr in substr_list:
            for lc, orig in lowered.items():
                if substr in lc:
                    return orig
        return None
     # Detect key columns  for this ------->year_col → year warehouse_col → warehouse/location/siteco2_col → CO₂ emissions
    # energy_col → energy consumption

    year_col = find_column(["year"])
    warehouse_col = find_column(["warehouse", "location", "site"])
    co2_col = find_column(["co2", "co₂", "co_2"])
    energy_col = find_column(["energy", "consumption"])
    renewable_col = find_column(["renewable"])

    if year_col is None and original_cols:
        year_col = original_cols[0]

    if year_col and pd.api.types.is_datetime64_any_dtype(df[year_col]):
        df[year_col] = df[year_col].dt.year.astype(str)
    elif year_col:
        df[year_col] = df[year_col].astype(str)

    if warehouse_col:
        df[warehouse_col] = df[warehouse_col].astype(str)

# .astype(str) → convert the data type of that column to string.
# astype() is a pandas method used to cast/convert a column (or entire DataFrame) to a different typw
    years = sorted([str(y) for y in df[year_col].dropna().unique()]) if year_col else []

    selected_year = request.GET.get("year", years[-1] if years else None)

    # Warehouses for that year
    if selected_year and warehouse_col:
        warehouses = sorted(df[df[year_col] == selected_year][warehouse_col].dropna().unique())
    else:
        warehouses = []

    selected_warehouse = request.GET.get("warehouse", warehouses[0] if warehouses else None)

    # Build nested dict: data_by_year[year][warehouse] = {values}
    data_by_year = {}
    for y in years:
        data_by_year[y] = {}
        dfy = df[df[year_col] == y]

        if warehouse_col:
            for w in dfy[warehouse_col].dropna().unique():
                dfyw = dfy[dfy[warehouse_col] == w]
                data_by_year[y][w] = {
                    "co2_total": int(dfyw[co2_col].sum()) if co2_col else 0,
                    "energy_total": int(dfyw[energy_col].sum()) if energy_col else 0,
                    "renewable_total": int(dfyw[renewable_col].sum()) if renewable_col else 0,
                }
        else:
            data_by_year[y]["ALL"] = {
                "co2_total": int(dfy[co2_col].sum()) if co2_col else 0,
                "energy_total": int(dfy[energy_col].sum()) if energy_col else 0,
                "renewable_total": int(dfy[renewable_col].sum()) if renewable_col else 0,
            }

    context = {
        "years": years,
        "warehouses": warehouses,
        "selected_year": selected_year,
        "selected_warehouse": selected_warehouse,
        "data_by_year": json.dumps(data_by_year),
        "load_error": None,
    }
    return render(request, "analyzer/dashboard.html", context)
