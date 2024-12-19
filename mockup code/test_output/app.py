import streamlit as st
from database import Database
from auth import login_form, check_authentication

def main():
    st.title("Library Book Management System")
    login_form()
    check_authentication()

    db = Database()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Add Book", "View Books", "Update Book", "Delete Book"])

    if page == "Add Book":
        st.header("Add a New Book")
        title = st.text_input("Title")
        author = st.text_input("Author")
        isbn = st.text_input("ISBN")
        if st.button("Add Book"):
            if db.add_book(title, author, isbn):
                st.success("Book added successfully!")
            else:
                st.error("Book with this ISBN already exists.")

    elif page == "View Books":
        st.header("View Books")
        title = st.text_input("Search by Title")
        author = st.text_input("Search by Author")
        isbn = st.text_input("Search by ISBN")
        if st.button("Search"):
            books = db.get_books(title, author, isbn)
            if books:
                st.table(books)
            else:
                st.info("No books found.")

    elif page == "Update Book":
        st.header("Update a Book")
        book_id = st.number_input("Book ID", min_value=1, step=1)
        title = st.text_input("New Title")
        author = st.text_input("New Author")
        isbn = st.text_input("New ISBN")
        if st.button("Update Book"):
            if db.update_book(book_id, title, author, isbn):
                st.success("Book updated successfully!")
            else:
                st.error("Failed to update book. Check ISBN uniqueness.")

    elif page == "Delete Book":
        st.header("Delete a Book")
        book_id = st.number_input("Book ID", min_value=1, step=1)
        if st.button("Delete Book"):
            db.delete_book(book_id)
            st.success("Book deleted successfully!")

if __name__ == "__main__":
    main()