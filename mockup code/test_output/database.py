import sqlite3

class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._setup_tables()

    def _setup_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE
            )
        ''')
        self.conn.commit()

    def add_book(self, title, author, isbn):
        try:
            self.cursor.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)', (title, author, isbn))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_books(self, title=None, author=None, isbn=None):
        query = "SELECT * FROM books WHERE 1=1"
        params = []
        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        if author:
            query += " AND author LIKE ?"
            params.append(f"%{author}%")
        if isbn:
            query += " AND isbn LIKE ?"
            params.append(f"%{isbn}%")
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def update_book(self, book_id, title, author, isbn):
        try:
            self.cursor.execute('''
                UPDATE books SET title = ?, author = ?, isbn = ? WHERE id = ?
            ''', (title, author, isbn, book_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_book(self, book_id):
        self.cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()