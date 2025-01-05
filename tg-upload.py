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
from moviepy.audio.io.AudioFileClip import AudioFileClip
from math import floor
import requests
import argparse
import hashlib

tg_upload = "1.1.5"
versions = f"tg-upload: {tg_upload} \
Python: {py_ver[0]}.{py_ver[1]}.{py_ver[2]} \
Pyrogram: {get_dist('pyrogram').version} \
Prettytable: {get_dist('prettytable').version} \
Pillow: {get_dist('pillow').version} \
httpx: {get_dist('httpx').version} \
TgCrypto: {get_dist('tgcrypto').version} \
moviepy {get_dist('moviepy').version} \
"
json_endpoint = "https://cdn.thecaduceus.eu.org/tg-upload/release.json"

parser = argparse.ArgumentParser(
  prog="tg-upload",
  usage="https://thecaduceus.eu.org/tg-upload",
  description="An open-source Python program or a CLI Tool to upload/download files/folder to/from Telegram effortlessly.",
  epilog="An open-source program developed by Dr.Caduceus (GitHub.com/TheCaduceus)"
)

# CONNECTIVITY FLAGS
parser.add_argument("--ipv6", default=env.get("TG_UPLOAD_IPV6", "False").lower() in {"true", "t", "1"}, action="store_true", help="Connect to Telegram using your device's IPv6, by default IPv4.")
parser.add_argument("--proxy", metavar="TG_UPLOAD_PROXY", default=env.get("TG_UPLOAD_PROXY", None), help="The name of the proxy (in proxy.json) to use for connecting to Telegram.")

# LOGIN FLAGS
parser.add_argument("-p","--profile", metavar="TG_UPLOAD_PROFILE", default=env.get("TG_UPLOAD_PROFILE", None), help="The name of your new or existing session.")
parser.add_argument("--info", default=env.get("TG_UPLOAD_INFO", "False").lower() in {"true", "t", "1"}, action="store_true", help="Show your Telegram account details as JSON.")
parser.add_argument("--api_id", metavar="TG_UPLOAD_API_ID", default=int(env.get("TG_UPLOAD_API_ID", 12345)), type=int, help="Telegram API ID, required to create new session.")
parser.add_argument("--api_hash", metavar="TG_UPLOAD_API_HASH", default=env.get("TG_UPLOAD_API_HASH", None), help="Telegram API HASH, required to create new session.")
parser.add_argument("--phone", metavar="TG_UPLOAD_PHONE", default=env.get("TG_UPLOAD_PHONE", None), help="Phone number (in international format), required to login as user.")
parser.add_argument("--hide_pswd", default=env.get("TG_UPLOAD_HIDE_PSWD", "False").lower() in {"true", "t", "1"}, action="store_true", help="Hide 2FA password using getpass.")
parser.add_argument("--bot", metavar="TG_UPLOAD_BOT_TOKEN", default=env.get("TG_UPLOAD_BOT_TOKEN", None), help="Telegram bot token, required to login as bot.")
parser.add_argument("--logout", default=env.get("TG_UPLOAD_LOGOUT", "False").lower() in {"true", "t", "1"}, action="store_true", help="Revoke current session and delete session file.")
parser.add_argument("--login_string", metavar="TG_UPLOAD_SESSION_STRING", default=env.get("TG_UPLOAD_SESSION_STRING", None), help="Session string to login without auth & creating a session file.")
parser.add_argument("--export_string", default=env.get("TG_UPLOAD_EXPORT_STRING", "False").lower() in {"true", "t", "1"}, action="store_true", help="Generate & display session string using existing session.")
parser.add_argument("--tmp_session", default=env.get("TG_UPLOAD_TMP_SESSION", "False").lower() in {"true", "t", "1"}, action="store_true", help="Don't create session file for this login.")
parser.add_argument("--login_only", default=env.get("TG_UPLOAD_LOGIN_ONLY", "False").lower() in {"true", "t", "1"}, action="store_true", help="Exit immediately after authorization process.")

