from flask import Flask, render_template, request, redirect, url_for
from api.guests import guests_api
from database import(
    create_table,
    add_guest,
    check_out_guest,
    get_all_guests,
    get_active_guests
)

app = Flask(__name__)
app.register_blueprint(guests_api)

create_table()

@app.route("/")
def index():
   guests = get_all_guests()
   return render_template("index.html", guests=guests)
     
@app.route("/checkin", methods=["POST"])
def checkin():
    name = request.form["name"]
    purpose = request.form["purpose"]

    add_guest(name, purpose)
    return redirect(url_for("index"))

@app.route("/checkout/<int:guest_id>")
def check_out(guest_id):
    check_out_guest(guest_id)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)