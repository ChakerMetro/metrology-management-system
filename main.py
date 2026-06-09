from datetime import datetime
import json
import sqlite3

# ==========================================
# DATABASE FUNCTIONS
# ==========================================

from datetime import datetime

def init_db():
    """Initializes the SQLite database and creates the instruments table if it doesn't exist."""
    # Connects to metrology.db (creates it automatically if it doesn't exist)
    conn = sqlite3.connect("metrology.db")
    cursor = conn.cursor()
    
    # Create the table using our strict schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            serial TEXT UNIQUE NOT NULL,
            manufacturer TEXT NOT NULL,
            calibration_date TEXT NOT NULL,
            next_calibration_date TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL,
            instrument_type TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def migrate_json_to_sqlite(json_instruments):
    """Safely ports existing legacy JSON instruments over to the new SQLite database."""
    if not json_instruments:
        return

    conn = sqlite3.connect("metrology.db")
    cursor = conn.cursor()
    migrated_count = 0

    for inst in json_instruments:
        # INSERT OR IGNORE checks the PRIMARY KEY (id). If it already exists, SQL skips it seamlessly!
        cursor.execute("""
            INSERT OR IGNORE INTO instruments (
                id, name, serial, manufacturer, calibration_date, 
                next_calibration_date, location, status, instrument_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inst.get("id"),
            inst.get("name"),
            inst.get("serial"),
            inst.get("manufacturer"),
            inst.get("calibration_date"),
            inst.get("next_calibration_date"),
            inst.get("location"),
            inst.get("status"),
            inst.get("instrument_type")
        ))
        
        # cursor.rowcount lets us know if a row was actually inserted or skipped
        if cursor.rowcount > 0:
            migrated_count += 1

    conn.commit()
    conn.close()

    if migrated_count > 0:
        print(f"📦 Database Bridge: Successfully migrated {migrated_count} assets from JSON to SQLite!")    

# ==========================================
# FILE HANDLING FUNCTIONS
# ==========================================

def save_instruments(instruments):
    """Saves the current instrument list to a JSON file."""
    with open("instruments.json", "w") as file:
        json.dump(instruments, file, indent=4)

def load_instruments():
    """Loads instruments from the JSON file or returns an empty list."""
    try:
        with open("instruments.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# ==========================================
# APPLICATION FEATURE FUNCTIONS
# ==========================================
def get_valid_date(prompt, allow_empty=False):
    """
    Prompts the user for a date and validates it against the YYYY-MM-DD format.
    If allow_empty is True, the user can hit enter to skip changing the date (used in edit mode).
    """
    while True:
        date_str = input(prompt).strip()
        
        if allow_empty and date_str == "":
            return ""

        try:
            # 1. Parse the date string into a real date object
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 2. Return it re-formatted! This forces "2026-6-5" to become "2026-06-05"
            return parsed_date.strftime("%Y-%m-%d")
            
        except ValueError:
            print("❌ Invalid date format! Please use exactly YYYY-MM-DD (e.g., 2026-06-05).")

def get_valid_status(prompt, allow_empty=False):
    """
    Forces the user to input exactly 'Active' or 'Inactive'.
    Automatically capitalizes input to maintain database consistency.
    """
    while True:
        status_input = input(prompt).strip().capitalize()
        
        # If editing, allow hitting enter to keep current value
        if allow_empty and status_input == "":
            return ""
            
        if status_input in ["Active", "Inactive"]:
            return status_input
            
        print("❌ Invalid input! Status must be exactly 'Active' or 'Inactive'.") 
        
def generate_next_id(instruments):
    """
    Scans existing instruments to find the highest numerical ID suffix
    and returns the next sequential ID (e.g., 'SYS-004').
    """
    max_num = 0
    for inst in instruments:
        if "id" in inst and inst["id"].startswith("SYS-"):
            try:
                # Extract the number after the hyphen
                num = int(inst["id"].split("-")[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
    return f"SYS-{(max_num + 1):03d}"                   

def add_instrument(instruments):
    """Handles adding a new instrument with duplicate-checking and status validation."""
    print("\n--- Add New Instrument ---")
    name = input("Instrument name: ").strip()
    
    # --- SAFEGUARD: Unique Serial Number Check ---
    while True:
        serial = input("Serial number: ").strip()
        # Scan the list to check for existing serial matches (case-insensitive)
        duplicate = False
        for inst in instruments:
            if inst["serial"].lower() == serial.lower():
                duplicate = True
                break
        
        if duplicate:
            print(f"❌ Error: An instrument with serial '{serial}' already exists! Serials must be unique.")
        elif serial == "":
            print("❌ Error: Serial number cannot be left blank.")
        else:
            # Serial is completely safe and unique! Break out of the validation loop.
            break

    manufacturer = input("The Manufacturer name: ").strip()
    calibration_date = get_valid_date("Calibration date (YYYY-MM-DD): ")
    next_calibration_date = get_valid_date("Next calibration date (YYYY-MM-DD): ")
    location = input("Location: ").strip()
    
    # --- SAFEGUARD: Enforced Status ---
    status = get_valid_status("Status (Active/Inactive): ")
    
    instrument_type = input("Type of instrument: ").strip()
    system_id = generate_next_id(instruments)

    instrument = {
        "id": system_id,
        "name": name,
        "serial": serial,
        "manufacturer": manufacturer,
        "calibration_date": calibration_date,
        "next_calibration_date": next_calibration_date,
        "location": location,
        "status": status,
        "instrument_type": instrument_type
    }

    instruments.append(instrument)
    save_instruments(instruments)
    print(f"✅ Instrument added successfully and secured under Tracking ID: {system_id}")

def view_instruments(instruments):
    """Displays all stored instruments in a clean layout, automatically sorted by calibration urgency."""
    if len(instruments) == 0:
        print("No instruments found.")
        return

    sorted_instruments = sorted(instruments, key=lambda x: x['next_calibration_date'])

    print("\n=== CURRENT REGISTERED INSTRUMENTS (Sorted by Calibration Urgency) ===")
    for instrument in sorted_instruments:
        display_id = instrument.get("id", "N/A")
        
        print(f"""
[ ID: {display_id} | Instrument: {instrument['name']} ]
---------------------------------------
• Serial Number:          {instrument['serial']}
• Manufacturer:           {instrument['manufacturer']}
• Calibration Date:       {instrument['calibration_date']}
• Next Calibration Date:  {instrument['next_calibration_date']}
• Location:               {instrument['location']}
• Status:                 {instrument['status']}
• Instrument Type:        {instrument['instrument_type']}
=======================================""")


def delete_instrument(instruments):
    """Finds and deletes an instrument by its serial number (case-insensitive)."""
    serial = input("Enter the serial number of the instrument to delete: ").strip()
    found = False

    for instrument in instruments:
        if instrument["serial"].lower() == serial.lower():
            instruments.remove(instrument)
            save_instruments(instruments)
            print("❌ Instrument deleted successfully!")
            found = True
            break

    if not found:
        print("❌ Instrument not found.")


def edit_instrument(instruments):
    """Edits an existing instrument's details using its serial number."""
    serial = input("Enter the serial number of the instrument to edit: ").strip()
    found = False

    for instrument in instruments:
        if instrument["serial"].lower() == serial.lower():
            print("\nLeave field blank to keep current value.")
            name = input(f"Instrument name ({instrument['name']}): ").strip() or instrument['name']
            manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ").strip() or instrument['manufacturer']
            calibration_date = get_valid_date(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ", allow_empty=True)
            next_calibration_date = get_valid_date(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ", allow_empty=True)
            location = input(f"Location ({instrument['location']}): ").strip() or instrument['location']
            status = get_valid_status(f"Status (Active/Inactive) ({instrument['status']}): ", allow_empty=True)
            instrument_type = input(f"Type of instrument ({instrument['instrument_type']}): ").strip() or instrument['instrument_type']

            instrument.update({
                "name": name,
                "manufacturer": manufacturer,
                "calibration_date": calibration_date if calibration_date != "" else instrument['calibration_date'],
                "next_calibration_date": next_calibration_date if next_calibration_date != "" else instrument['next_calibration_date'],
                "location": location,
                "status": status if status != "" else instrument['status'],
                "instrument_type": instrument_type
            })

            save_instruments(instruments)
            print("📝 Instrument updated successfully!")
            found = True
            break

    if not found:
        print("❌ Instrument not found.")

def search_instruments(instruments):
    """Provides a targeted sub-menu to search instruments by specific fields."""
    if len(instruments) == 0:
        print("No instruments registered to search.")
        return

    print("\n--- Search Filter Options ---")
    print("1. Search by Serial Number")
    print("2. Search by Instrument Name")
    print("3. Search by Manufacturer")
    print("4. Search by Instrument Type")
    
    sub_choice = input("Select a search criteria (1-4): ").strip()
    
    if sub_choice not in ["1", "2", "3", "4"]:
        print("❌ Invalid search choice. Returning to main menu.")
        return

    search_term = input("Enter your search keyword: ").strip().lower()
    found = False

    print("\n=== SEARCH RESULTS ===")
    for instrument in instruments:
        match = False
        
        if sub_choice == "1" and search_term in instrument["serial"].lower():
            match = True
        elif sub_choice == "2" and search_term in instrument["name"].lower():
            match = True
        elif sub_choice == "3" and search_term in instrument["manufacturer"].lower():
            match = True
        elif sub_choice == "4" and search_term in instrument["instrument_type"].lower():
            match = True

        if match:
            display_id = instrument.get("id", "N/A")
            print(f"""
[ ID: {display_id} | Match Found: {instrument['name']} ]
---------------------------------------
• Serial Number:          {instrument['serial']}
• Manufacturer:           {instrument['manufacturer']}
• Calibration Date:       {instrument['calibration_date']}
• Next Calibration Date:  {instrument['next_calibration_date']}
• Location:               {instrument['location']}
• Status:                 {instrument['status']}
• Instrument Type:        {instrument['instrument_type']}
=======================================""")
            found = True

    if not found:
        print("No matching instruments found for your search term.")


def view_due_soon(instruments):
    """Checks and displays instruments that are due for calibration within 30 days or overdue."""
    due_soon = []
    today = datetime.now().date()

    for instrument in instruments:
        next_calibration_date = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
        days_until_calibration = (next_calibration_date - today).days

        if days_until_calibration <= 30:
            due_soon.append((instrument, days_until_calibration))

    if due_soon:
        print("\n⏳ --- Instruments Due Soon / Overdue ---")
        for instrument, days_left in due_soon:
            if days_left < 0:
                status_msg = f"🚨 OVERDUE by {abs(days_left)} days!"
            else:
                status_msg = f"{days_left} days remaining"

            display_id = instrument.get("id", "N/A")
            print(f"""
• ID:                    {display_id}
• Name:                  {instrument['name']}
• Serial:                {instrument['serial']}
• Next Calibration Date: {instrument['next_calibration_date']}
• Timeline Status:       {status_msg}
---------------------------------------""")
    else:
        print("🎉 No instruments are due for calibration in the next 30 days.")

def view_dashboard(instruments):
    """Displays a high-level data analysis and health report of the lab inventory."""
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
        days_left = (next_cal - today).days
        if days_left < 0:
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
    migrate_json_to_sqlite(legacy_instruments)  # Ensure the database is initialized (even if we're not using it yet)
    instruments = load_instruments()
    
    # ⚙️ LEGACY DATA MIGRATION ENGINE
    migration_needed = False
    for inst in instruments:
        if "id" not in inst:
            inst["id"] = generate_next_id(instruments)
            migration_needed = True
            
    if migration_needed:
        save_instruments(instruments)
        print("⚙️ System: Database successfully migrated to Schema v1.0.0 (Tracking IDs added).")
        
    while True:
        print("\n=== Metrology Management System ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Delete Instrument")
        print("4. Edit Instrument")
        print("5. Search Instrument")
        print("6. View Instruments Due soon (30days or less)")
        print("7. View lab analytics Dashboard")
        print("8. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_instrument(instruments)
        elif choice == "2":
            view_instruments(instruments)
        elif choice == "3":
            delete_instrument(instruments)
        elif choice == "4":
            edit_instrument(instruments)
        elif choice == "5":
            search_instruments(instruments)
        elif choice == "6":
            view_due_soon(instruments)
        elif choice == "7":
            view_dashboard(instruments)
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick an option from 1 to 8.")

main()