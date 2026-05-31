def main():
    while True:
        print("\n=== Metrology Management System ===")
        print("1. Add Instrument")
        print("2. View Instruments")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            print("Add Instrument selected")

        elif choice == "2":
            print("View Instruments selected")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice")


main()