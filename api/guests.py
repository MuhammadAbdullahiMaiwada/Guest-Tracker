from flask import Blueprint, jsonify, request
from database import(
    add_guest,
    check_out_guest,
    get_all_guests,
    get_active_guests
)

guests_api = Blueprint("guests_api", __name__)

@guests_api.route("/api/guests", methods=["GET"])
def all_guests():
    return jsonify(get_all_guests())

@guests_api.route("/api/guests/active", methods=["GET"])
def active_guests():
    return jsonify(get_active_guests())

@guests_api.route("/api/checkin", methods=["POST"])
def checkin():
    data = request.json
    name = data.get("name")
    purpose = data.get("purpose")
    
    if not name or not purpose:
        return jsonify({"error": "Missing data"}), 400
    
    add_guest(name, purpose)
    return jsonify({"message": "Guset checked in"}), 201

@guests_api.route("/api/checkout/<int:guest_id>", methods=["PUT"])
def checkout(guest_id):
    result = check_out_guest(guest_id)
    
    if not result:
        return jsonify({"error": "Gust not active"}), 404
    
    return jsonify({"message": "Guest checked out"})