from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from database import *

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

create_table()
create_admin_table()

@app.route("/")
def home():
    return "Guest Tracker API is running"

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    admin_id = verify_admin(data["username"], data["password"])

    if not admin_id:
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=str(admin_id))
    return jsonify(access_token=token)

@app.route("/api/guests", methods=["GET"])
@jwt_required()
def guests():
    return jsonify(get_all_guests())

@app.route("/api/checkin", methods=["POST"])
@jwt_required()
def checkin():
    data = request.get_json()
    name = data.get("name")
    purpose = data.get("purpose")
    room = data.get("room")

    if not name or not purpose or not room:
        return jsonify({"msg": "Missing name/purpose/room"}), 400

    add_guest(name, purpose, room)
    return jsonify({"msg": "Guest checked in"}), 201

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/checkout/<int:guest_id>", methods=["POST"])
@jwt_required()
def checkout(guest_id):
    result = check_out_guest(guest_id)
    if not result:
        return jsonify({"msg": "Guest not active"}), 400
    return jsonify({"msg": "Checked out", "time": result})

if __name__ == "__main__":
    app.run(debug=True)