# FILE FLAGS
parser.add_argument("-l","--path", metavar="TG_UPLOAD_PATH", default=env.get("TG_UPLOAD_PATH", None), help="Path to the file or folder to upload.")
parser.add_argument("-n","--filename", metavar="TG_UPLOAD_FILENAME", default=env.get("TG_UPLOAD_FILENAME", None), help="To upload/download data with custom name.")
parser.add_argument("-i","--thumb", metavar="TG_UPLOAD_THUMB", default=env.get("TG_UPLOAD_THUMB", None), help="Path of thumbnail image to be attached with given file. Pass 'auto' for random frame or provide time in seconds.")
parser.add_argument("-z","--caption", metavar="TG_UPLOAD_CAPTION", default=env.get("TG_UPLOAD_CAPTION", ""), help="Caption text to be attached with file, markdown & HTML formatting allowed.")
parser.add_argument("--duration", metavar="TG_UPLOAD_DURATION", default=int(env.get("TG_UPLOAD_DURATION", 0)), type=int, help="Duration of audio/video in seconds. Pass '-1' for automatic detection.")
parser.add_argument("--capjson", metavar="TG_UPLOAD_CAPJSON", default=env.get("TG_UPLOAD_CAPJSON", None), help="Caption name (in caption.json) to attach with given file.")

