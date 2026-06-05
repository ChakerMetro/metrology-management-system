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
    Forces the user to input a valid date format (YYYY-MM-DD).
    If allow_empty is True, hitting enter without typing anything is allowed (for editing).
    """
    while True:
        date_str = input(prompt).strip()
        
        # If we are editing, an empty input means "don't change the date"
        if allow_empty and date_str == "":
            return ""

        try:
            # We try to parse the string using our date blueprint
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str  # If successful, exit the loop and pass back the clean date text
        except ValueError:
            # If datetime throws an error, catch it here instead of crashing!
            print("❌ Invalid date format! Please use exactly YYYY-MM-DD (e.g., 2026-06-05).")

def add_instrument(instruments):
    """Handles adding a new instrument to the system."""
    print("\n--- Add New Instrument ---")
    name = input("Instrument name: ")
    serial = input("Serial number: ")
    manufacturer = input("The Manufacturer name: ")
    calibration_date = get_valid_date("Calibration date (YYYY-MM-DD): ")
    next_calibration_date = get_valid_date("Next calibration date (YYYY-MM-DD): ")
    location = input("Location: ")
    status = input("Status (Active/Inactive): ")
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
    print("✅ Instrument added successfully!")


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
    serial = input("Enter the serial number of the instrument to edit: ")
    found = False

    for instrument in instruments:
        if instrument["serial"] == serial:
            print("\nLeave field blank to keep current value.")
            name = input(f"Instrument name ({instrument['name']}): ") or instrument['name']
            manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ") or instrument['manufacturer']
            calibration_date = get_valid_date(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ", allow_empty=True)
            next_calibration_date = get_valid_date(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ", allow_empty=True)
            location = input(f"Location ({instrument['location']}): ") or instrument['location']
            status = input(f"Status (Active) ({instrument['status']}): ") or instrument['status']
            instrument_type = input(f"Type of instrument ({instrument['instrument_type']}): ") or instrument['instrument_type']

            instrument.update({
                "name": name,
                "manufacturer": manufacturer,
                "calibration_date": calibration_date,
                "next_calibration_date": next_calibration_date,
                "location": location,
                "status": status,
                "instrument_type": instrument_type
            })

            save_instruments(instruments)
            print("📝 Instrument updated successfully!")
            found = True
            break

    if not found:
        print("Instrument not found.")


def search_instruments(instruments):
    """Searches for instruments by Name or Serial."""
    search_term = input("Enter the name or serial number of the instrument to search: ").lower()
    found = False

    for instrument in instruments:
        if instrument["serial"].lower() == search_term or search_term in instrument["name"].lower():
            print("\n🔍 --- Instrument Found ---")
            print(f"""
• Name:                  {instrument['name']}
• Serial:                {instrument['serial']}
• Manufacturer:          {instrument['manufacturer']}
• Next Calibration Date: {instrument['next_calibration_date']}
• Location:              {instrument['location']}
• Status:                {instrument['status']}
---------------------------------------""")
            found = True

    if not found:
        print("Instrument not found.")


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
        print("7. Exit")

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
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick an option from 1 to 7.")

# This triggers our program to run
main()