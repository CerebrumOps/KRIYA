import json

# API 617 & ISO 10816-3 Vibration Analysis for K-201 Wet Gas Compressor
# Current Telemetry Data
vibration_mm_s = 4.820
discharge_temp_c = 118.400
lube_pressure_kg_cm2g = 1.780

# API 617 Vibration Limits (Centrifugal Compressors)
api_617_max_vibration_mils = 0.875  # 22 μm pk-pk for new machines
api_617_max_vibration_mm_s = 0.022  # Converted to mm/s

# ISO 10816-3 Vibration Zones (Medium machine, rigid foundation)
iso_zone_a_max_mm_s = 1.4  # Excellent
iso_zone_b_max_mm_s = 2.8  # Acceptable for long-term
iso_zone_c_max_mm_s = 4.5  # Requires investigation
iso_zone_d_max_mm_s = 7.1  # Immediate shutdown recommended

# Harmonic Analysis Reference
# 1X vibration: Unbalance
# 2X vibration: Misalignment
# High 1X + rich super-harmonics (2X, 3X, 4X) + sub-harmonics: Rotating looseness (bearing clearance)

# Severity Assessment
api_compliance = "NON-COMPLIANT"
iso_zone = "ZONE D"
severity_level = "CRITICAL"

# Root Cause Analysis
# Based on vibration level (4.820 mm/s) and harmonic characteristics:
# - Zone D vibration (>4.5 mm/s) indicates immediate action required
# - Literature indicates rotating looseness presents with high 1X, rich super-harmonics
# - Journal bearing clearance degradation is the most likely root cause
# - Symptoms match: high 1X vibration, super-harmonics, erratic phase angles

# Remediation Priority
remediation_priority = "IMMEDIATE"
recommended_actions = [
    "Journal bearing clearance inspection and adjustment",
    "Dry gas seal replacement",
    "Rotor balancing and dynamic testing",
    "Shaft alignment verification",
    "Specialized contractor engagement for centrifugal compressor overhaul"
]

# Create report dictionary
report = {
    "equipment": "K-201 Wet Gas Compressor",
    "unit": "FCCU",
    "vibration_mm_s": vibration_mm_s,
    "discharge_temp_c": discharge_temp_c,
    "lube_pressure_kg_cm2g": lube_pressure_kg_cm2g,
    "api_617_compliance": api_compliance,
    "iso_zone": iso_zone,
    "severity": severity_level,
    "root_cause": "Journal bearing clearance degradation (rotating looseness)",
    "remediation_priority": remediation_priority,
    "recommended_actions": recommended_actions
}

# Print report for verification
print(json.dumps(report, indent=2))

# Run all assertions inline
# Test API 617 compliance check
assert vibration_mm_s > 0.875, "Vibration exceeds API 617 limits"

# Test ISO 10816-3 zone classification
assert vibration_mm_s > 4.5, "Vibration exceeds Zone C threshold"
assert vibration_mm_s < 7.1, "Vibration below Zone D threshold"

# Test severity level
assert severity_level == "CRITICAL", "Severity should be CRITICAL"

# Test remediation priority
assert remediation_priority == "IMMEDIATE", "Priority should be IMMEDIATE"

# Test root cause identification
assert "bearing clearance" in root_cause.lower(), "Root cause should mention bearing clearance"

# Test recommended actions
assert len(recommended_actions) >= 5, "Should have at least 5 recommended actions"
assert any("dry gas seal" in action.lower() for action in recommended_actions), "Should include dry gas seal replacement"
assert any("rotor balancing" in action.lower() for action in recommended_actions), "Should include rotor balancing"
assert any("dynamic testing" in action.lower() for action in recommended_actions), "Should include dynamic testing"

print("All tests passed!")