from flask import Flask, render_template, request, jsonify
import os, psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# ── Normalise DATABASE_URL ────────────────────────────────────────────────
raw_url = os.getenv("DATABASE_URL", "")
if raw_url.startswith("postgres://"):                 # legacy prefix
    raw_url = raw_url.replace("postgres://",
                              "postgresql+psycopg2://", 1)

if not raw_url:                                       # hard-stop guard
    raise RuntimeError("DATABASE_URL env-var is missing!")

engine = create_engine(raw_url, pool_pre_ping=True)


# ── Auto-create table on first run (idempotent) ───────────────────────────
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public.products (
            id             SERIAL PRIMARY KEY,
            serial_number  TEXT UNIQUE NOT NULL,
            order_number   TEXT,
            size           TEXT,
            scanned_at     TIMESTAMPTZ DEFAULT now()
        );
    """))


# ─────────────────────────── Routes ───────────────────────────────────────
@app.route("/")
def home():
    return "Backend is running!"

@app.route("/scan")
def scan_page():
    return render_template("scan.html")            # mobile scanner UI


# API → insert product row
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json(force=True, silent=True) or {}
    serial = data.get("serial", "").strip()
    order  = data.get("order",  "").strip()
    size   = data.get("size",   "").strip()

    if not serial:                             # fast validation
        return jsonify({"error": "serial is required"}), 400

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO public.products
                        (serial_number, order_number, size)
                        VALUES (:sn, :on, :sz)
                """),
                {"sn": serial, "on": order, "sz": size}
            )
        return jsonify({"status": "ok"}), 201

    except IntegrityError:                     # duplicate serial
        return jsonify({"error": "duplicate"}), 409
    except Exception as e:                     # anything else
        return jsonify({"error": str(e)}), 500


# (Optional) keep the old mobile URL working
@app.route("/api/scan", methods=["POST"])
def scan_alias():
    return add_product()


# ── simple liveness/db check endpoints ────────────────────────────────────
@app.route("/db-check")
def db_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "✅ Database connection is working!"
    except Exception as e:
        return f"❌ Database error: {e}"

# ── Local dev entrypoint (Render runs gunicorn) ───────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=True)
