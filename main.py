def main():
    instruments = []
    while True:
        print("\n=== Metrology Management System ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Delete Instrument")
        print("4. Exit")

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
                    print("Instrument deleted successfully!")
                    found = True
                    break

            if not found:
                print("Instrument not found.")           

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice")


main()