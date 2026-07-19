import os
import csv
import io
from flask import Flask, request, jsonify, render_template, Response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from database import (
    create_table, create_admin_table, create_admin, verify_admin, admin_exists,
    add_guest, check_out_guest, get_all_guests, get_active_guests,
    get_guests_by_range, get_checkins_last_7_days, get_stats,
)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-me-in-production-please-32chars!!")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

jwt = JWTManager(app)

create_table()
create_admin_table()

if not admin_exists():
    create_admin("admin", "admin123")
    print("[INFO] Default admin created -> username: admin | password: admin123")
    print("[INFO] Change this password before sharing the app!")


# Pages
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# Auth
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Request body must be JSON"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400
    admin_id = verify_admin(username, password)
    if not admin_id:
        return jsonify({"msg": "Invalid username or password"}), 401
    token = create_access_token(identity=str(admin_id))
    return jsonify(access_token=token), 200


# Guests
@app.route("/api/guests", methods=["GET"])
@jwt_required()
def api_guests():
    range_filter = request.args.get("range", "all")
    guests = get_guests_by_range(range_filter)
    return jsonify(guests), 200

@app.route("/api/guests/active", methods=["GET"])
@jwt_required()
def api_active_guests():
    return jsonify(get_active_guests()), 200

@app.route("/api/checkin", methods=["POST"])
@jwt_required()
def api_checkin():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Request body must be JSON"}), 400
    name    = data.get("name", "").strip()
    purpose = data.get("purpose", "").strip()
    room    = data.get("room", "").strip()
    host    = data.get("host", "").strip()
    phone   = data.get("phone", "").strip()
    id_type = data.get("id_type", "").strip()
    if not name:
        return jsonify({"msg": "Guest name is required"}), 400
    if not purpose:
        return jsonify({"msg": "Purpose of visit is required"}), 400
    if not room:
        return jsonify({"msg": "Room number is required"}), 400
    new_id = add_guest(name, purpose, room, host, phone, id_type)
    return jsonify({"msg": "Guest checked in successfully", "id": new_id}), 201

@app.route("/api/checkout/<int:guest_id>", methods=["POST"])
@jwt_required()
def api_checkout(guest_id):
    result = check_out_guest(guest_id)
    if result is None:
        return jsonify({"msg": "Guest not found or already checked out"}), 400
    return jsonify({"msg": "Guest checked out successfully", "check_out": result}), 200


# Analytics
@app.route("/api/stats", methods=["GET"])
@jwt_required()
def api_stats():
    return jsonify(get_stats()), 200

@app.route("/api/chart/weekly", methods=["GET"])
@jwt_required()
def api_weekly_chart():
    return jsonify(get_checkins_last_7_days()), 200


# Export CSV
@app.route("/api/export/csv", methods=["GET"])
@jwt_required()
def api_export_csv():
    range_filter = request.args.get("range", "all")
    guests = get_guests_by_range(range_filter)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Purpose", "Room", "Host", "Phone", "ID Type", "Check-In", "Check-Out"])
    for g in guests:
        writer.writerow([
            g["id"], g["name"], g["purpose"], g["room"],
            g.get("host", ""), g.get("phone", ""), g.get("id_type", ""),
            g["check_in"], g["check_out"] or "Active"
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=guests.csv"}
    )


# JWT error handlers
@jwt.unauthorized_loader
def missing_token_callback(reason):
    return jsonify({"msg": "Authorization token is missing"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return jsonify({"msg": "Invalid token"}), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has expired. Please log in again."}), 401


if __name__ == "__main__":
    app.run(debug=True)