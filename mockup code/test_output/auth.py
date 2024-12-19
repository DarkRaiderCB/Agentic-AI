import streamlit as st
import hashlib

# Simple in-memory user storage for demonstration purposes
USERS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest()
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    hashed_password = hash_password(password)
    return USERS.get(username) == hashed_password

def login_form():
    with st.sidebar:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state["logged_in"] = True
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password")

def check_authentication():
    if not st.session_state.get("logged_in"):
        st.error("Please log in to access this page.")
        login_form()
        st.stop()