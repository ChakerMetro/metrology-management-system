from datetime import datetime
import json
import sqlite3

# ==========================================
# DATABASE FUNCTIONS & COMPLIANCE SCHEMAS
# ==========================================

def init_db():
    """Initializes and auto-migrates relational inventory tables with strict ISO-grade constraints."""
    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        
        # Force Foreign Key constraint tracking inside the SQLite runtime environment
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Main Inventory Table (Upgraded with Soft Delete capabilities)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                serial TEXT UNIQUE NOT NULL COLLATE NOCASE,
                manufacturer TEXT NOT NULL,
                calibration_date TEXT NOT NULL,
                next_calibration_date TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                instrument_type TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0
            )
        """)
        
        # Self-Healing Layer: Check if existing database needs column updating
        cursor.execute("PRAGMA table_info(instruments);")
        columns = [col[1] for col in cursor.fetchall()]
        if "is_deleted" not in columns:
            cursor.execute("ALTER TABLE instruments ADD COLUMN is_deleted INTEGER DEFAULT 0;")
        
        # 2. 🛡️ Regulatory Audit History Table (Protected via RESTRICT parameters)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id TEXT NOT NULL,
                serial TEXT NOT NULL,
                action_type TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE RESTRICT
            )
        """)
        
        # 3. 🧪 BRAND NEW: Traceable Calibration Events Log (ISO 17025 Compliance Metric)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id TEXT NOT NULL,
                cal_date TEXT NOT NULL,
                next_cal_date TEXT NOT NULL,
                technician TEXT NOT NULL,
                standard_used TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                pass_fail TEXT CHECK(pass_fail IN ('Pass', 'Fail')),
                notes TEXT,
                FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE RESTRICT
            )
        """)

def migrate_json_to_sqlite(json_instruments):
    """Safely ports legacy JSON data over to SQLite using content managers."""
    if not json_instruments:
        return

    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        migrated_count = 0

        for inst in json_instruments:
            cursor.execute("""
                INSERT OR IGNORE INTO instruments (
                    id, name, serial, manufacturer, calibration_date, 
                    next_calibration_date, location, status, instrument_type, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                inst.get("id"), inst.get("name"), inst.get("serial"),
                inst.get("manufacturer"), inst.get("calibration_date"),
                inst.get("next_calibration_date"), inst.get("location"),
                inst.get("status"), inst.get("instrument_type")
            ))
            if cursor.rowcount > 0:
                migrated_count += 1

    if migrated_count > 0:
        print(f"📦 Database Bridge: Successfully migrated {migrated_count} assets from JSON to SQLite!") 

def log_change(cursor, instrument_id, serial, action_type, details):
    """Automates compliance tracking tracking inside an active transaction execution cursor."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO audit_history (instrument_id, serial, action_type, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (instrument_id, serial, action_type, details, timestamp))

def view_audit_history():
    """Fetches and displays the immutable regulatory audit trail."""
    print("\n--- Compliance Audit Logs ---")
    search_serial = input("Enter serial number to filter logs (or leave blank to see all history): ").strip()
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if search_serial:
            cursor.execute("""
                SELECT * FROM audit_history 
                WHERE LOWER(serial) = LOWER(?) 
                ORDER BY log_id DESC
            """, (search_serial,))
        else:
            cursor.execute("SELECT * FROM audit_history ORDER BY log_id DESC")
            
        logs = cursor.fetchall()

    if not logs:
        print("ℹ️ No audit history records found matching your request.")
        return

    print("\n📜 ================= COMPLIANCE AUDIT TRAIL =================")
    for log in logs:
        print(f"""[{log['timestamp']}] ACTION: {log['action_type']} | Asset Serial: {log['serial']}
• System Tracking ID: {log['instrument_id']}
• Change Ledger Details:
  ↳ {log['details']}
