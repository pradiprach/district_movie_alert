import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from datetime import datetime, date
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

date = "2026-01-17"
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

url = f"https://www.district.in/movies/anaganaga-oka-raju-movie-tickets-in-hyderabad-MV151347?frmtid=sXBaVe4G5&fromdate={date}"
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
                send_email()
                is_found = True
                break
    if is_found:
        print("Tickets Available!")
    else:
        print("Tickets not available")










