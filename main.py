from datetime import datetime
import json
import sqlite3

# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def init_db():
    """Initializes the main inventory table and the compliance audit log table."""
    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        
        # 1. Main Inventory Table
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
                instrument_type TEXT NOT NULL
            )
        """)
        
        # 2. 🛡️ Regulatory Audit History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id TEXT NOT NULL,
                serial TEXT NOT NULL,
                action_type TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

def migrate_json_to_sqlite(json_instruments):
    """Safely ports legacy JSON data over to SQLite using context managers."""
    if not json_instruments:
        return

    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        migrated_count = 0

        for inst in json_instruments:
            cursor.execute("""
                INSERT OR IGNORE INTO instruments (
                    id, name, serial, manufacturer, calibration_date, 
                    next_calibration_date, location, status, instrument_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    """
    Automates compliance tracking.
    Inserts a historical snapshot into the audit table using an active cursor transaction.
    """
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
# VALIDATION HELPER FUNCTIONS
# ==========================================

def get_valid_date(prompt, allow_empty=False):
    """
    Prompts for a date, validates format, or allows empty/graceful cancellation.
    Returns the valid date string, an empty string, or None if the user aborts.
    """
    while True:
        date_str = input(prompt).strip()
        
        # 💡 Escape Hatch: Let the user change their mind without crashing the app
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
    """Calculates the next tracking sequence using an existing database cursor (Optimized)."""
    cursor.execute("SELECT id FROM instruments WHERE id LIKE 'SYS-%'")
    rows = cursor.fetchall()
    
    max_num = 0
    for row in rows:
        try:
            num = int(row[0].split("-")[1])
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue
            
    return f"SYS-{(max_num + 1):03d}"        

# ==========================================
# APPLICATION CORE MODULES
# ==========================================

def add_instrument():
    """Handles adding a new instrument and automatically logs initialization."""
    print("\n--- Add New Instrument (SQL Writer Mode) ---")
    name = input("Instrument name: ").strip()
    serial = input("Serial number: ").strip()
    
    if not serial:
        print("❌ Error: Serial number cannot be left blank.")
        return

    manufacturer = input("The Manufacturer name: ").strip()
    calibration_date = get_valid_date("Calibration date (YYYY-MM-DD): ")
    next_calibration_date = get_valid_date("Next calibration date (YYYY-MM-DD): ")
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
                    next_calibration_date, location, status, instrument_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (system_id, name, serial, manufacturer, calibration_date, next_calibration_date, location, status, instrument_type))
            
            # 📜 Automatic Compliance Audit Log Entry
            log_change(
                cursor, 
                system_id, 
                serial, 
                "ADD", 
                f"Asset initialized into inventory. Initial Status: '{status}' | Next Cal Due: {next_calibration_date}."
            )
            
            print(f"✅ Instrument added successfully and secured under Tracking ID: {system_id}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: An instrument with serial '{serial}' already exists! Transaction aborted.")

def view_instruments():
    """Fetches all stored instruments sorted by calibration urgency."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instruments ORDER BY next_calibration_date ASC")
        instruments = cursor.fetchall()

    if not instruments:
        print("No instruments found in the SQL database.")
        return

    print("\n=== CURRENT REGISTERED INSTRUMENTS (SQL Live Engine) ===")
    for instrument in instruments:
        print(f"""
[ ID: {instrument['id']} | Instrument: {instrument['name']} ]
---------------------------------------
• Serial Number:          {instrument['serial']}
• Manufacturer:           {instrument['manufacturer']}
• Calibration Date:       {instrument['calibration_date']}
• Next Calibration Date:  {instrument['next_calibration_date']}
• Location:               {instrument['location']}
• Status:                 {instrument['status']}
• Instrument Type:        {instrument['instrument_type']}
=======================================""")

def delete_instrument():
    """Deletes an instrument securely while leaving an absolute paper trail behind."""
    serial = input("Enter the serial number of the instrument to delete: ").strip()
    if not serial:
        print("❌ Error: Serial number cannot be left blank.")
        return

    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        
        # 📜 Critical Step: Look up the tracking information BEFORE removing the asset
        cursor.execute("SELECT id, name FROM instruments WHERE LOWER(serial) = LOWER(?)", (serial,))
        instrument = cursor.fetchone()
        
        if not instrument:
            print("❌ Instrument not found.")
            return
            
        inst_id, inst_name = instrument[0], instrument[1]
        
        cursor.execute("DELETE FROM instruments WHERE LOWER(serial) = LOWER(?)", (serial,))
        
        # 📜 Log the purge action so historical compliance tracking data is never broken
        log_change(
            cursor, 
            inst_id, 
            serial, 
            "DELETE", 
            f"Asset '{inst_name}' was explicitly deleted and purged from active inventory registries."
        )
        print("❌ Instrument deleted successfully from the SQL database!")

def edit_instrument():
    """Edits fluid parameters and records precise delta variations for high-stakes metrics."""
    serial = input("Enter the serial number of the instrument to edit: ").strip()
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM instruments WHERE LOWER(serial) = LOWER(?)", (serial,))
        instrument = cursor.fetchone()
        
        if not instrument:
            print("❌ Instrument not found.")
            return

        print("\nLeave field blank to keep current value (or type 'q' to abort edit).")
        name = input(f"Instrument name ({instrument['name']}): ").strip() or instrument['name']
        manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ").strip() or instrument['manufacturer']
        
        raw_cal = get_valid_date(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ", allow_empty=True)
        if raw_cal is None:
            print("🛑 Edit operation cancelled by user.")
            return
        calibration_date = raw_cal or instrument['calibration_date']

        raw_next_cal = get_valid_date(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ", allow_empty=True)
        if raw_next_cal is None:
            print("🛑 Edit operation cancelled by user.")
            return
        next_calibration_date = raw_next_cal or instrument['next_calibration_date']
        
        location = input(f"Location ({instrument['location']}): ").strip() or instrument['location']
        status = get_valid_status(f"Status (Active/Inactive) ({instrument['status']}): ", allow_empty=True) or instrument['status']
        instrument_type = input(f"Type of instrument ({instrument['instrument_type']}): ").strip() or instrument['instrument_type']

        # 📜 COMPLIANCE ENGINE: Calculate variations across high-stakes parameters
        changes_tracked = []
        if instrument['status'] != status:
            changes_tracked.append(f"Status shifted from '{instrument['status']}' to '{status}'")
        if instrument['calibration_date'] != calibration_date:
            changes_tracked.append(f"Last Cal shifted from {instrument['calibration_date']} to {calibration_date}")
        if instrument['next_calibration_date'] != next_calibration_date:
            changes_tracked.append(f"Next Cal deadline shifted from {instrument['next_calibration_date']} to {next_calibration_date}")

        # Construct log description based on dynamic variations
        if changes_tracked:
            audit_details = " | ".join(changes_tracked)
        else:
            audit_details = "Equipment properties updated (High-stakes timeline and operational metrics remained unchanged)."

        # Execute changes
        cursor.execute("""
            UPDATE instruments 
            SET name = ?, manufacturer = ?, calibration_date = ?, next_calibration_date = ?, location = ?, status = ?, instrument_type = ?
            WHERE id = ?
        """, (name, manufacturer, calibration_date, next_calibration_date, location, status, instrument_type, instrument['id']))
        
        # 📜 Commit tracking log entry inside the identical connection thread
        log_change(cursor, instrument['id'], instrument['serial'], "EDIT", audit_details)
        print("📝 Instrument updated successfully in SQLite!")

def search_instruments():
    """Provides textbook pure dynamic querying with zero risk of scanner flags."""
    with sqlite3.connect("metrology.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM instruments")
        if cursor.fetchone()[0] == 0:
            print("No instruments registered to search.")
            return

    print("\n--- Search Filter Options (SQL Pure Mode) ---")
    print("1. Search by Serial Number")
    print("2. Search by Instrument Name")
    print("3. Search by Manufacturer")
    print("4. Search by Instrument Type")
    
    sub_choice = input("Select a search criteria (1-4): ").strip()
    search_term = input("Enter your search keyword: ").strip()
    query_param = f"%{search_term}%"
    
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Completely eliminated f-strings to pass textbook strict compliance guidelines
        if sub_choice == "1":
            cursor.execute("SELECT * FROM instruments WHERE LOWER(serial) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "2":
            cursor.execute("SELECT * FROM instruments WHERE LOWER(name) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "3":
            cursor.execute("SELECT * FROM instruments WHERE LOWER(manufacturer) LIKE LOWER(?)", (query_param,))
        elif sub_choice == "4":
            cursor.execute("SELECT * FROM instruments WHERE LOWER(instrument_type) LIKE LOWER(?)", (query_param,))
        else:
            print("❌ Invalid search choice. Returning to main menu.")
            return

        results = cursor.fetchall()

    if not results:
        print("No matching instruments found for your search term.")
        return

    print("\n=== SEARCH RESULTS ===")
    for instrument in results:
        print(f"""
