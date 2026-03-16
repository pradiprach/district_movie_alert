import json
import logging
import requests
import os
import pytz
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from database import init_db, get_movies_list, add_movie, update_movie_details, delete_movie
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo


load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MOVIES_LIST = []
IST = pytz.timezone("Asia/Kolkata")
REQUEST_TIMEOUT = 10

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
_raw_origins     = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS  = [o.strip() for o in _raw_origins.split(",") if o.strip()]
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

def load_movies_list():
    global MOVIES_LIST
    MOVIES_LIST = get_movies_list()

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def send_telegram_msg(movie_name, cinema_name):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message = f"Movie {movie_name} Tickets - Available - {cinema_name}"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        session = get_session()
        response = session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info(f"Telegram alert sent: {movie_name} {cinema_name}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def check_movie():
    logger.info("Started Running scheduled task")
    for movie in MOVIES_LIST:
        try:
            url = f"{movie['url']}{movie['date']}"
            content = requests.get(url=url).text
            soup = BeautifulSoup(content, 'html.parser')
            script = soup.find("script", id="__NEXT_DATA__")
            json_data = json.loads(script.text)
            data = json_data["props"]["pageProps"]["data"]["serverState"]["movieSessions"]

            given_dt_ist = datetime.strptime(
                movie["date"], "%Y-%m-%d"
            ).replace(
                tzinfo=ZoneInfo("Asia/Kolkata")
            )
            today_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

            if today_ist >= given_dt_ist:
                print("Date exceeded or today is current date. Hence Skipping!")
            else:
                for session in data:
                    shows = data[session]["arrangedSessions"]
                    for show in shows:
                        show_data = show["data"]
                        for cinema in movie["cinema_names"].split(","):
                            if cinema.strip() in show_data["name"]:
                                send_telegram_msg(movie["name"], cinema)
                                break
        except Exception as e:
            logger.error(f"Error processing {movie['name']}: {e}")
            continue
    logger.info("Finished Running scheduled task")

def create_scheduler():
    scheduler = BackgroundScheduler(timezone=IST)

    scheduler.add_job(
        func=check_movie,
        trigger=CronTrigger(minute="*/5", timezone=IST),
        id="movie_job",
        replace_existing=True
    )

    scheduler.start()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status"    : "ok"
    })


@app.route('/movie', methods=['POST'])
def add_movie_entry():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    name = data.get('name')
    cinemas = data.get('cinemas')
    date = data.get('date')
    url = data.get('url')

    if not url or not name or cinemas is None or date is None:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        add_movie(name, url, cinemas, date)
        load_movies_list()
        return jsonify({'message': 'Stock added successfully'}), 201
    except Exception as e:
        logger.error(f"Add stock error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/movie/<int:id>', methods=['PUT'])
def update_movie_entry_values(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    name = data.get('name')
    cinemas = data.get('cinemas')
    date = data.get('date')

    if name is None or cinemas is None or date is None:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        update_movie_details(id, name, cinemas, date)
        load_movies_list()
        return jsonify({'message': 'Movie updated successfully'}), 200
    except Exception as e:
        logger.error(f"Update stock error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/movie/<int:id>', methods=['DELETE'])
def remove_movie(id):
    try:
        delete_movie(id)
        return jsonify({'message': 'Movie deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Delete stock error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/movies', methods=['GET'])
def get_all_movies():
    try:
        if request.args.get("refresh"):
            load_movies_list()
        return jsonify(MOVIES_LIST), 200
    except Exception as e:
        logger.error(f"Get stocks error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

init_db()
load_movies_list()
create_scheduler()

if __name__ == '__main__':
    try:
        logger.info("Application started successfully")
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=False)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise