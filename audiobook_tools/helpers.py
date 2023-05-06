import argparse
import logging
import os
import readline
import subprocess
import sys

from dateutil.parser import parse
from jinja2 import Template

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
