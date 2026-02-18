import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from datetime import datetime, date
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

date = "2026-02-19"
cinema_name = "INOX Sattva"
# cinema_name = "Rajadhani"

def send_email():
    my_email = os.environ.get("SMTP_EMAIL")
    to_email = os.environ.get("TO_EMAIL")
    password = os.environ.get("SMTP_PASSWORD")

    message = MIMEMultipart()
    message['From'] = my_email
    message['To'] = to_email
    message['Subject'] = f"Movie Tickets - Available - {cinema_name}"
    message.attach(MIMEText(f"Tickets available for {cinema_name}", 'html'))

    with SMTP("smtp-relay.brevo.com", port=587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email, to_addrs=to_email, msg=message.as_string())

def send_telegram_msg():
    # Your credentials
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")  # Use the negative ID for groups

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message = f"Movie Tickets - Available - {cinema_name}"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent to family!")
        else:
            print(f"Failed to send: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

url = f"https://www.district.in/movies/couple-friendly-movie-tickets-in-hyderabad-MV204055?frmtid=cuoat8whir&fromdate={date}"
content = requests.get(url=url).text
soup = BeautifulSoup(content, 'html.parser')
script = soup.find("script", id="__NEXT_DATA__")
json_data = json.loads(script.text)
data = json_data["props"]["pageProps"]["data"]["serverState"]["movieSessions"]

given_dt_ist = datetime.strptime(
    date, "%Y-%m-%d"
).replace(
    tzinfo=ZoneInfo("Asia/Kolkata")
)
today_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

if today_ist >= given_dt_ist:
    print("Date exceeded or today is current date. Hence Skipping!")
else:
    is_found = False
    for session in data:
        shows = data[session]["arrangedSessions"]
        for show in shows:
            show_data = show["data"]
            if cinema_name in show_data["name"]:
                send_telegram_msg()
                is_found = True
                break
    if is_found:
        print("Tickets Available!")
    else:
        print("Tickets not available")













