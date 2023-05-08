import argparse
import json
import logging
import os
import readline
import shlex
import subprocess
import sys

from dateutil.parser import parse
from jinja2 import Template
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, TPE2, TPOS, TRCK, TYER
from mutagen.mp3 import MP3

debug = logging.DEBUG
info = logging.INFO
warning = logging.WARNING
error = logging.ERROR
critical = logging.CRITICAL
logger = logging.getLogger("audiobook_tools")
logger.setLevel(info)
ch = logging.StreamHandler(sys.stderr)
ch.setLevel(debug)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def common_parser(prog):
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "--log-level",
        "-l",
        help="log level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="error",
    )
    return parser


def log(message, level=info):
    logger.log(level, message)


def run(cmd):
    log(f"Running shell command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        log(result.stdout, debug)
        return result.stdout
    except subprocess.CalledProcessError as e:
        log(e.output, error)
        raise e


def abspath(file):
    return os.path.realpath(os.path.abspath(file))


def get_year(date_string):
    if date_string:
        dt = parse(date_string)
        return str(dt.year)
    else:
        return date_string


def merge_dicts(*dicts):
    return {**dicts[0], **merge_dicts(*dicts[1:])} if dicts else {}


def render(template, variables):
    return Template(template).render(variables)


def get_input(prompt, initial_text):
    readline.set_startup_hook(lambda: readline.insert_text(initial_text))
    user_input = input(f"{prompt}: ")
    readline.set_startup_hook()
    return user_input


def select_keys(dictionary, keys):
    return {key: dictionary[key] for key in keys}


def get_m4b_tags(input_file):
    log(f"Loading tags from file: {input_file}", info)
    tags = select_keys(
        json.loads(
            run(
                f"ffprobe -v quiet -print_format json -show_format -show_streams {shlex.quote(input_file)}"
            )
        )
        .get("format", {})
        .get("tags", {}),
        ["artist", "title", "date"],
    )
    tags["author"] = tags.pop("artist", "")
    tags["year"] = get_year(tags.pop("date", ""))
    for tag in ["author", "title", "year"]:
        tags[tag] = get_input(tag.capitalize(), f"{tags[tag]}")
    return tags


def set_mp3_tags(mp3, artist, album, title, year, track, cover, disc=None):
    audio = MP3(mp3, ID3=ID3)
    audio.delete()
    try:
        audio.add_tags()
    except Exception:
        pass
    audio["TPE1"] = TPE1(encoding=3, text=artist)
    audio["TPE2"] = TPE2(encoding=3, text=artist)
    audio["TALB"] = TALB(encoding=3, text=album)
    audio["TIT2"] = TIT2(encoding=3, text=title)
    audio["TYER"] = TYER(encoding=3, text=year)
    audio["TRCK"] = TRCK(encoding=3, text=track)
    if disc:
        audio["TPOS"] = TPOS(encoding=3, text=disc)
    with open(cover, "rb") as image:
        data = image.read()
    audio["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=data)
    log(f"Saving tags to file: {mp3}", info)
    audio.save(v2_version=3)
