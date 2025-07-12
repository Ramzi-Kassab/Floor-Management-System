from flask import Flask, render_template, request, jsonify
import os, psycopg2, logging
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
    data = request.get_json(force=True)
    serial = (data.get("serial") or "").strip()
    order  = (data.get("order")  or "").strip()
    size   = (data.get("size")   or "").strip()

    if not serial:
        return jsonify(error="serial is required"), 400

    try:
        with engine.begin() as conn:
            # INSERT … ON CONFLICT returns a row only when it was NEW
            row = conn.execute(
                text("""
                    INSERT INTO products (serial_number, order_number, size)
                    VALUES (:serial, :order, :size)
                    ON CONFLICT (serial_number) DO NOTHING
                    RETURNING id
                """),
                {"serial": serial, "order": order, "size": size}
            ).first()

        if row:                         # we really inserted a new row
            return "", 201
        else:                           # conflict ⇒ serial existed already
            return jsonify(error="duplicate serial"), 409

    except Exception as e:
        app.logger.exception(e)
        return jsonify(error="db error"), 500


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
