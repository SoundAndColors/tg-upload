import argparse
import hashlib
import requests
from pathlib import Path, PurePath
from sys import version_info as py_ver
from pkg_resources import get_distribution as get_dist
from time import time
from json import load as json_load
from PIL import Image
from datetime import datetime
from httpx import get as get_url
from os import environ as env
from moviepy.video.io.VideoFileClip import VideoFileClip

from pyrogram import Client, enums, errors

# Function to fetch movie details from TMDB
def get_movie_details(movie_title, api_key):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}"
    search_response = requests.get(search_url).json()
    if search_response['results']:
        movie_id = search_response['results'][0]['id']
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&append_to_response=images"
        details_response = requests.get(details_url).json()
        return details_response
    return None

# Setup argparse and other initial configurations
tg_upload = "1.1.5"
versions = f"tg-upload: {tg_upload} Python: {py_ver[0]}.{py_ver[1]}.{py_ver[2]} Pyrogram: {get_dist('pyrogram').version} Prettytable: {get_dist('prettytable').version} Pillow: {get_dist('pillow').version} httpx: {get_dist('httpx').version} TgCrypto: {get_dist('tgcrypto').version} moviepy {get_dist('moviepy').version} "
json_endpoint = "https://cdn.thecaduceus.eu.org/tg-upload/release.json"

parser = argparse.ArgumentParser(
    prog="tg-upload",
    usage="https://thecaduceus.eu.org/tg-upload",
    description="An open-source Python program or a CLI Tool to upload/download files/folder to/from Telegram effortlessly.",
    epilog="An open-source program developed by Dr.Caduceus (GitHub.com/TheCaduceus)"
)

# Define arguments
parser.add_argument("--api_id", metavar="TG_UPLOAD_API_ID", default=int(env.get("TG_UPLOAD_API_ID", 12345)), type=int, help="Telegram API ID, required to create new session.")
parser.add_argument("--api_hash", metavar="TG_UPLOAD_API_HASH", default=env.get("TG_UPLOAD_API_HASH", None), help="Telegram API HASH, required to create new session.")
parser.add_argument("--phone", metavar="TG_UPLOAD_PHONE", default=env.get("TG_UPLOAD_PHONE", None), help="Phone number (in international format), required to login as user.")
parser.add_argument("--bot", metavar="TG_UPLOAD_BOT_TOKEN", default=env.get("TG_UPLOAD_BOT_TOKEN", None), help="Telegram bot token, required to login as bot.")
parser.add_argument("-p", "--profile", metavar="TG_UPLOAD_PROFILE", default=env.get("TG_UPLOAD_PROFILE", None), help="The name of your new or existing session.")
parser.add_argument("--path", metavar="TG_UPLOAD_PATH", default=env.get("TG_UPLOAD_PATH", None), help="Path to the file or folder to upload.")
parser.add_argument("--chat_id", metavar="TG_UPLOAD_CHAT_ID", default=env.get("TG_UPLOAD_CHAT_ID", "me"), help="The identity of the chat to upload or download the file to/from can be the username.")
parser.add_argument("--as_video", default=env.get("TG_UPLOAD_AS_VIDEO", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as video.")
parser.add_argument("--thumb_dir", metavar="TG_UPLOAD_THUMB_DIR", default=env.get("TG_UPLOAD_THUMB_DIR", "thumb"), help="Set custom directory for saving thumbnails.")
parser.add_argument("--api_key", metavar="TMDB_API_KEY", default=env.get("TMDB_API_KEY", None), help="The Movie Database API key for fetching movie details.")
args = parser.parse_args()

# Initialize Telegram client
if args.bot:
    client = Client(args.profile, api_id=args.api_id, api_hash=args.api_hash, bot_token=args.bot)
else:
    client = Client(args.profile, api_id=args.api_id, api_hash=args.api_hash, phone_number=args.phone)

# Upload video with movie details
with client:
    if not args.path:
        exit("Error: Path is not provided.")
    chat_id = args.chat_id
    if args.as_video:
        if Path(args.path).is_file():
            try:
                filename = PurePath(args.path).name
                api_key = args.api_key
                movie_title = PurePath(args.path).stem
                movie_details = get_movie_details(movie_title, api_key)
                if movie_details and 'poster_path' in movie_details:
                    poster_url = f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
                    poster_response = requests.get(poster_url)
                    thumb_path = f"{args.thumb_dir}/{filename}.jpg"
                    with open(thumb_path, 'wb') as poster_file:
                        poster_file.write(poster_response.content)
                    args.thumb = thumb_path
                with VideoFileClip(args.path) as video:
                    if args.thumb == 'auto':
                        args.thumb = f"thumb/THUMB_{PurePath(args.path).stem}.jpg"
                        video.save_frame(args.thumb, t=video.duration / 2)
                client.send_video(chat_id, args.path, thumb=args.thumb)
            except Exception as e:
                print(f"An error occurred: {e}")