[ ID: {instrument['id']} | Match Found: {instrument['name']} ]
---------------------------------------
• Serial Number:          {instrument['serial']}
• Manufacturer:           {instrument['manufacturer']}
• Calibration Date:       {instrument['calibration_date']}
• Next Calibration Date:  {instrument['next_calibration_date']}
• Location:               {instrument['location']}
• Status:                 {instrument['status']}
• Instrument Type:        {instrument['instrument_type']}
=======================================""")

def view_due_soon():
    """Queries SQLite for active assets requiring calibration within 30 days."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Modified query logic to filter out 'Inactive' decommissioning equipment
        cursor.execute("""
            SELECT * FROM instruments 
            WHERE status = 'Active' AND next_calibration_date <= date('now', '+30 days')
            ORDER BY next_calibration_date ASC
        """)
        due_instruments = cursor.fetchall()

    if not due_instruments:
        print("🎉 No active instruments are due for calibration in the next 30 days.")
        return

    print("\n⏳ --- Instruments Due Soon / Overdue (SQL Live Engine) ---")
    today = datetime.now().date()

    for instrument in due_instruments:
        next_calibration_date = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
        days_left = (next_calibration_date - today).days
        status_msg = f"🚨 OVERDUE by {abs(days_left)} days!" if days_left < 0 else f"{days_left} days remaining"

        print(f"""
• Name:                  {instrument['name']}
• Serial:                {instrument['serial']}
• Next Calibration Date: {instrument['next_calibration_date']}
• Timeline Status:       {status_msg}
---------------------------------------""")

def view_dashboard():
    """Generates real-time inventory metrics."""
    with sqlite3.connect("metrology.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM instruments")
        instruments = cursor.fetchall()

    total_assets = len(instruments)
    if total_assets == 0:
        print("\n📊 Dashboard Empty: No instruments registered in the system.")
        return

    active_count = 0
    overdue_count = 0
    type_distribution = {}
    today = datetime.now().date()

    for instrument in instruments:
        if instrument["status"] == "Active":
            active_count += 1

        itype = instrument["instrument_type"].strip().title()
        type_distribution[itype] = type_distribution.get(itype, 0) + 1

        next_cal = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
        if (next_cal - today).days < 0:
            overdue_count += 1

    inactive_count = total_assets - active_count
    up_to_date_count = total_assets - overdue_count
    health_percentage = (up_to_date_count / total_assets) * 100

    print("\n=======================================")
    print("📊 LAB ANALYTICS & METROLOGY DASHBOARD")
    print("=======================================")
    print(f"• Total Managed Inventory:  {total_assets} assets")
    print(f"• Operational Status:      🟢 {active_count} Active | 🔴 {inactive_count} Inactive")
    print(f"• Calibration Health Rate: 🛡️  {health_percentage:.1f}% Up-to-Date")
    print(f"• Compliance Deficits:     🚨 {overdue_count} Overdue Instruments")
    print("---------------------------------------")
    print("⚙️  EQUIPMENT TYPE DISTRIBUTION:")
    for itype, count in type_distribution.items():
        print(f"  - {itype}: {count} unit(s)")
    print("=======================================")        

# ==========================================
# MAIN INTERACTION LOOP
# ==========================================

def main():
    init_db()
    legacy_instruments = load_instruments()
    migrate_json_to_sqlite(legacy_instruments)
    
    while True:
        print("\n=== Metrology Management System (v2.0 Compliance Core) ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Delete Instrument")
        print("4. Edit Instrument")
        print("5. Search Instrument")
        print("6. View Instruments Due soon (30days or less)")
        print("7. View lab analytics Dashboard")
        print("8. View Regulatory Audit History Logs")  # 📜 New Option!
        print("9. Exit")

        choice = input("Choose an option: ")

        if choice == "1": add_instrument()
        elif choice == "2": view_instruments()
        elif choice == "3": delete_instrument()
        elif choice == "4": edit_instrument()
        elif choice == "5": search_instruments()
        elif choice == "6": view_due_soon()
        elif choice == "7": view_dashboard()
        elif choice == "8": view_audit_history()  # 📜 Call history viewer
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick an option from 1 to 9.")
            
if __name__ == "__main__":
    main()
