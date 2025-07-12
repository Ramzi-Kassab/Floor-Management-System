# app.py  ──────────────────────────────────────────────────────────────
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import os, psycopg2

app = Flask(__name__)

# ── 1. Normalise DATABASE_URL ────────────────────────────────────────
raw_url = os.getenv("DATABASE_URL", "")
if raw_url.startswith("postgres://"):                      # Render’s short form
    raw_url = raw_url.replace("postgres://",
                              "postgresql+psycopg2://", 1)

engine = create_engine(raw_url, pool_pre_ping=True)

# ── 2. Make sure the table exists (one-off) ───────────────────────────
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id            SERIAL PRIMARY KEY,
            serial_number TEXT UNIQUE NOT NULL,
            order_number  TEXT,
            size          TEXT,
            scanned_at    TIMESTAMPTZ DEFAULT now()
        );
    """))

# ── 3. Routes ────────────────────────────────────────────────────────
@app.route("/")
def home():
    return "Backend is running!"

@app.route("/scan")
def scan_page():
    return render_template("scan.html")

@app.route("/db-check")
def db_check():
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        return "✅ Database connection is working!"
    except Exception as e:
        return f"❌ Database error: {e}"

# Optional: API endpoint the scanner page can POST to
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json(force=True, silent=True) or {}
    serial = data.get("serial_number")
    order  = data.get("order_number")
    size   = data.get("size")

    if not serial:
        return jsonify({"error": "serial_number is required"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO products (serial_number, order_number, size) "
                     "VALUES (:s,:o,:z) "
                     "ON CONFLICT (serial_number) DO NOTHING"),
                {"s": serial, "o": order, "z": size}
            )
        return jsonify({"status": "ok"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── 4. Run locally (Render ignores this) ─────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            debug=True)
