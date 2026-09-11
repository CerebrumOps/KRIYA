import json

# ============================================================
# K-201 FCCU Wet Gas Compressor — Turnaround Investigation Model
# ============================================================

# --- Telemetry snapshot (from query_refinery_telemetry) ---
telemetry = {
    "Discharge Gas Temperature": {"value": 118.40, "unit": "degC", "min": 80.0, "max": 130.0, "state": "NORMAL"},
    "Lube Oil Supply Pressure":   {"value": 1.78,  "unit": "kg/cm2g", "min": 1.50, "max": 2.50, "state": "NORMAL"},
    "Vibration Drive-End (X-Axis)": {"value": 4.82, "unit": "mm/s", "min": 0.50, "max": 4.50, "state": "WARNING"},
}

print("=== TELEMETRY SNAPSHOT ===")
for k, v in telemetry.items():
    print(f"{k}: {v['value']} {v['unit']} -> {v['state']}")
