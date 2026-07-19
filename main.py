from database import (
    create_table,
    add_guest,
    check_out_guest,
    get_all_guests,
    get_active_guests
)
from datetime import datetime

create_table()

print("\n=== Guest Check-In / Check-Out System ===")
print("1. Guest Check-In")
print("2. Guest Check-Out")
print("3. View All Guests")

choice = input("Select option (1 / 2 / 3): ")

if choice == "1":
    name = input("Guest name: ")
    purpose = input("Purpose of visit: ")

    check_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_guest(name, purpose, check_in)

    print("\nGuest checked in successfully!")
    print("Check-in time:", check_in)

elif choice == "2":
    active_guests = get_active_guests()

    if not active_guests:
        print("\nNo active guests to check out.")
    else:
        print("\n--- Active Guests ---")
        for g in active_guests:
            print(f"ID: {g[0]} | Name: {g[1]} | Purpose: {g[2]} | Check-in: {g[3]}")

        guest_id = input("\nEnter Guest ID to check out: ")
        time_out = check_out_guest(guest_id)

        if time_out is None:
            print("Checkout failed. Wrong ID or already checked out.")
        else:
            print("\nGuest checked out successfully!")
            print("Check-out time:", time_out)

elif choice == "3":
    guests = get_all_guests()

    print("\n--- Guest List ---")
    for guest in guests:
        print(
            f"ID: {guest[0]} | "
            f"Name: {guest[1]} | "
            f"Purpose: {guest[2]} | "
            f"Check-in: {guest[3]} | "
            f"Check-out: {guest[4]}"
        )

else:
    print("Invalid option")