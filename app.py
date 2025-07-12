# app.py  ──────────────────────────────────────────────────────────────
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import os

app = Flask(__name__, template_folder="templates")

# ── DB CONNECTION ────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")          # set in Render
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env-var is not set")

# pool_pre_ping=True revives stale connections automatically
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Make sure the table exists (no-op after first run)
with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS scans (
        id            SERIAL PRIMARY KEY,
        serial_number TEXT UNIQUE NOT NULL,
        order_number  TEXT,
        size          TEXT,
        scanned_at    TIMESTAMPTZ DEFAULT now()
    );
    """))

# ── ROUTES ───────────────────────────────────────────────────────────
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

@app.post("/api/scan")
def save_scan():
    """
    Expects JSON body like:
    {
      "serial_number": "123456",
      "order_number" : "ORD1009",
      "size"         : "8.5"
    }
    """
    data = request.get_json(silent=True) or {}
    required = {"serial_number"}
    if not required.issubset(data):
        return jsonify({"error": "serial_number is required"}), 400

    stmt = text("""
        INSERT INTO scans (serial_number, order_number, size)
        VALUES (:serial, :order, :size)
        ON CONFLICT (serial_number) DO UPDATE
          SET order_number = EXCLUDED.order_number,
              size         = EXCLUDED.size;
    """)
    try:
        with engine.begin() as conn:
            conn.execute(stmt, {
                "serial": data["serial_number"],
                "order" : data.get("order_number"),
                "size"  : data.get("size")
            })
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Optional crude admin viewer  (protect with auth if you keep it)
@app.route("/admin")
def admin():
    rows = []
    with engine.begin() as conn:
        res = conn.execute(text("SELECT * FROM scans ORDER BY scanned_at DESC"))
        rows = [dict(r) for r in res]
    return render_template("admin.html", rows=rows)

# ── ENTRYPOINT FOR RENDER/GUNICORN ───────────────────────────────────
if __name__ == "__main__":                       # local dev only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