# BEHAVIOUR FLAGS
parser.add_argument("-c","--chat_id", metavar="TG_UPLOAD_CHAT_ID", default=env.get("TG_UPLOAD_CHAT_ID", "me") , help="The identity of the chat to upload or download the file to/from can be the username, phone number or user ID.")
parser.add_argument("--as_photo", default=env.get("TG_UPLOAD_AS_PHOTO", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as picture.")
parser.add_argument("--as_video", default=env.get("TG_UPLOAD_AS_VIDEO", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as video.")
parser.add_argument("--as_audio", default=env.get("TG_UPLOAD_AS_AUDIO", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as audio.")
parser.add_argument("--as_voice", default=env.get("TG_UPLOAD_AS_VOICE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as voice.")
parser.add_argument("--as_video_note", default=env.get("TG_UPLOAD_AS_VIDEO_NOTE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send given file as video note.")
parser.add_argument("--split", metavar="TG_UPLOAD_SPLIT", type=int, default=int(env.get("TG_UPLOAD_SPLIT", 0)), help="Split files in given bytes and upload.")
parser.add_argument("--replace", metavar="TG_UPLOAD_REPLACE", type=str, default=env.get("TG_UPLOAD_REPLACE", ",").split(","), nargs=2, help="Replace given character or keyword in filename. Requires two arguments.")
parser.add_argument("--reply_to", metavar="TG_UPLOAD_REPLY_TO", type=int, default=int(env.get("TG_UPLOAD_REPLY_TO", 0)), help="Send files as reply to given message id.")
parser.add_argument("--disable_stream", default=env.get("TG_UPLOAD_DISABLE_STREAM", "True").lower() in {"true", "t", "1"}, action="store_false", help="Disable streaming for given video.")
parser.add_argument("-b","--spoiler", default=env.get("TG_UPLOAD_SPOILER", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send media with spoiler animation.")
parser.add_argument("-y","--self_destruct", metavar="TG_UPLOAD_SELF_DESTRUCT", type=int, default=int(env.get("TG_UPLOAD_SELF_DESTRUCT", 0)), help="Number of seconds (60 or below) after which photo/video will self destruct.")
parser.add_argument("--protect", default=env.get("TG_UPLOAD_PROTECT", "False").lower() in {"true", "t", "1"}, action="store_true", help="Protect uploaded files from getting forwarded & saved.")
parser.add_argument("--parse_mode", metavar="TG_UPLOAD_PARSE_MODE", default=env.get("TG_UPLOAD_PARSE_MODE", "DEFAULT"), help="Set custom formatting mode for caption.")
parser.add_argument("-d","--delete_on_done", default=env.get("TG_UPLOAD_DELETE_ON_DONE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Delete the given file after task completion.")
parser.add_argument("-w","--width", metavar="TG_UPLOAD_WIDTH", type=int, default=int(env.get("TG_UPLOAD_WIDTH", 0)), help="Set custom width for video, by default to original video width.")
parser.add_argument("-e","--height", metavar="TG_UPLOAD_HEIGHT", type=int, default=int(env.get("TG_UPLOAD_HEIGHT", 0)), help="Set custom height for video, by default to original video height.")
parser.add_argument("-a","--artist", metavar="TG_UPLOAD_ARTIST", default=env.get("TG_UPLOAD_ARTIST", None), help="Set artist name of given audio file.")
parser.add_argument("-t","--title", metavar="TG_UPLOAD_TITLE", default=env.get("TG_UPLOAD_TITLE", None), help="Set title of given audio file.")
parser.add_argument("-s","--silent", default=env.get("TG_UPLOAD_SILENT", "False").lower() in {"true", "t", "1"}, action="store_true", help="Send files silently to given chat.")
parser.add_argument("-r","--recursive", default=env.get("TG_UPLOAD_RECURSIVE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Upload files recursively if path is a folder.")
parser.add_argument("--prefix", metavar="TG_UPLOAD_PREFIX", default=env.get("TG_UPLOAD_PREFIX", None), help="Add given prefix text to each filename (prefix + filename).")
parser.add_argument("-g","--hash_memory_limit", metavar="TG_UPLOAD_HASH_MEMORY_LIMIT", type=int, default=int(env.get("TG_UPLOAD_HASH_MEMORY_LIMIT", 1000000)), help="Limit how much memory should be used for calculating hash.")
parser.add_argument("-f","--combine_memory_limit", metavar="TG_UPLOAD_COMBINE_MEMORY_LIMIT", type=int, default=int(env.get("TG_UPLOAD_COMBINE_MEMORY_LIMIT", 1000000)), help="Limit how much memory should be used for combining files.")
parser.add_argument("--split_dir", metavar="TG_UPLOAD_SPLIT_DIR", default=env.get("TG_UPLOAD_SPLIT_DIR", "split"), help="Set custom directory for saving splitted files.")
parser.add_argument("--combine_dir", metavar="TG_UPLOAD_COMBINE_DIR", default=env.get("TG_UPLOAD_COMBINE_DIR", "combine"), help="Set custom directory for saving combined files.")
parser.add_argument("--thumb_dir", metavar="TG_UPLOAD_THUMB_DIR", default=env.get("TG_UPLOAD_THUMB_DIR", "thumb"), help="Set custom directory for saving thumbnails.")
parser.add_argument("--no_warn", default=env.get("TG_UPLOAD_NO_WARN", "False").lower() in {"true", "t", "1"}, action="store_true", help="Don't show warning messages. (DEPRECATED)")
parser.add_argument("--no_update", default=env.get("TG_UPLOAD_NO_UPDATE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Disable checking for updates.")

# DOWNLOAD FLAGS
parser.add_argument("--dl", default=env.get("TG_UPLOAD_DL", "False").lower() in {"true", "t", "1"}, action="store_true", help="Enable download module of tg-upload.")
parser.add_argument("--links", metavar="TG_UPLOAD_LINKS", nargs="+", type=str, default=env.get("TG_UPLOAD_LINKS", "").split(","), help="Telegram file links to be downloaded (separated with space).")
parser.add_argument("--txt_file", metavar="TG_UPLOAD_TXT_FILE", default=env.get("TG_UPLOAD_TXT_FILE", None), help=".txt file path containing telegram file links to be downloaded (1 link / line).")
parser.add_argument("-j", "--auto_combine", default=env.get("TG_UPLOAD_AUTO_COMBINE", "False") in {"true","t","1"}, action="store_true", help="Automatically start combining part files after download.")
parser.add_argument("--range", default=env.get("TG_UPLOAD_RANGE", "False").lower() in {"true", "t", "1"}, action="store_true", help="Find and download messages in between of two given links or message IDs.")
parser.add_argument("--msg_id", nargs="+", metavar="TG_UPLOAD_MSG_ID", type=int, default=env.get("TG_UPLOAD_MSG_ID", "").split(","), help="Identity number of messages to be downloaded (separated with space).")
parser.add_argument("--dl_dir", metavar="TG_UPLOAD_DL_DIR", default=env.get("TG_UPLOAD_DL_DIR", "downloads"), help="Change the download directory, by default 'downloads' in current working directory.")

# UTILITY FLAGS
parser.add_argument("--env", action="store_true", help="Display environment variables, their current value and default value in tabular format.")
parser.add_argument("--file_info", help="Show basic file information.")
parser.add_argument("--hash", help="Calculate & display hash of given file.")
parser.add_argument("--split_file", type=int, help="Split file in given byte, accepts only size & requires path using path flag.")
parser.add_argument("--combine", nargs="+", type=str, help="Restore original file using part files produced by tg-upload. Accepts one or more paths.")
parser.add_argument("--frame", type=int, help="Capture a frame from a video file at given time & save as .jpg file, accepts only time (in seconds) & video file path using path flag.")
parser.add_argument("--convert", help="Convert any image into JPEG format.")

# MISC FLAGS
parser.add_argument("--device_model", metavar="TG_UPLOAD_DEVICE_MODEL", default=env.get("TG_UPLOAD_DEVICE_MODEL", "tg-upload"), help="Overwrite device model before starting client, by default 'tg-upload'.")
parser.add_argument("--system_version", metavar="TG_UPLOAD_SYSTEM_VERSION", default=env.get("TG_UPLOAD_SYSTEM_VERSION", f"{py_ver[0]}.{py_ver[1]}.{py_ver[2]}"), help="Overwrite system version before starting client, by default Python version.")
parser.add_argument("-v","--version", action="version", help="Display current version of tg-upload and dependencies.", version=versions)

args = parser.parse_args()

# Check version
if not args.no_update:
  try:
    release_json = get_url(json_endpoint).json()
    if tg_upload != release_json["latestRelease"]["version"]:
      print(f"[UPDATE] - A new release v{release_json['latestRelease']['version']} is available.\n")
      if release_json["latestRelease"]["showNotLatestMSG"] == "1":
        print(f"\n[NEWS] - {release_json['release']['notLatestMSG']}\n")
    elif release_json["latestRelease"]["showLatestMSG"] == "1":
      print(f"[NEWS] - {release_json['latestRelease']['latestMSG']}\n")

    if tg_upload in list(release_json["releaseSpecificNotice"].keys()):
      print(f"[NOTICE] - {release_json['releaseSpecificNotice'][tg_upload]}\n")
  except Exception:
    print("[UPDATE] - Failed to check for latest version.")

def validate_link(link):
    link_parts = link.replace(" ", "").split('/')
    if 'https:' not in link_parts and 'http:' not in link_parts:
        exit("Error: Link should contain 'https://' or 'http://'.")
    elif "t.me" not in link_parts:
        exit("Error: Link should use t.me as domain.")
    chat_id = int(f"-100{link_parts[4]}") if 'c' in link_parts else link_parts[3]
    msg_id = int(link_parts[-1])
    
    return chat_id, msg_id

def msg_info(message):
    if message.video:
        filename = message.video.file_name
        filesize = message.video.file_size
        if filename is None:
            if message.video.mime_type == 'video/x-matroska':
                filename = f"VID_{message.id}_{message.video.file_unique_id}.mkv"
            else:
                filename = f"VID_{message.id}_{message.video.file_unique_id}.{message.video.mime_type.split('/')[-1]}"
    elif message.document:
        filename = message.document.file_name
        filesize = message.document.file_size
    elif message.sticker:
        filename = message.sticker.file_name
        filesize = message.sticker.file_size
    elif message.animation:
        filename = message.animation.file_name
        filesize = message.animation.file_size
    elif message.audio:
        filename = message.audio.file_name
        filesize = message.audio.file_size
    elif message.photo:
        filename = f"IMG_{message.id}_{message.photo.file_unique_id}.jpg"
        filesize = message.photo.file_size
    else:
        filename = f"unknown_{message.id}"
        filesize = 0

    if args.filename:
        filename = args.filename
    if args.prefix:
        filename = args.prefix + filename
    if args.replace:
        filename = filename.replace(args.replace[0], args.replace[1])
    if args.dl_dir:
        dl_dir = PurePath(args.dl_dir)
        filename = f"{dl_dir}/{filename}"

    return filename, filesize / 1024 / 1024 if filesize != 0 else 0

def file_info(file_path, caption_text):
    file_size = Path(file_path).stat().st_size

    if '{file_sha256}' in caption_text and '{file_md5}' in caption_text:
        with open(file_path, "rb") as f:
            bytes_read = 0
            file_sha256 = hashlib.sha256()
            file_md5 = hashlib.md5()
            while True:
                chunk = f.read(args.hash_memory_limit)
                if not chunk:
                    break
                file_sha256.update(chunk)
                file_md5.update(chunk)
                bytes_read += len(chunk)
                progress = bytes_read / file_size * 100
                print(f"\rCalculating SHA256 & MD5 - {progress:.2f}%", end="")
        file_sha256 = file_sha256.hexdigest()
        file_md5 = file_md5.hexdigest()
    elif '{file_sha256}' in caption_text:
        with open(file_path, "rb") as f:
            bytes_read = 0
            file_sha256 = hashlib.sha256()
            while True:
