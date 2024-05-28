import streamlit as st
import sqlite3
import pandas as pd
from passlib.hash import pbkdf2_sha256

# Your SQLite database connection
conn = sqlite3.connect('your_database.db')  # Replace 'your_database.db' with your actual database file
cursor = conn.cursor()

# Create 'admins' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

# Add an example admin (replace with actual admin credentials)
admin_username = "han"
admin_password = pbkdf2_sha256.hash("han@123")
cursor.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)", (admin_username, admin_password))

# Create 'packages' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        price REAL NOT NULL,
        details TEXT
    )
''')

# Create 'bookings' table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        package_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY (package_id) REFERENCES packages(id)
    )
''')

conn.commit()

# Streamlit app
st.set_page_config(page_title="Admin_Login", page_icon="🛡️")

# Page state management
if 'is_admin_authenticated' not in st.session_state:
    st.session_state.is_admin_authenticated = False

# Authentication page
if not st.session_state.is_admin_authenticated:
    st.title("Admin")

    # User inputs
    username_input = st.text_input("Enter Admin name:")
    password_input = st.text_input("Enter Password:", type="password")

    # Authentication logic
    if st.button("Login"):
        # Retrieve hashed password from the database
        cursor.execute("SELECT password FROM admins WHERE username=?", (username_input,))
        result = cursor.fetchone()

        if result and pbkdf2_sha256.verify(password_input, result[0]):
            st.success("Admin login successful! You can proceed.")
            st.session_state.is_admin_authenticated = True
        else:
            st.error("Admin login failed. Please check your credentials.")

# Admin Dashboard
elif st.session_state.is_admin_authenticated:
    st.title("Admin Dashboard")

    # Navigation menu
    page = st.sidebar.selectbox("Navigation", ["Create Packages", "Manage Packages", "Update Packages", "Admin Created Packages", "Manage Bookings", "Logout"])

    # Admin logout
    if page == "Logout":
        st.session_state.is_admin_authenticated = False
        st.success("Admin logged out successfully!")

    # Create Packages page
    elif page == "Create Packages":
        st.title("Create Packages")

        # Package creation form
        package_name = st.text_input("Enter Package Name:")
        package_location = st.selectbox("Package Type", ["Family", "Couple", "Other"])
        # package_type = st.text_input("Enter Package Location:")
        package_type = st.text_input("Enter Package Location:")
        package_price = st.number_input("Enter Package Price (in rupees):", min_value=0, step=1)
        package_features = st.text_input("Enter Package Features:")
        package_details = st.text_area("Enter Package Details:")
        # ... add other package details as needed

        if st.button("Create Package"):
            # Save package details to the database
            cursor.execute("INSERT INTO packages (type, price, details) VALUES (?, ?, ?)",
                           (package_type, package_price, package_details))
            conn.commit()

            st.success("Package created successfully!")

    # Manage Packages page
    elif page == "Manage Packages":
        st.title("Manage Packages")

        # Display available packages from the database in a table
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()

        if packages:
            st.subheader("Available Packages:")
            package_df = pd.DataFrame(packages, columns=["ID", "Location", "Price", "Details"])
            package_df["Price"] = package_df["Price"].apply(lambda x: f'₹ {x:.0f}')

            # Display package details in a DataFrame table
            st.table(package_df)

            # Delete individual package
            package_id_to_delete = st.number_input("Enter Package ID to delete:")
            if st.button("Delete Package"):
                # Delete package from the database
                cursor.execute("DELETE FROM packages WHERE id=?", (package_id_to_delete,))
                conn.commit()
                st.success("Package deleted successfully!")

        else:
            st.info("No packages available.")

    # Update Package page
    elif page == "Update Packages":
        st.subheader("Update Package:")
        package_id_to_update = st.number_input("Enter Package ID to update:")
        package_to_update = cursor.execute("SELECT * FROM packages WHERE id=?", (package_id_to_update,)).fetchone()

        if package_to_update:
            # Display the existing details for updating
            st.write(f"Existing details for Package ID {package_id_to_update}: {package_to_update}")

            # Update form
            new_package_type = st.text_input("Enter New Package Location:")
            new_package_price = st.number_input("Enter New Package Price (in rupees):", min_value=0, step=1)
            new_package_details = st.text_area("Enter New Package Details:")

            if st.button("Update Package"):
                # Update location, price, and details in the database
                cursor.execute("UPDATE packages SET type=?, price=?, details=? WHERE id=?",
                               (new_package_type, new_package_price, new_package_details, package_id_to_update))
                conn.commit()
                st.success("Package updated successfully!")

                # Display updated packages
                updated_packages = cursor.execute("SELECT * FROM packages").fetchall()
                updated_package_df = pd.DataFrame(updated_packages, columns=["ID", "Location", "Price", "Details"])
                updated_package_df["Price"] = updated_package_df["Price"].apply(lambda x: f'₹ {x:.0f}')
                st.subheader("Updated Packages:")
                st.table(updated_package_df)
            else:
                st.warning(f"No package found with ID {package_id_to_update}")
        else:
            st.info("No packages available.")

    # User Homepage page
    elif page == "Admin Created Packages":
        st.title("Admin Created Packages")

        # Display available packages from the database in a table
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()

        if packages:
            st.subheader("Available Packages:")
            package_df = pd.DataFrame(packages, columns=["ID", "Location", "Price", "Details"])
            package_df["Price"] = package_df["Price"].apply(lambda x: f'₹ {x:.0f}')

            # Display package details in a DataFrame table
            st.table(package_df)
        else:
            st.info("No packages available.")

    # Manage Bookings page
    elif page == "Manage Bookings":
        st.title("Manage Bookings")

        # Retrieve and display bookings from the database in a table
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()

        if bookings:
            st.subheader("Bookings:")
            booking_df = pd.DataFrame(bookings, columns=["ID", "User Name", "Package ID", "Status"])
            st.table(booking_df)

            # Action selection
            action = st.sidebar.selectbox("Action", ["Update Booking", "Delete Booking"])

            if action == "Update Booking":
                # Update booking status
                st.subheader("Update Booking")
                booking_id_to_manage = st.number_input("Enter Booking ID to manage:")
                status_options = ["Accepted", "Rejected", "Pending"]
                selected_status = st.selectbox("Select Status:", status_options)

                if st.button("Update Booking Status"):
                    # Update the status of the booking in the database
                    cursor.execute("UPDATE bookings SET status=? WHERE id=?", (selected_status, booking_id_to_manage))
                    conn.commit()
                    st.success("Booking status updated successfully!")

            elif action == "Delete Booking":
                # Delete booking
                st.subheader("Delete Booking")
                booking_id_to_delete = st.number_input("Enter Booking ID to delete:")
                if st.button("Delete Booking"):
                    # Delete booking from the database
                    cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id_to_delete,))
                    conn.commit()
                    st.success("Booking deleted successfully!")

        else:
            st.info("No bookings available.")

# Close the database connection
conn.close()
