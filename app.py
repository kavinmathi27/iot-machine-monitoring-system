from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import csv, os
import smtplib
from email.mime.text import MIMEText
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pymongo import MongoClient

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- MONGODB CLOUD ----------------
MONGO_URI = "mongodb+srv://iotuser:iotpass123@myatlasclusteredu.9p5eicb.mongodb.net/"
client = MongoClient(MONGO_URI)

db = client["iot_machine_db"]
collection = db["sensor_data"]

# ---------------- CSV BACKUP ----------------
DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "machine_data.csv")
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        csv.writer(f).writerow(
            ["Time", "Temperature", "Humidity", "Vibration", "Status"]
        )

# ---------------- EMAIL CONFIG ----------------
EMAIL_SENDER = "kavinmathi029@gmail.com"
EMAIL_PASSWORD = "qgrh fvqg euzi fhmt"   # Gmail App Password
EMAIL_RECEIVER = "kavinmathi099@gmail.com"

last_alert_time = None

def send_alert_email(temp, vib):
    global last_alert_time
    now = datetime.now()

    # Prevent spam (1 mail every 5 minutes)
    if last_alert_time and (now - last_alert_time).seconds < 300:
        return

    msg = MIMEText(
        f"🚨 MACHINE CRITICAL ALERT 🚨\n\n"
        f"Temperature: {temp} °C\n"
        f"Vibration: {vib}\n\n"
        f"Immediate maintenance required!"
    )

    msg["Subject"] = "CRITICAL MACHINE ALERT"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    last_alert_time = now

# ---------------- ROUTES ----------------

@app.route("/")
def dashboard():
    return render_template("macdash.html")

@app.route("/push", methods=["POST"])
def push_data():
    data = request.json
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    temp = float(data.get("temperature", 0))
    hum  = float(data.get("humidity", 0))
    vib  = float(data.get("vibration", 0))

    status = "RUNNING"
    if temp > 60 or vib > 15:
        status = "CRITICAL"
        send_alert_email(temp, vib)
    elif temp > 50 or vib > 12:
        status = "WARNING"

    # -------- STORE IN MONGODB (CLOUD) --------
    record = {
        "time": time,
        "temperature": temp,
        "humidity": hum,
        "vibration": vib,
        "status": status
    }
    collection.insert_one(record)

    # -------- CSV BACKUP --------
    with open(CSV_FILE, "a", newline="") as f:
        csv.writer(f).writerow([time, temp, hum, vib, status])

    return jsonify({"status": "stored successfully"})

@app.route("/data")
def get_latest_data():
    last = list(collection.find().sort("_id", -1).limit(1))
    if not last:
        return jsonify({})

    last = last[0]

    return jsonify({
        "time": last["time"],
        "temperature": last["temperature"],
        "humidity": last["humidity"],
        "vibration": last["vibration"],
        "status": last["status"]
    })

@app.route("/export/csv")
def export_csv():
    return send_file(CSV_FILE, as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    pdf_path = os.path.join(DATA_DIR, "machine_report.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    y = A4[1] - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Machine Monitoring Report")
    y -= 30

    c.setFont("Helvetica", 10)

    with open(CSV_FILE) as f:
        for row in csv.reader(f):
            c.drawString(40, y, " | ".join(row))
            y -= 14
            if y < 40:
                c.showPage()
                y = A4[1] - 40

    c.save()
    return send_file(pdf_path, as_attachment=True)

# ---------------- RUN ----------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