----------------------------------------------------------------------""")
    print("==============================================================")         

def load_instruments():
    """Loads backup tracking from JSON file if it exists."""
    try:
        with open("instruments.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# ==========================================
# VALIDATION & METRIC PARSING HELPERS
# ==========================================

def get_valid_date(prompt, allow_empty=False):
    """Prompts for a date, validates format, or allows graceful cancellation."""
    while True:
        date_str = input(prompt).strip()
        if date_str.lower() in ['q', 'quit', 'cancel']:
            return None
        if allow_empty and date_str == "":
            return ""
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Invalid date format! Use YYYY-MM-DD (or type 'q' to cancel).")

def get_valid_status(prompt, allow_empty=False):
    """Enforces rigid status validation rules."""
    while True:
        status_input = input(prompt).strip().capitalize()
        if allow_empty and status_input == "":
            return ""
        if status_input in ["Active", "Inactive"]:
            return status_input
        print("❌ Invalid input! Status must be exactly 'Active' or 'Inactive'.") 

def generate_next_id(cursor):
    """Calculates the next sequence natively inside SQL via extraction expressions (Scans all items to prevent collisions)."""
    cursor.execute("SELECT MAX(CAST(SUBSTR(id, 5) AS INTEGER)) FROM instruments WHERE id LIKE 'SYS-%'")
    result = cursor.fetchone()
    max_num = result[0] if result[0] is not None else 0
    return f"SYS-{(max_num + 1):03d}"        

# ==========================================
# INVENTORY CONTROLLER MODULES
# ==========================================

def add_instrument():
    """Handles adding a new instrument with chronological gatekeeping validation."""
    print("\n--- Add New Instrument (SQL Writer Mode) ---")
    name = input("Instrument name: ").strip()
    serial = input("Serial number: ").strip()
    
    if not serial:
        print("❌ Error: Serial number cannot be left blank.")
        return

    manufacturer = input("The Manufacturer name: ").strip()
    
    # 🛡️ UPGRADE 1: Strict Timeline Gatekeeping Loop
    while True:
        calibration_date = get_valid_date("Calibration date (YYYY-MM-DD): ")
        if calibration_date is None: return
        
        next_calibration_date = get_valid_date("Next calibration date (YYYY-MM-DD): ")
        if next_calibration_date is None: return
        
        if next_calibration_date > calibration_date:
            break
        print("❌ Compliance Error: Next calibration date must be strictly AFTER the last calibration date.")

    location = input("Location: ").strip()
    status = get_valid_status("Status (Active/Inactive): ")
    instrument_type = input("Type of instrument: ").strip()
    
    try:
        with sqlite3.connect("metrology.db") as conn:
            cursor = conn.cursor()
            system_id = generate_next_id(cursor)
            
            cursor.execute("""
                INSERT INTO instruments (
                    id, name, serial, manufacturer, calibration_date, 
                    next_calibration_date, location, status, instrument_type, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (system_id, name, serial, manufacturer, calibration_date, next_calibration_date, location, status, instrument_type))
            
            log_change(cursor, system_id, serial, "ADD", f"Asset initialized into inventory. Status: '{status}' | Next Due: {next_calibration_date}.")
            print(f"✅ Instrument added successfully and secured under Tracking ID: {system_id}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: An instrument with serial '{serial}' already exists! Transaction aborted.")

def view_instruments():
    """Fetches non-deleted instruments sorted by calibration urgency."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instruments WHERE is_deleted = 0 ORDER BY next_calibration_date ASC")
        instruments = cursor.fetchall()

    if not instruments:
        print("No active instruments found in the SQL database.")
        return

    print("\n=== CURRENT REGISTERED INSTRUMENTS (Active Registries Only) ===")
    for instrument in instruments:
        print(f"""[ ID: {instrument['id']} | Instrument: {instrument['name']} ]
