import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# CPM Network Analysis for CDU-II TAR-2026-Q4
# 45 interdependent work orders across 4 phases

# Define work order data with dependencies
work_orders = [
    # Pre-Shutdown Phase (Days 1-5)
    {"id": "WO-001", "name": "CDU-II Shutdown Procedure Execution", "phase": "Pre-Shutdown", "duration": 2, "start": 1, "end": 2, "dependencies": []},
    {"id": "WO-002", "name": "Process Isolation & Blind Installation", "phase": "Pre-Shutdown", "duration": 3, "start": 1, "end": 3, "dependencies": ["WO-001"]},
    {"id": "WO-003", "name": "Utility Shutdown (Steam, Water, Electricity)", "phase": "Pre-Shutdown", "duration": 2, "start": 1, "end": 2, "dependencies": ["WO-001"]},
    {"id": "WO-004", "name": "Safety System Activation (LOTO, Gas Detection)", "phase": "Pre-Shutdown", "duration": 1, "start": 2, "end": 2, "dependencies": ["WO-003"]},
    {"id": "WO-005", "name": "Hot Work Permit & Hot Surface Tagging", "phase": "Pre-Shutdown", "duration": 1, "start": 2, "end": 2, "dependencies": ["WO-004"]},
    {"id": "WO-006", "name": "C-101 Column Isolation & Drainage", "phase": "Pre-Shutdown", "duration": 2, "start": 2, "end": 3, "dependencies": ["WO-002", "WO-003"]},
    {"id": "WO-007", "name": "E-104 Heat Exchanger Isolation", "phase": "Pre-Shutdown", "duration": 1, "start": 2, "end": 2, "dependencies": ["WO-003"]},
    {"id": "WO-008", "name": "F-101 Furnace Isolation & Fuel Gas Shutoff", "phase": "Pre-Shutdown", "duration": 1, "start": 2, "end": 2, "dependencies": ["WO-003"]},
    
    # Steaming/De-inventory Phase (Days 3-7)
    {"id": "WO-009", "name": "C-101 Column Steaming (De-inventory)", "phase": "Steaming", "duration": 4, "start": 3, "end": 6, "dependencies": ["WO-006"]},
    {"id": "WO-010", "name": "E-104 Steam Purge & Drain", "phase": "Steaming", "duration": 2, "start": 3, "end": 4, "dependencies": ["WO-007"]},
    {"id": "WO-011", "name": "F-101 Furnace Steam Purge", "phase": "Steaming", "duration": 3, "start": 3, "end": 5, "dependencies": ["WO-008"]},
    {"id": "WO-012", "name": "Residue Removal Verification", "phase": "Steaming", "duration": 1, "start": 6, "end": 6, "dependencies": ["WO-009", "WO-010", "WO-011"]},
    
    # Mechanical Overhaul Phase (Days 7-12)
    {"id": "WO-013", "name": "C-101 Tray Inspection & Replacement", "phase": "Mechanical", "duration": 5, "start": 7, "end": 11, "dependencies": ["WO-012"]},
    {"id": "WO-014", "name": "C-101 Column Reassembly & Alignment", "phase": "Mechanical", "duration": 3, "start": 11, "end": 13, "dependencies": ["WO-013"]},
    {"id": "WO-015", "name": "E-104 Bundle Extraction", "phase": "Mechanical", "duration": 4, "start": 7, "end": 10, "dependencies": ["WO-012"]},
    {"id": "WO-016", "name": "E-104 Tube Pass & Cleaning", "phase": "Mechanical", "duration": 3, "start": 10, "end": 12, "dependencies": ["WO-015"]},
    {"id": "WO-017", "name": "E-104 Bundle Reassembly", "phase": "Mechanical", "duration": 2, "start": 12, "end": 13, "dependencies": ["WO-016"]},
    {"id": "WO-018", "name": "F-101 Steam-Air Decoking", "phase": "Mechanical", "duration": 5, "start": 7, "end": 11, "dependencies": ["WO-012"]},
    {"id": "WO-019", "name": "F-101 Furnace Internal Inspection", "phase": "Mechanical", "duration": 2, "start": 11, "end": 12, "dependencies": ["WO-018"]},
    {"id": "WO-020", "name": "F-101 Furnace Reassembly", "phase": "Mechanical", "duration": 2, "start": 12, "end": 13, "dependencies": ["WO-019"]},
    
    # Catalyst Passivation Phase (Days 13-14)
    {"id": "WO-021", "name": "C-101 Catalyst Passivation", "phase": "Catalyst", "duration": 2, "start": 13, "end": 14, "dependencies": ["WO-014"]},
    {"id": "WO-022", "name": "System Pressure Test", "phase": "Catalyst", "duration": 1, "start": 14, "end": 14, "dependencies": ["WO-014", "WO-017", "WO-020"]},
    {"id": "WO-023", "name": "Utility Restoration", "phase": "Catalyst", "duration": 2, "start": 14, "end": 15, "dependencies": ["WO-022"]},
    {"id": "WO-024", "name": "Gradual Process Restart", "phase": "Catalyst", "duration": 2, "start": 15, "end": 16, "dependencies": ["WO-023"]},
    {"id": "WO-025", "name": "Post-TAR Inspection & Handover", "phase": "Catalyst", "duration": 1, "start": 16, "end": 16, "dependencies": ["WO-024"]},
]

# Create DataFrame
df = pd.DataFrame(work_orders)

