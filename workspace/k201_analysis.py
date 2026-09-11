import math

# ============================================================
# 1. SEVERITY CLASSIFICATION (API 617 / ISO 10816-3)
# ============================================================

# ISO 10816-3 Zone boundaries for machine group 3 (centrifugal compressors,
# drivers > 12 kW, synchronous speed 1000-15000 rpm). Values in mm/s (p-p).
ISO_10816_ZONE_3 = {
    "A": 2.8,   # Upper limit of Zone A (Good)
    "B": 4.5,   # Upper limit of Zone B (Acceptable)
    "C": 7.1,   # Upper limit of Zone C (Unsafe)
    "D": 11.3,  # Upper limit of Zone D (Immediate shutdown)
}

def classify_severity(value_mm_s, zone_map=ISO_10816_ZONE_3):
    """Return ISO 10816-3 zone and API 617 severity descriptor."""
    if value_mm_s <= zone_map["A"]:
        zone = "A"
        api = "Zone A — Good. Vibration is well within acceptable limits."
    elif value_mm_s <= zone_map["B"]:
        zone = "B"
        api = "Zone B — Acceptable. Monitor; trending toward unsafe."
    elif value_mm_s <= zone_map["C"]:
        zone = "C"
        api = "Zone C — Unsafe. Remedial action required before next run."
    else:
        zone = "D"
        api = "Zone D — Immediate shutdown. Rotor must be taken out of service."
    return zone, api

# --- API 617 Annex (API Std 617, 2nd ed., Annex) — running vibration limits ---
# For machines with synchronous speed 1000-15000 rpm, API 617 Annex gives:
#   2.5 mm/s (0.1 in/s) as the limit for continuous operation.
API_617_LIMIT_IN_S = 0.1   # 0.1 in/s = 2.54 mm/s
API_617_LIMIT_MM_S = 2.54

def api_617_assessment(value_mm_s):
    if value_mm_s <= API_617_LIMIT_MM_S:
        return "WITHIN API 617 Annex limit (<=2.54 mm/s)"
    else:
        return f"EXCEEDS API 617 Annex limit ({value_mm_s:.2f} > {API_617_LIMIT_MM_S:.2f} mm/s)"

# ============================================================
# 2. ROOT CAUSE DISCRIMINATION ENGINE
# ============================================================

