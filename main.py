from datetime import datetime
import json

def save_instruments(instruments):
    with open("instruments.json", "w") as file:
        json.dump(instruments, file, indent=4)

def load_instruments():
    try:
        with open("instruments.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

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
            name = input("Instrument name: ")
            serial = input("Serial number: ")
            manufacturer = input("The Manufacturer name: ")
            calibration_date = input("Calibration date (YYYY-MM-DD): ")
            next_calibration_date = input("Next calibration date (YYYY-MM-DD): ")
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
            print("Instrument added successfully!")

        elif choice == "2":
            if len(instruments) == 0:
               print("No instruments found.")
            else:
               print("\n--- Instruments ---")

               for instrument in instruments:
                   print(
                       f"Name: {instrument['name']} | "
                       f"Serial: {instrument['serial']} | "
                       f"Manufacturer: {instrument['manufacturer']} | "
                       f"Calibration Date: {instrument['calibration_date']} | "
                       f"Next Calibration Date: {instrument['next_calibration_date']} | "
                       f"Location: {instrument['location']} | "
                       f"Status: {instrument['status']} | "
                       f"instrument_type: {instrument['instrument_type']}"
                   )
        elif choice == "3":
            serial = input("Enter the serial number of the instrument to delete: ")
            found = False

            for instrument in instruments:
                if instrument["serial"] == serial:
                    instruments.remove(instrument)
                    save_instruments(instruments)
                    print("Instrument deleted successfully!")
                    found = True
                    break

            if not found:
                print("Instrument not found.") 
        elif choice == "4":
            serial = input("Enter the serial number of the instrument to edit: ")
            found = False

            for instrument in instruments:
                if instrument["serial"] == serial:
                    print("Leave field blank to keep current value.")
                    name = input(f"Instrument name ({instrument['name']}): ") or instrument['name']
                    manufacturer = input(f"The Manufacturer name ({instrument['manufacturer']}): ") or instrument['manufacturer']
                    calibration_date = input(f"Calibration date (YYYY-MM-DD) ({instrument['calibration_date']}): ") or instrument['calibration_date']
                    next_calibration_date = input(f"Next calibration date (YYYY-MM-DD) ({instrument['next_calibration_date']}): ") or instrument['next_calibration_date']
                    location = input(f"Location ({instrument['location']}): ") or instrument['location']
                    status = input(f"Status (Active/Inactive) ({instrument['status']}): ") or instrument['status']
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
                    print("Instrument updated successfully!")
                    found = True
                    break

            if not found:
                print("Instrument not found.") 
                             
        elif choice == "5":
            search_term = input(
                "Enter the name or serial number of the instrument to search: "
            ).lower()

            found = False

            for instrument in instruments:
                if (
                    instrument["serial"].lower() == search_term
                    or search_term in instrument["name"].lower()
                ):
                    print("\n--- Instrument Found ---")
                    print(
                        f"Name: {instrument['name']} | "
                        f"Serial: {instrument['serial']} | "
                        f"Manufacturer: {instrument['manufacturer']} | "
                        f"Calibration Date: {instrument['calibration_date']} | "
                        f"Next Calibration Date: {instrument['next_calibration_date']} | "
                        f"Location: {instrument['location']} | "
                        f"Status: {instrument['status']} | "
                        f"Instrument Type: {instrument['instrument_type']}"
                    )
                    found = True

            if not found:
                print("Instrument not found.")
                
        elif choice == "6":
            # View instruments due soon (30 days or less) or overdue
            due_soon = []
            today = datetime.now().date()

            for instrument in instruments:
                next_calibration_date = datetime.strptime(instrument['next_calibration_date'], "%Y-%m-%d").date()
                days_until_calibration = (next_calibration_date - today).days

                # Changed '0 <=' to include negative numbers (overdue tools)
                if days_until_calibration <= 30:
                    # We save the instrument AND its specific days remaining together
                    due_soon.append((instrument, days_until_calibration))

            if due_soon:
                print("\n--- Instruments Due Soon / Overdue ---")
                # Loop through our pairs cleanly
                for instrument, days_left in due_soon:
                    # If days_left is negative, it's overdue!
                    if days_left < 0:
                        status_msg = f"🚨 OVERDUE by {abs(days_left)} days!"
                    else:
                        status_msg = f"{days_left} days remaining"

                    print(
                        f"Name: {instrument['name']} | "
                        f"Serial: {instrument['serial']} | "
                        f"Next Calibration Date: {instrument['next_calibration_date']} | "
                        f"Timeline: {status_msg}"
                    )
            else:
                print("No instruments are due for calibration in the next 30 days.")
                
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice")


main()