# CPM Algorithm Implementation
def cpm_analysis(df):
    """
    Compute Early Start, Early Finish, Late Start, Late Finish, Total Float
    and identify Critical Path
    """
    n = len(df)
    
    # Sort by dependencies to ensure topological order
    df = df.sort_values(by=['phase', 'start'])
    
    # Forward Pass (Early Start, Early Finish)
    ES = {}
    EF = {}
    
    for idx, row in df.iterrows():
        ws = row['start']  # Work start day
        duration = row['duration']
        
        # Calculate Early Start (max of predecessor EF)
        if len(row['dependencies']) == 0:
            ES[idx] = ws
        else:
            max_predecessor_ef = max([EF[df[df['id'] == dep]['id'].values[0]] for dep in row['dependencies']])
            ES[idx] = max_predecessor_ef
        
        EF[idx] = ES[idx] + duration - 1  # Day-based (inclusive)
    
    # Find project completion day
    project_end = max(EF.values())
    
    # Backward Pass (Late Start, Late Finish)
    LS = {}
    LF = {}
    
    for idx, row in df.iterrows():
        duration = row['duration']
        
        # Calculate Late Finish (min of successor LS)
        if len(row['dependencies']) == 0:
            LF[idx] = project_end
        else:
            min_successor_ls = min([LS[df[df['id'] == succ]['id'].values[0]] for succ in row['dependencies']])
            LF[idx] = min_successor_ls
        
        LS[idx] = LF[idx] - duration + 1
    
    # Calculate Total Float
    TF = {}
    for idx in df['id']:
        TF[idx] = LS[idx] - ES[idx]
    
    # Identify Critical Path (TF = 0)
    critical_path = [row['id'] for idx, row in df.iterrows() if TF[idx] == 0]
    
    # Calculate project duration
    project_duration = project_end + 1
    
    return {
        'ES': ES,
        'EF': EF,
        'LS': LS,
        'LF': LF,
        'TF': TF,
        'critical_path': critical_path,
        'project_duration': project_duration
    }

# Run CPM Analysis
cpm_results = cpm_analysis(df)

# Display Results
print("=" * 80)
print("CDU-II TAR-2026-Q4 CPM NETWORK ANALYSIS")
print("=" * 80)

print(f"\nTotal Work Orders: {len(work_orders)}")
print(f"Project Duration: {cpm_results['project_duration']} days")
print(f"Critical Path Activities: {len(cpm_results['critical_path'])}")

print("\n" + "=" * 80)
print("PHASE BREAKDOWN")
print("=" * 80)

for phase in ['Pre-Shutdown', 'Steaming', 'Mechanical', 'Catalyst']:
    phase_orders = df[df['phase'] == phase]
    print(f"\n{phase} Phase:")
    print(f"  Work Orders: {len(phase_orders)}")
    print(f"  Duration: {phase_orders['duration'].sum()} days")
    print(f"  Critical Activities: {phase_orders[phase_orders['id'].isin(cpm_results['critical_path'])]['id'].tolist()}")

print("\n" + "=" * 80)
print("CRITICAL PATH ANALYSIS")
print("=" * 80)

print("\nCritical Path Sequence:")
for i, order_id in enumerate(cpm_results['critical_path'], 1):
    order = df[df['id'] == order_id].iloc[0]
    print(f"{i}. {order['id']}: {order['name']}")
    print(f"   Phase: {order['phase']}, Duration: {order['duration']} days, ES: {order['start']}, EF: {order['start'] + order['duration'] - 1}")

print("\n" + "=" * 80)
print("TOTAL FLOAT ANALYSIS")
print("=" * 80)

print("\nNon-Critical Activities (Float > 0):")
non_critical = df[df['id'].isin(cpm_results['TF']) & (df['TF'] > 0)]
for idx, row in non_critical.iterrows():
    print(f"{row['id']}: {row['name']} - Float: {row['TF']} days")

print("\n" + "=" * 80)
print("BOTTLENECK IDENTIFICATION")
print("=" * 80)

# Identify activities with zero float (critical) and long duration
critical_activities = df[df['id'].isin(cpm_results['critical_path'])]
print("\nCritical Path Bottlenecks (Long Duration Activities):")
for idx, row in critical_activities.iterrows():
    print(f"{row['id']}: {row['name']} - {row['duration']} days")

# Identify activities with high float that could become critical if delayed
high_float = non_critical.sort_values(by='TF', ascending=False).head(5)
print("\nActivities with High Float (Risk if delayed):")
for idx, row in high_float.iterrows():
    print(f"{row['id']}: {row['name']} - Float: {row['TF']} days")

# Save results to file
import json
results = {
    'work_orders': len(work_orders),
    'project_duration': cpm_results['project_duration'],
    'critical_path': cpm_results['critical_path'],
    'phase_breakdown': {
        'Pre-Shutdown': {
            'orders': len(phase_orders),
            'duration': phase_orders['duration'].sum(),
            'critical': phase_orders[phase_orders['id'].isin(cpm_results['critical_path'])]['id'].tolist()
        },
        'Steaming': {
            'orders': len(phase_orders),
            'duration': phase_orders['duration'].sum(),
            'critical': phase_orders[phase_orders['id'].isin(cpm_results['critical_path'])]['id'].tolist()
        },
        'Mechanical': {
            'orders': len(phase_orders),
            'duration': phase_orders['duration'].sum(),
            'critical': phase_orders[phase_orders['id'].isin(cpm_results['critical_path'])]['id'].tolist()
        },
        'Catalyst': {
            'orders': len(phase_orders),
            'duration': phase_orders['duration'].sum(),
            'critical': phase_orders[phase_orders['id'].isin(cpm_results['critical_path'])]['id'].tolist()
        }
    }
}

with open('cdu_ii_tar_2026_q4_cpm_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nResults saved to: cd_u_ii_tar_2026_q4_cpm_analysis.json")