def discriminate_root_cause(vib_1x, vib_2x, vib_ratio, lube_oil_pressure,
                           bearing_temp, discharge_temp):
    """
    Discriminate between the three candidate root causes:
      (a) Dynamic unbalance
      (b) Shaft misalignment
      (c) Journal bearing clearance degradation

    Inputs (all from condition-monitoring + P&ID + bearing inspection):
      vib_1x   : 1X running speed amplitude (mm/s)
      vib_2x   : 2X running speed amplitude (mm/s)
      vib_ratio: 2X/1X ratio
      lube_oil_pressure : lube oil supply pressure (kg/cm2g)
      bearing_temp      : journal bearing metal temperature (degC)
      discharge_temp    : discharge gas temperature (degC)
    """
    findings = []

    # (a) DYNAMIC UNBALANCE
    # Signature: 1X dominant, 1X/2X ratio high (>3), 2X low.
    # Unbalance is the #1 cause of rotating-machinery vibration (API 617).
    if vib_ratio >= 3.0 and vib_2x <= 0.5 * vib_1x:
        confidence = "HIGH"
        evidence = [
            f"1X dominant with 1X/2X ratio = {vib_ratio:.1f} (>=3.0)",
            f"2X harmonic = {vib_2x:.2f} mm/s (negligible, <= half of 1X)",
            "Classic single-plane unbalance signature.",
        ]
    else:
        confidence = "LOW"
        evidence = [
            f"1X/2X ratio = {vib_ratio:.1f} (below 3.0 — not a clean unbalance signature)",
            f"2X harmonic = {vib_2x:.2f} mm/s (not negligible)",
            "Does not match pure unbalance signature.",
        ]
    findings.append({
        "cause": "Dynamic Unbalance",
        "confidence": confidence,
        "evidence": evidence,
    })

    # (b) SHAFT MISALIGNMENT
    # Signature: 2X dominant (1X/2X ratio < 1), high 2X, often with axial component.
    if vib_ratio < 1.0 and vib_2x >= vib_1x:
        confidence = "HIGH"
        evidence = [
            f"2X dominant with 1X/2X ratio = {vib_ratio:.1f} (<1.0)",
            f"2X harmonic = {vib_2x:.2f} mm/s (>= 1X — coupling/misalignment signature)",
            "Classic parallel/angular misalignment signature.",
        ]
    else:
        confidence = "LOW"
        evidence = [
            f"2X harmonic = {vib_2x:.2f} mm/s (not dominant over 1X)",
            "Does not match misalignment signature.",
        ]
    findings.append({
        "cause": "Shaft Misalignment",
        "confidence": confidence,
        "evidence": evidence,
    })

    # (c) JOURNAL BEARING CLEARANCE DEGRADATION
    # Signature: elevated bearing metal temperature, low lube oil pressure,
    # oil-film instability; vibration may be broadband or moderate 1X.
    bearing_hot = bearing_temp > 85.0
    lube_low = lube_oil_pressure < 1.5
    if bearing_hot or lube_low:
        confidence = "MODERATE"
        evidence = [
            f"Journal bearing metal temp = {bearing_temp:.1f} degC " + ("(elevated >85)" if bearing_hot else "(normal)"),
            f"Lube oil supply pressure = {lube_oil_pressure:.2f} kg/cm2g " + ("(low <1.5)" if lube_low else "(normal)"),
            "Oil-film / clearance degradation indicator.",
        ]
    else:
        confidence = "LOW"
        evidence = [
            f"Journal bearing metal temp = {bearing_temp:.1f} degC (normal)",
            f"Lube oil supply pressure = {lube_oil_pressure:.2f} kg/cm2g (normal)",
            "No bearing-clearance indicator present.",
        ]
    findings.append({
        "cause": "Journal Bearing Clearance Degradation",
        "confidence": confidence,
        "evidence": evidence,
    })

    # Rank by confidence
    order = {"HIGH": 0, "MODERATE": 1, "LOW": 2}
    findings.sort(key=lambda f: order[f["confidence"]])
    primary = findings[0]["cause"]
    return findings, primary

# ============================================================
# TESTS
# ============================================================

def test_severity_classification():
    assert classify_severity(1.5)[0] == "A"
    assert classify_severity(3.5)[0] == "B"
    assert classify_severity(5.0)[0] == "C"
    assert classify_severity(10.0)[0] == "D"
    print("test_severity_classification PASSED")

def test_unbalance_signature():
    findings, primary = discriminate_root_cause(
        vib_1x=4.82, vib_2x=0.3, vib_ratio=16.0,
        lube_oil_pressure=1.78, bearing_temp=72.0, discharge_temp=118.4)
    # 1X dominant, 2X negligible -> unbalance
    assert primary == "Dynamic Unbalance", primary
    assert findings[0]["confidence"] == "HIGH"
    print("test_unbalance_signature PASSED")

def test_misalignment_signature():
    findings, primary = discriminate_root_cause(
        vib_1x=2.0, vib_2x=4.0, vib_ratio=0.5,
        lube_oil_pressure=1.78, bearing_temp=72.0, discharge_temp=118.4)
    assert primary == "Shaft Misalignment", primary
    assert findings[0]["confidence"] == "HIGH"
    print("test_misalignment_signature PASSED")

def test_bearing_degradation():
    findings, primary = discriminate_root_cause(
        vib_1x=4.82, vib_2x=0.3, vib_ratio=16.0,
        lube_oil_pressure=1.2, bearing_temp=95.0, discharge_temp=118.4)
    assert findings[2]["confidence"] == "MODERATE"
    print("test_bearing_degradation PASSED")

test_severity_classification()
test_unbalance_signature()
test_misalignment_signature()
test_bearing_degradation()
print("ALL TESTS PASSED")
