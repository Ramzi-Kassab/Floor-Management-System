from flask import Flask, render_template
import psycopg2
import os

app = Flask(__name__)

# Environment variable for database connection
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    return "Backend is running!"

@app.route('/scan')
def scan_page():
    return render_template('scan.html')

@app.route('/db-check')
def db_check():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return "✅ Database connection is working!"
    except Exception as e:
        return f"❌ Database error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
