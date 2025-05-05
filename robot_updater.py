import imaplib
import smtplib
import email
import requests
import re
import time
from email.mime.text import MIMEText
from email.utils import make_msgid

# CONFIG
EMAIL_USER = "adam@alistarincoh.com"
EMAIL_PASS = "kimc cosr nahz goya"  # Gmail App Password
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SAMSARA_API_TOKEN = "samsara_api_2NI0rRVo0DqNZH9krQNGwcPHVry4y4"  # Replace with your token
OPENCAGE_API_KEY = "43d8196cca694186a7df235c524e869d"

# FUNCTIONS
def get_vehicle_location_and_speed(driver_id):
    headers = {
        "Authorization": f"Bearer {SAMSARA_API_TOKEN}",
        "X-Samsara-API-Version": "2024-04-01"
    }
    url = f"https://api.samsara.com/fleet/vehicles/locations?vehicleIds={driver_id}"
    response = requests.get(url, headers=headers)
    if response.ok:
        data = response.json()
        vehicle = data.get("data", [None])[0]
        if not vehicle: return None
        loc = vehicle.get("location", {})
        return {
            "lat": loc.get("latitude"),
            "lon": loc.get("longitude"),
            "speed": loc.get("speed")
        }
    return None

def reverse_geocode(lat, lon):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={OPENCAGE_API_KEY}"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        if data["results"]:
            return data["results"][0]["formatted"]
    return f"{lat}, {lon}"

def find_latest_message_with_load_id(imap_conn, load_id):
    imap_conn.select("INBOX")
    result, data = imap_conn.search(None, f'(SUBJECT "{load_id}")')
    if result != "OK" or not data or not data[0]:
        return None
    msg_ids = data[0].split()
    latest_id = msg_ids[-1]
    result, msg_data = imap_conn.fetch(latest_id, "(RFC822)")
    if result != "OK":
        return None
    msg = email.message_from_bytes(msg_data[0][1])

    # Check if the message body mentions delivery
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode(errors='ignore')
            if "load has been delivered successfully" in body.lower():
                print(f"Skipping Load ID {load_id} (already delivered)")
                return "DELIVERED"
    return msg

def reply_all_smtp(original_msg, to, cc, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = f"Re: {subject}"
    msg['From'] = EMAIL_USER
    msg['To'] = to
    msg['Cc'] = cc
    msg['Message-ID'] = make_msgid()
    msg['In-Reply-To'] = original_msg.get("Message-ID")
    msg['References'] = original_msg.get("Message-ID")
    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.sendmail(EMAIL_USER, [to] + cc.split(","), msg.as_string())

def run_batch_updates(load_ids, driver_ids):
    imap_conn = imaplib.IMAP4_SSL(IMAP_SERVER)
    imap_conn.login(EMAIL_USER, EMAIL_PASS)

    for cycle in range(3):  # 0h, 2h, 4h
        print(f"\n--- Update Cycle {cycle + 1}/3 ---")
        for load_id, driver_input in zip(load_ids, driver_ids):
            match = re.search(r'(\d{15,})', driver_input)
            if not match:
                print(f"Invalid driver input: {driver_input}")
                continue
            driver_id = match.group(1)

            vehicle_data = get_vehicle_location_and_speed(driver_id)
            if not vehicle_data:
                print(f"No data for driver ID {driver_id}")
                continue

            if vehicle_data['speed'] == 0:
                print(f"Skipping Load ID {load_id} (speed is 0)")
                continue

            address = reverse_geocode(vehicle_data['lat'], vehicle_data['lon'])
            msg = find_latest_message_with_load_id(imap_conn, load_id)
            if msg == "DELIVERED":
                continue
            if not msg:
                print(f"No email found for Load ID {load_id}")
                continue

            to_email = email.utils.parseaddr(msg["From"])[1]
            cc = msg.get("Cc", "")
            subject = msg["Subject"]

            if vehicle_data['speed'] < 50:
                status = "Status: rolling slowly due to the traffic"
            else:
                status = "Status: rolling"

            body = (
                f"Load ID: {load_id}\n"
                f"Current location: {address}\n"
                f"{status}\n"
                "We will keep you posted\n"
                "Thank you"
            )

            reply_all_smtp(msg, to_email, cc, subject, body)
            print(f"Update sent for Load ID {load_id}")

        if cycle < 2:
            print("Waiting 2 hours until next update...")
            time.sleep(2 * 3600)
    print("\n✅ All updates complete.")

def run_manual_batch():
    load_ids = [input(f"Enter Load ID {i+1}: ").strip() for i in range(15)]
    driver_ids = [input(f"Enter Driver ID {i+1}: ").strip() for i in range(15)]
    run_batch_updates(load_ids, driver_ids)

# Start
run_manual_batch()