------------------------------------------------------
• Serial Number:          {instrument['serial']}
• Manufacturer:           {instrument['manufacturer']}
• Calibration Date:       {instrument['calibration_date']}
• Next Calibration Date:  {instrument['next_calibration_date']}
• Location:               {instrument['location']}
• Status:                 {instrument['status']}
• Instrument Type:        {instrument['instrument_type']}
=======================================================""")

def delete_instrument():
    """Executes an immutable Soft-Delete. Preserves integrity while shifting assets out of deployment views."""
    serial = input("Enter the serial number of the instrument to archive/delete: ").strip()
    if not serial:
        print("❌ Error: Serial number cannot be left blank.")
        return

    with sqlite3.connect("metrology.db") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, is_deleted FROM instruments WHERE LOWER(serial) = LOWER(?) AND is_deleted = 0", (serial,))
        instrument = cursor.fetchone()
        
        if not instrument:
            print("❌ Active instrument not found with that serial number.")
            return
            
        inst_id, inst_name = instrument[0], instrument[1]
        
        # Execute the Soft Delete modification
        cursor.execute("UPDATE instruments SET is_deleted = 1, status = 'Inactive' WHERE id = ?", (inst_id,))
        
        # Log entry to maintain chain of custody record continuity
        log_change(cursor, inst_id, serial, "DELETE (SOFT)", f"Asset '{inst_name}' was soft-deleted and archived from active display registries.")
        print(f"❌ Asset successfully flagged as archived! Real-time systems adjusted.")

def edit_instrument():
    """Edits fluid parameters, enforces date logic limits, and records precise delta logs."""
    serial = input("Enter the serial number of the instrument to edit: ").strip()
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM instruments WHERE LOWER(serial) = LOWER(?) AND is_deleted = 0", (serial,))
        instrument = cursor.fetchone()
        
        if not instrument:
            print("❌ Active instrument not found.")
            return

        print("\nLeave field blank to keep current value (or type 'q' to abort edit).")
        name = input(f"Instrument name ({instrument['name']}): ").strip() or instrument['name']
        manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ").strip() or instrument['manufacturer']
        
        raw_cal = get_valid_date(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ", allow_empty=True)
        if raw_cal is None: print("🛑 Edit operation cancelled."); return
        calibration_date = raw_cal or instrument['calibration_date']

        raw_next_cal = get_valid_date(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ", allow_empty=True)
        if raw_next_cal is None: print("🛑 Edit operation cancelled."); return
        next_calibration_date = raw_next_cal or instrument['next_calibration_date']
        
        # 🛡️ UPGRADE 1: Verification gate block inside editor engine
        if next_calibration_date <= calibration_date:
            print("❌ Compliance Error: Next calibration date cannot be before or equal to the calibration date! Update aborted.")
            return
        
        location = input(f"Location ({instrument['location']}): ").strip() or instrument['location']
        status = get_valid_status(f"Status (Active/Inactive) ({instrument['status']}): ", allow_empty=True) or instrument['status']
        instrument_type = input(f"Type of instrument ({instrument['instrument_type']}): ").strip() or instrument['instrument_type']

        changes_tracked = []
        if instrument['status'] != status: changes_tracked.append(f"Status shifted from '{instrument['status']}' to '{status}'")
        if instrument['calibration_date'] != calibration_date: changes_tracked.append(f"Last Cal shifted from {instrument['calibration_date']} to {calibration_date}")
        if instrument['next_calibration_date'] != next_calibration_date: changes_tracked.append(f"Next Cal deadline shifted from {instrument['next_calibration_date']} to {next_calibration_date}")

        audit_details = " | ".join(changes_tracked) if changes_tracked else "Equipment properties updated (High-stakes timelines unchanged)."

        cursor.execute("""
            UPDATE instruments 
            SET name = ?, manufacturer = ?, calibration_date = ?, next_calibration_date = ?, location = ?, status = ?, instrument_type = ?
            WHERE id = ?
        """, (name, manufacturer, calibration_date, next_calibration_date, location, status, instrument_type, instrument['id']))
        
        log_change(cursor, instrument['id'], instrument['serial'], "EDIT", audit_details)
        print("📝 Instrument updated successfully in SQLite!")

def search_instruments():
    """Provides dynamic cross-column sweeping while avoiding archived rows."""
    print("\n--- Search Filter Options (SQL Pure Mode) ---")
    print("1. Search by Serial Number")
    print("2. Search by Instrument Name")
    print("3. Search by Manufacturer")
    print("4. Search by Instrument Type")
    print("5. 🔍 Search All Fields (Global Search)") 
    
    sub_choice = input("Select search criteria (1-5): ").strip()
    search_term = input("Enter your search keyword: ").strip()
    query_param = f"%{search_term}%"
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        base_query = "SELECT * FROM instruments WHERE is_deleted = 0 AND "
        if sub_choice == "1": cursor.execute(base_query + "LOWER(serial) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "2": cursor.execute(base_query + "LOWER(name) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "3": cursor.execute(base_query + "LOWER(manufacturer) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "4": cursor.execute(base_query + "LOWER(instrument_type) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "5":
            cursor.execute(base_query + """(LOWER(serial) LIKE LOWER(?)
                            OR LOWER(name) LIKE LOWER(?)
                            OR LOWER(manufacturer) LIKE LOWER(?)
                            OR LOWER(instrument_type) LIKE LOWER(?)
                            OR LOWER(location) LIKE LOWER(?)
                            OR LOWER(status) LIKE LOWER(?))""", [query_param]*6)
        else:
            print("❌ Invalid choice."); return

        results = cursor.fetchall()

    if not results: print("No matching active instruments found."); return
    print(f"\n=== SEARCH RESULTS ({len(results)} Active Matches Found) ===")
    for instrument in results:
        print(f"[ ID: {instrument['id']} | Match: {instrument['name']} ]\n• Serial: {instrument['serial']} | Status: {instrument['status']} | Location: {instrument['location']}")

def view_due_soon():
    """Queries SQLite for active assets requiring calibration within 30 days or already overdue."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Pull all active, non-archived instruments to evaluate them in Python
        cursor.execute("SELECT * FROM instruments WHERE is_deleted = 0 AND status = 'Active'")
        instruments = cursor.fetchall()

    if not instruments:
        print("🎉 No active instruments found in the registry.")
        return

    today = datetime.now().date()
    due_instruments = []

    for instrument in instruments:
        try:
            # Parse the text date cleanly using Python's verified engine
            next_cal = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
            days_left = (next_cal - today).days
            
            # Catch anything already overdue (days_left < 0) or due within the next 30 days
            if days_left <= 30:
                due_instruments.append((instrument, days_left))
        except ValueError:
            # Gracefully skip any legacy, badly-formatted test entries from older versions
            continue

    # Sort entries by urgency (most overdue items float to the very top)
    due_instruments.sort(key=lambda x: x[1])

    if not due_instruments:
        print("🎉 No active instruments are due for calibration in the next 30 days.")
        return

    print("\n⏳ --- Instruments Due Soon / Overdue (Python Verified Engine) ---")
    for instrument, days_left in due_instruments:
        if days_left < 0:
            status_msg = f"🚨 OVERDUE by {abs(days_left)} days!"
        elif days_left == 0:
            status_msg = "⚠️ DUE TODAY!"
        else:
            status_msg = f"⏳ {days_left} days remaining"

        print(f"""
• Name:                  {instrument['name']}
• Serial:                {instrument['serial']}
• Next Calibration Date: {instrument['next_calibration_date']}
• Timeline Status:       {status_msg}
---------------------------------------""")

