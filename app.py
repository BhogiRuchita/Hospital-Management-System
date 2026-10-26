
import os
from flask import Flask, request, jsonify, send_from_directory
import oracledb

app = Flask(__name__)

def get_connection():
    return oracledb.connect(
        user=os.environ.get("DB_USER", "HOSPITAL_APP"),
        password=os.environ["DB_PASSWORD"],
        dsn=os.environ.get("DB_DSN", "localhost:1521/xepdb1")
    )

@app.route("/")
def home():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "index.html"
    )

@app.route("/api/patients", methods=["POST"])
def add_patient():
    data = request.get_json(silent=True)

    if not data or not data.get("name"):
        return jsonify({"error": "Patient name is required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        new_id = cursor.var(oracledb.NUMBER)

        cursor.execute("""
            INSERT INTO PATIENTS
                (patient_name, age, gender, phone, address)
            VALUES
                (:name, :age, :gender, :phone, :address)
            RETURNING patient_id INTO :new_id
        """, {
            "name": data["name"],
            "age": data.get("age") or None,
            "gender": data.get("gender") or None,
            "phone": data.get("phone") or None,
            "address": data.get("address") or None,
            "new_id": new_id
        })

        patient_id = new_id.getvalue()[0]
        connection.commit()

        return jsonify({
            "message": "Patient registered successfully",
            "patient_id": int(patient_id)
        }), 201

    except Exception:
        app.logger.exception("Patient registration failed")
        return jsonify({
            "error": "Patient registration failed. Check the server logs."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )
