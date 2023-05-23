import json
import shlex

import yaml
from helpers import *


def main():
    parser = common_parser("m4b2mp3")
    parser.add_argument("m4b", type=str, help="m4b file", nargs="+")
    args = parser.parse_args()
    logger.setLevel(logging.getLevelName(args.log_level.upper()))
    input_files = []
    for file_pattern in args.m4b:
        if "*" in file_pattern:
            input_files.extend(expand_glob(file_pattern))
        else:
            input_files.append(abspath(file_pattern))
    log(f"There are {len(input_files)} m4b files to process: {input_files}", debug)
    # input_file = abspath(args.m4b)
    tags = get_m4b_tags(input_files[0])
    output_dir = abspath(os.path.join(os.getcwd(), f"{tags['author']}/{tags['title']}"))
    output_dir = abspath(get_input("Output directory", f"{output_dir}"))
    output_image = os.path.join(output_dir, "cover.jpg")
    output_image = abspath(get_input("Output cover image file", f"{output_image}"))
    output_metadata = os.path.join(output_dir, f"metadata.yaml")
    output_metadata = abspath(get_input("Output metadata file", f"{output_metadata}"))
    os.makedirs(output_dir, exist_ok=True)
    run(
        f"ffmpeg -y -i {shlex.quote(input_files[0])} -an -c:v copy {shlex.quote(output_image)}"
    )
    if len(input_files) == 1:
        chapters = json.loads(
            run(
                f"ffprobe -v quiet -print_format json -show_chapters {shlex.quote(input_files[0])}"
            )
        ).get("chapters", {})
        print("Splitting m4b file into chapter tracks...")
        for chapter in chapters:
            chapter["track"] = str(int(chapter["id"]) + 1).zfill(
                len(str(len(chapters)))
            )
            chapter["section"] = "1"
            chapter["chapter"] = chapter["tags"]["title"]
            chapter.pop("tags")
            m4b_output_file = os.path.join(output_dir, f"{chapter['id']}.m4b")
            run(
                f"ffmpeg -y -i '{input_files[0]}' -sn -vn -codec copy -ss {chapter['start_time']} -to {chapter['end_time']} '{m4b_output_file}'"
            )
    else:
        chapters = []
        for idx, input_file in enumerate(input_files):
            log(f"Processing file: {input_file}", debug)
            chapter_tags = get_m4b_tags(input_file, prompt=False)
            chapter = {}
            chapter["file"] = input_file
            chapter["track"] = str(idx + 1).zfill(len(str(len(input_files))))
            chapter["section"] = "1"
            chapter["chapter"] = chapter_tags["title"]
            chapters.append(chapter)
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
    total_sections = mp3_metadata.get("total_sections", None) or max(
        [int(chapter["section"]) for chapter in mp3_metadata["chapters"]]
    )
    total_sections = get_input("Total sections", f"{total_sections}")
    if int(total_sections) > 1:
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
        if len(input_files) == 1:
            input_file = input_files[0]
            run(
                f"ffmpeg -y -i '{input_file}' -map_metadata -1 -sn -vn -codec:a libmp3lame -qscale:a 2 -ss {chapter['start_time']} -to {chapter['end_time']} {shlex.quote(mp3_output_file)}"
            )
        else:
            input_file = chapter["file"]
            run(
                f"ffmpeg -y -i '{input_file}' -map_metadata -1 -sn -vn -codec:a libmp3lame -qscale:a 2 {shlex.quote(mp3_output_file)}"
            )
        total_tracks_in_section = len(
            [c for c in mp3_metadata["chapters"] if c["section"] == chapter["section"]]
        )
        track = f"{chapter['track']}/{total_tracks_in_section}"
        if int(total_sections) > 1:
            section = f"{chapter['section']}/{total_sections}"
        else:
            section = None
        set_mp3_tags(
            mp3=mp3_output_file,
            artist=mp3_metadata["author"],
            album=mp3_metadata["title"],
            title=chapter["chapter"],
            year=mp3_metadata["year"],
            track=track,
            cover=input_cover_image,
            disc=section,
        )

    # Remove m4b files
    if len(input_files) == 1:
        print("Removing m4b files...")
        for chapter in mp3_metadata["chapters"]:
            m4b_output_file = os.path.join(output_dir, f"{chapter['id']}.m4b")
            os.remove(m4b_output_file)


if __name__ == "__main__":
    main()