# ==========================================
# 🧪 NEW: METROLOGY CALIBRATION EVENTS LOGIC
# ==========================================

def record_calibration():
    """🧪 Captures raw laboratory validation metadata and logs an traceable Calibration Event."""
    print("\n--- Record New Laboratory Calibration Event ---")
    serial = input("Enter the instrument serial number: ").strip()
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instruments WHERE LOWER(serial) = LOWER(?) AND is_deleted = 0", (serial,))
        instrument = cursor.fetchone()
        
    if not instrument:
        print("❌ No active instrument found with that serial number.")
        return

    print(f"🎯 Registering event logs for: {instrument['name']} ({instrument['id']})")
    technician = input("Technician Name: ").strip()
    standard_used = input("Reference Standard/Block Used (Traceability ID): ").strip()
    
    try:
        temperature = float(input("Ambient Temperature (°C): ").strip())
        humidity = float(input("Relative Humidity (%RH): ").strip())
    except ValueError:
        print("❌ Mathematical Error: Temperature and Humidity must be real numbers.")
        return

    pass_fail = input("Calibration Verdict (Type 'Pass' or 'Fail'): ").strip().capitalize()
    if pass_fail not in ['Pass', 'Fail']:
        print("❌ Validation Error: Verdict must be exactly 'Pass' or 'Fail'.")
        return

    notes = input("Operational/Tolerance notes: ").strip()

    # Timeline confirmation rules
    while True:
        cal_date = get_valid_date("Date Calibration Performed (YYYY-MM-DD): ")
        if cal_date is None: return
        next_cal_date = get_valid_date("Next Calibration Deadline (YYYY-MM-DD): ")
        if next_cal_date is None: return
        
        if next_cal_date > cal_date:
            break
        print("❌ Timeline Error: Next calibration must occur AFTER the execution date.")

    # Execute Atomic Multi-Table Transaction
    with sqlite3.connect("metrology.db") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        
        try:
            # 1. Insert records to Calibration events history repository
            cursor.execute("""
                INSERT INTO calibration_events (
                    instrument_id, cal_date, next_cal_date, technician, 
                    standard_used, temperature, humidity, pass_fail, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (instrument['id'], cal_date, next_cal_date, technician, standard_used, temperature, humidity, pass_fail, notes))
            
            # 2. Update active properties inside Main Inventory table
            new_status = "Active" if pass_fail == "Pass" else "Inactive"
            cursor.execute("""
                UPDATE instruments 
                SET calibration_date = ?, next_calibration_date = ?, status = ?
                WHERE id = ?
            """, (cal_date, next_cal_date, new_status, instrument['id']))
            
            # 3. Secure snapshot change marker on the global audit trail
            log_change(
                cursor, 
                instrument['id'], 
                instrument['serial'], 
                "CALIBRATE", 
                f"Calibrated by {technician}. Result: {pass_fail} | Next Due: {next_cal_date} | Temp: {temperature}°C, RH: {humidity}%"
            )
            print(f"✅ Calibration event securely integrated! Inventory data adjusted to: '{new_status}'")
        except sqlite3.Error as e:
            print(f"❌ Database Transaction Interrupted: {e}")

def view_calibration_history():
    """Chronologically loops calibration metrics tracking parameters for verification audits."""
    serial = input("Enter instrument serial number to verify calibration history: ").strip()
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ce.*, i.name as inst_name, i.serial as inst_serial 
            FROM calibration_events ce
            JOIN instruments i ON ce.instrument_id = i.id
            WHERE LOWER(i.serial) = LOWER(?)
            ORDER BY ce.event_id DESC
        """, (serial,))
        events = cursor.fetchall()

    if not events:
        print("ℹ️ No historical execution records found for this instrument.")
        return

    print(f"\n📜 ============ CALIBRATION LOG TIMELINE: {events[0]['inst_name'].upper()} ============")
    for ev in events:
        verdict_icon = "🟢" if ev['pass_fail'] == "Pass" else "🔴"
        print(f"""[Event ID: {ev['event_id']}] Execution Date: {ev['cal_date']}
• Technician:       {ev['technician']}
• Reference ID:     {ev['standard_used']}
• Environment:      🌡️ {ev['temperature']}°C | 💧 {ev['humidity']}% RH
• Status Verdict:   {verdict_icon} {ev['pass_fail'].upper()}
• Next Recall Due:  {ev['next_cal_date']}
• Technician Notes: {ev['notes'] if ev['notes'] else 'N/A'}
-------------------------------------------------------------------------""")
    print("=========================================================================")

