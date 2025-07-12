from flask import Flask
import os
import psycopg2

app = Flask(__name__)

@app.route('/')
def home():
    return "Backend is running!"

@app.route('/test-db')
def test_db():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return f"Database Connected Successfully!<br>PostgreSQL version: {db_version[0]}"
    except Exception as e:
        return f"Database connection failed: {e}"

if __name__ == '__main__':
    app.run(debug=True)
