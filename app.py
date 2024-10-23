import pyodbc
from flask import Flask, request, render_template, redirect, url_for, send_file
import pandas as pd
from config import DB_CONFIG  # Import the database configuration

app = Flask(__name__)


# Function to create the database connection
def get_db_connection():
    connection = pyodbc.connect(
        f'DRIVER={DB_CONFIG["driver"]};'
        f'SERVER={DB_CONFIG["server"]};'
        f'DATABASE={DB_CONFIG["database"]};'
        f'UID={DB_CONFIG["username"]};'
        f'PWD={DB_CONFIG["password"]}'
    )
    return connection


# Create the Inventory table if it doesn't exist
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Inventory' AND xtype='U')
    CREATE TABLE Inventory (
        entry_id INT IDENTITY(1,1) PRIMARY KEY,
        title NVARCHAR(255) NOT NULL,
        author NVARCHAR(255) NOT NULL,
        genre NVARCHAR(100),
        publication_date DATE,
        isbn NVARCHAR(20) UNIQUE NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


# Add a new book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        publication_date = request.form['publication_date']
        isbn = request.form['isbn']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Inventory (title, author, genre, publication_date, isbn)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, author, genre, publication_date, isbn))
            conn.commit()
            print("Book added successfully.")
        except pyodbc.IntegrityError:
            print("Error: Book with the same ISBN already exists.")
        finally:
            conn.close()
        return redirect(url_for('home'))
    return render_template('add.html')


# Filter books
@app.route('/filter', methods=['GET'])
def filter_books():
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    genre = request.args.get('genre', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Inventory WHERE 1=1"
    params = []

    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")
    if genre:
        query += " AND genre LIKE ?"
        params.append(f"%{genre}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return render_template('filter.html', books=rows)


# Display all books
@app.route('/books', methods=['GET'])
def books_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Inventory")
    rows = cursor.fetchall()
    conn.close()

    return render_template('books_list.html', books=rows)


# Export data
@app.route('/export', methods=['GET'])
def export_data():
    format1 = request.args.get('format1', 'csv')
    conn = get_db_connection()
    query = "SELECT * FROM Inventory"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if format1 == 'csv':
        csv_file = 'book_inventory.csv'
        df.to_csv(csv_file, index=False)
        print("Data exported to book_inventory.csv")
        return send_file(csv_file, as_attachment=True)
    elif format1 == 'json':
        json_file = 'book_inventory.json'
        df.to_json(json_file, orient='records')
        print("Data exported to book_inventory.json")
        return send_file(json_file, as_attachment=True)
    else:
        print("Unsupported format. Please choose 'csv' or 'json'.")

    return redirect(url_for('home'))


# Home page route
@app.route('/')
def home():
    return render_template('index.html')


# Main entry point
if __name__ == '__main__':
    create_table()
    app.run(debug=True)
