def main():
    instruments = []
    while True:
        print("\n=== Metrology Management System ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            name = input("Instrument name: ")
            serial = input("Serial number: ")

            instrument = {
            "name": name,
            "serial": serial
            }

            instruments.append(instrument)

            print("Instrument added successfully!")

        elif choice == "2":
            if len(instrument) == 0:
               print("No instruments found.")
            else:
               print("\n--- Instruments ---")

               for instrument in instruments:
                   print(
                       f"Name: {instrument['name']} | "
                       f"Serial: {instrument['serial']}" 
                   )   

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice")


main()