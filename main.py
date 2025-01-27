import sys

def show_menu():
    print("\nWelcome to OpenCyb3r")
    print("=====================")
    print("1. Example Tool (Coming Soon)")
    print("2. Exit")
    return input("Choose an option: ")

def example_tool():
    print("\nExample Tool: Replace this with your tool's functionality.")
    input("Press Enter to return to the menu.")

def main():
    while True:
        choice = show_menu()
        if choice == "1":
            example_tool()
        elif choice == "2":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
