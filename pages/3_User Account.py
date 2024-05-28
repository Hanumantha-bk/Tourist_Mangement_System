import streamlit as st
import pandas as pd
import sqlite3
import hashlib  # Import hashlib for password hashing

# Your SQLite database connection
conn = sqlite3.connect('your_database.db')  # Replace 'your_database.db' with your actual database file
cursor = conn.cursor()

# Create tables if not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        is_authenticated BOOLEAN DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY,
        type TEXT,
        price INTEGER,
        details TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY,
        user_email TEXT,
        package_id INTEGER,
        status TEXT
    )
''')
conn.commit()

# Check if session_state has been initialized
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
    st.session_state.username = None

# Navigation bar
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Home", "User SignUp", "User LogIn", "View Package", "Book Package", "View Accepted Bookings", "Logout"])

if page == "Home":
    st.title("Welcome to our Travel Booking App")
    st.image("kar.jpg")

elif page == "User SignUp":
    st.title("User SignUp")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        if username and password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                st.warning("Username already exists. Please choose a different username.")
            else:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                st.success("Account created successfully! Now you can log in.")
        else:
            st.warning("Username and password are required.")

elif page == "User LogIn":
    st.title("User LogIn")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        user = cursor.fetchone()

        if user:
            st.session_state.is_authenticated = True
            st.session_state.username = username
            st.success(f"Welcome, {username}!")
        else:
            st.error("Invalid username or password. Please try again.")

elif st.session_state.is_authenticated and page == "View Package":
    st.title("View Packages")
    # Retrieve and display packages from the database
    cursor.execute("SELECT * FROM packages")
    packages = cursor.fetchall()

    if packages:
        st.subheader("Available Packages:")
        package_df = pd.DataFrame(packages, columns=["ID", "Type", "Price", "Details"])
        package_df["Price"] = package_df["Price"].apply(lambda x: f'₹ {x:.2f}')

        # Display package details in a DataFrame table
        st.table(package_df)

    else:
        st.info("No packages available.")

elif st.session_state.is_authenticated and page == "Book Package":
    st.title("Book Package")
    # Retrieve and display packages from the database
    cursor.execute("SELECT * FROM packages")
    packages = cursor.fetchall()

    if packages:
        package_options = {package[1]: package[0] for package in packages}
        selected_package = st.selectbox("Select a Package:", list(package_options.keys()))

        if st.button("Book"):
            selected_package_id = package_options[selected_package]
            user_email = st.session_state.username
            status = "Pending"
            cursor.execute("INSERT INTO bookings (user_email, package_id, status) VALUES (?, ?, ?)",
                           (user_email, selected_package_id, status))
            conn.commit()
            st.success("Booking successful! You booked {} package.".format(selected_package))

            # Display booking details
            cursor.execute("SELECT * FROM bookings WHERE user_email=? AND package_id=?", (user_email, selected_package_id))
            booking_details = cursor.fetchone()
            if booking_details:
                st.subheader("Booking Details:")
                st.write(f"Username: {user_email}")
                st.write(f"Package ID: {selected_package_id}")
                st.write(f"Package Type: {selected_package}")
                st.write(f"Status: {status}")
            else:
                st.warning("Failed to retrieve booking details.")

    else:
        st.info("No packages available.")

# Add this code snippet to display admin's view of accepted booking statuses
elif st.session_state.is_authenticated and page == "View Accepted Bookings":
    st.title("Accepted Bookings")
    # Retrieve and display accepted bookings from the database
    cursor.execute("SELECT * FROM bookings WHERE status=?", ("Accepted",))
    accepted_bookings = cursor.fetchall()

    if accepted_bookings:
        st.subheader("Accepted Bookings:")
        booking_df = pd.DataFrame(accepted_bookings, columns=["ID", "User Email", "Package ID", "Status"])
        st.table(booking_df)
    else:
        st.info("No accepted bookings available.")

elif page == "Logout":
    st.title("Logout")
    st.session_state.is_authenticated = False
    st.session_state.username = None
    st.success("You have been logged out successfully.")

# Close the database connection
conn.close()
