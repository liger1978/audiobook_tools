import argparse
import json
import readline
import shlex

import yaml
from helpers import *
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, TPE2, TPOS, TRCK, TYER
from mutagen.mp3 import MP3


def m4b_tags(input_file):
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


def main():
    parser = common_parser("m4b2mp3")
    parser.add_argument("m4b", type=str, help="m4b file")
    args = parser.parse_args()
    logger.setLevel(logging.getLevelName(args.log_level.upper()))
    input_file = abspath(args.m4b)
    tags = m4b_tags(input_file)
    output_dir = abspath(os.path.join(os.getcwd(), f"{tags['author']}/{tags['title']}"))
    output_dir = abspath(get_input("Output directory", f"{output_dir}"))
    output_image = os.path.join(output_dir, "cover.jpg")
    output_image = abspath(get_input("Output cover image file", f"{output_image}"))
    output_metadata = os.path.join(output_dir, f"metadata.yaml")
    output_metadata = abspath(get_input("Output metadata file", f"{output_metadata}"))
    os.makedirs(output_dir, exist_ok=True)
    run(
        f"ffmpeg -y -i {shlex.quote(input_file)} -an -c:v copy {shlex.quote(output_image)}"
    )
    chapters = json.loads(
        run(
            f"ffprobe -v quiet -print_format json -show_chapters {shlex.quote(input_file)}"
        )
    ).get("chapters", {})
    print("Splitting m4b file into chapter tracks...")
    for chapter in chapters:
        chapter["track"] = str(int(chapter["id"]) + 1).zfill(len(str(len(chapters))))
        chapter["section"] = "1"
        chapter["chapter"] = chapter["tags"]["title"]
        chapter.pop("tags")
        m4b_output_file = os.path.join(output_dir, f"{chapter['id']}.m4b")
        run(
            f"ffmpeg -y -i '{input_file}' -codec copy -ss {chapter['start_time']} -to {chapter['end_time']} '{m4b_output_file}'"
        )
    yaml.dump(
        merge_dicts(tags, {"chapters": chapters}),
        open(output_metadata, "w"),
        default_flow_style=False,
    )
    input_cover_image = abspath(get_input("Input cover image", f"{output_image}"))
    input_metadata = abspath(get_input("Input metadata", f"{output_metadata}"))
    input(
        "WARNING: check input cover image and metadata before proceeding. Press Enter to continue..."
    )
    mp3_metadata = yaml.load(open(input_metadata, "r"), Loader=yaml.FullLoader)
    total_sections = max(
        [int(chapter["section"]) for chapter in mp3_metadata["chapters"]]
    )
    if total_sections > 1:
        file_name_format = "{{ author }} - {{ title }} - {{ section }} - {{ track }} - {{ chapter }}.mp3"
    else:
        file_name_format = (
            "{{ author }} - {{ title }} - {{ track }} - {{ chapter }}.mp3"
        )
    file_name_format = get_input("File name format", f"{file_name_format}")
    print("Converting m4b files to mp3...")
    for chapter in mp3_metadata["chapters"]:
        mp3_output_file = os.path.join(
            output_dir, (render(file_name_format, merge_dicts(mp3_metadata, chapter)))
        )
        run(
            f"ffmpeg -y -i '{input_file}' -codec:a libmp3lame -qscale:a 2 -ss {chapter['start_time']} -to {chapter['end_time']} {shlex.quote(mp3_output_file)}"
        )
        audio = MP3(mp3_output_file, ID3=ID3)
        audio.delete()
        try:
            audio.add_tags()
        except Exception:
            pass
        audio["TPE1"] = TPE1(encoding=3, text=mp3_metadata["author"])
        audio["TPE2"] = TPE2(encoding=3, text=mp3_metadata["author"])
        audio["TALB"] = TALB(encoding=3, text=mp3_metadata["title"])
        audio["TIT2"] = TIT2(encoding=3, text=chapter["chapter"])
        total_tracks_in_section = len(
            [c for c in mp3_metadata["chapters"] if c["section"] == chapter["section"]]
        )
        audio["TRCK"] = TRCK(
            encoding=3, text=f"{chapter['track']}/{total_tracks_in_section}"
        )
        audio["TYER"] = TYER(encoding=3, text=mp3_metadata["year"])
        if total_sections > 1:
            audio["TPOS"] = TPOS(
                encoding=3,
                text=f"{chapter['section']}/{total_sections}",
            )
        with open(input_cover_image, "rb") as cover_image:
            cover_image_data = cover_image.read()
        audio["APIC"] = APIC(
            encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_image_data
        )
        audio.save(v2_version=3)
    # Remove m4b files
    print("Removing m4b files...")
    for chapter in mp3_metadata["chapters"]:
        m4b_output_file = os.path.join(output_dir, f"{chapter['id']}.m4b")
        os.remove(m4b_output_file)


if __name__ == "__main__":
    main()
