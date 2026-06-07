from datetime import datetime
import json

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

def add_instrument(instruments):
    """Handles adding a new instrument with duplicate-checking and status validation."""
    print("\n--- Add New Instrument ---")
    name = input("Instrument name: ")
    
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

    manufacturer = input("The Manufacturer name: ")
    calibration_date = get_valid_date("Calibration date (YYYY-MM-DD): ")
    next_calibration_date = get_valid_date("Next calibration date (YYYY-MM-DD): ")
    location = input("Location: ")
    
    # --- SAFEGUARD: Enforced Status ---
    status = get_valid_status("Status (Active/Inactive): ")
    
    instrument_type = input("Type of instrument: ")

    instrument = {
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
    print("✅ Instrument added successfully and secured!")

def view_instruments(instruments):
    """Displays all stored instruments in a clean, vertical data sheet layout."""
    if len(instruments) == 0:
        print("No instruments found.")
        return

    print("\n=== CURRENT REGISTERED INSTRUMENTS ===")
    for instrument in instruments:
        print(f"""
[ Instrument: {instrument['name']} ]
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
    """Finds and deletes an instrument by its serial number."""
    serial = input("Enter the serial number of the instrument to delete: ")
    found = False

    for instrument in instruments:
        if instrument["serial"] == serial:
            instruments.remove(instrument)
            save_instruments(instruments)
            print("❌ Instrument deleted successfully!")
            found = True
            break

    if not found:
        print("Instrument not found.")


def edit_instrument(instruments):
    """Edits an existing instrument's details using its serial number."""
    serial = input("Enter the serial number of the instrument to edit: ").strip()
    found = False

    for instrument in instruments:
        if instrument["serial"].lower() == serial.lower():  # Added .lower() for safer matching!
            print("\nLeave field blank to keep current value.")
            name = input(f"Instrument name ({instrument['name']}): ") or instrument['name']
            manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ") or instrument['manufacturer']
            calibration_date = get_valid_date(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ", allow_empty=True)
            next_calibration_date = get_valid_date(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ", allow_empty=True)
            location = input(f"Location ({instrument['location']}): ") or instrument['location']
            status = get_valid_status(f"Status (Active/Inactive) ({instrument['status']}): ", allow_empty=True)
            instrument_type = input(f"Type of instrument ({instrument['instrument_type']}): ") or instrument['instrument_type']

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
    
    # Validation check for the sub-menu choice
    if sub_choice not in ["1", "2", "3", "4"]:
        print("❌ Invalid search choice. Returning to main menu.")
        return

    search_term = input("Enter your search keyword: ").strip().lower()
    found = False

    print("\n=== SEARCH RESULTS ===")
    for instrument in instruments:
        match = False
        
        # Determine matching logic based on user's sub-choice
        if sub_choice == "1" and search_term in instrument["serial"].lower():
            match = True
        elif sub_choice == "2" and search_term in instrument["name"].lower():
            match = True
        elif sub_choice == "3" and search_term in instrument["manufacturer"].lower():
            match = True
        elif sub_choice == "4" and search_term in instrument["instrument_type"].lower():
            match = True

        # If a match is found, print it using our clean vertical layout!
        if match:
            print(f"""
[ Match Found: {instrument['name']} ]
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

            print(f"""
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
        # 1. Parse Status Breakdown
        if instrument["status"] == "Active":
            active_count += 1

        # 2. Parse Type Distribution (Standardized to title case)
        itype = instrument["instrument_type"].strip().title()
        type_distribution[itype] = type_distribution.get(itype, 0) + 1

        # 3. Calculate Calibration Health Metric
        next_cal = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
        days_left = (next_cal - today).days
        if days_left < 0:
            overdue_count += 1

    # Compute calculations
    inactive_count = total_assets - active_count
    up_to_date_count = total_assets - overdue_count
    health_percentage = (up_to_date_count / total_assets) * 100

    # Print the Dashboard UI
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
    instruments = load_instruments()
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

        choice = input("Choose an option: ")

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

# This triggers our program to run
main()