# ==========================================
# ANALYTICS ENGINE & MAIN SYSTEM LOOP
# ==========================================

def view_dashboard():
    """Generates real-time inventory metrics."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instruments WHERE is_deleted = 0")
        instruments = cursor.fetchall()

    total_assets = len(instruments)
    if total_assets == 0:
        print("\n📊 Dashboard Empty: No instruments registered in the system.")
        return

    active_count = sum(1 for i in instruments if i["status"] == "Active")
    overdue_count = 0
    type_distribution = {}
    today = datetime.now().date()

    for instrument in instruments:
        itype = instrument["instrument_type"].strip().title()
        type_distribution[itype] = type_distribution.get(itype, 0) + 1
        next_cal = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
        if (next_cal - today).days < 0: overdue_count += 1

    health_percentage = ((total_assets - overdue_count) / total_assets) * 100

    print(f"\n=======================================\n📊 LAB ANALYTICS DASHBOARD\n=======================================")
    print(f"• Total Active Inventory:   {total_assets} units\n• Operational Status:       🟢 {active_count} Active | 🔴 {total_assets - active_count} Inactive")
    print(f"• Lab Health Rating:        🛡️  {health_percentage:.1f}%\n• Recalibration Deficits:   🚨 {overdue_count} Overdue Instruments")
    print("---------------------------------------\n⚙️  EQUIPMENT DISTRIBUTION TYPE:")
    for itype, count in type_distribution.items(): print(f"  - {itype}: {count} unit(s)")
    print("=======================================")        

def main():
    init_db()
    legacy_instruments = load_instruments()
    migrate_json_to_sqlite(legacy_instruments)
    
    while True:
        print("\n=== Metrology Management System (v2.5 Lab-Ready Prototype) ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Archive/Delete Instrument (Soft Delete)")
        print("4. Edit Instrument")
        print("5. Search Instrument (Global Search)")
        print("6. View Instruments Due Soon (30 Days or Less)")
        print("7. 🧪 Record New Calibration Event")
        print("8. 📜 View Calibration History Timeline")
        print("9. View Lab Analytics Dashboard")
        print("10. View Regulatory Audit History Logs")
        print("11. Exit")

        choice = input("Choose an option: ")

        if choice == "1": add_instrument()
        elif choice == "2": view_instruments()
        elif choice == "3": delete_instrument()
        elif choice == "4": edit_instrument()
        elif choice == "5": search_instruments()
        elif choice == "6": view_due_soon()
        elif choice == "7": record_calibration()
        elif choice == "8": view_calibration_history()
        elif choice == "9": view_dashboard()
        elif choice == "10": view_audit_history()
        elif choice == "11":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick an option from 1 to 11.")

if __name__ == "__main__":
    main()