import yaml
from helpers import *


def main():
    parser = common_parser("fixmetadata")
    args = parser.parse_args()
    logger.setLevel(logging.getLevelName(args.log_level.upper()))
    dir = abspath(os.getcwd())
    dir = abspath(get_input("Input directory", f"{dir}"))
    image = os.path.join(dir, "cover.jpg")
    image = abspath(get_input("Input cover image", f"{image}"))
    old_metadata = os.path.join(dir, "metadata.yaml")
    old_metadata = abspath(get_input("Input old metadata", f"{old_metadata}"))
    new_metadata = old_metadata.replace(
        os.path.splitext(old_metadata)[1], "_new" + os.path.splitext(old_metadata)[1]
    )
    new_metadata = abspath(get_input("Input new metadata", f"{new_metadata}"))
    input(
        "WARNING: check input cover image, old metadata and new metadata before proceeding. Press Enter to continue..."
    )
    mp3_old_metadata = yaml.load(open(old_metadata, "r"), Loader=yaml.FullLoader)
    mp3_new_metadata = yaml.load(open(new_metadata, "r"), Loader=yaml.FullLoader)
    total_sections = mp3_old_metadata.get("total_sections", None) or max(
        [int(chapter["section"]) for chapter in mp3_old_metadata["chapters"]]
    )
    total_sections = get_input("Existing total sections", f"{total_sections}")
    if int(total_sections) > 1:
        file_name_format = "{{ author }} - {{ title }} - {{ section }} - {{ track }} - {{ chapter }}.mp3"
    else:
        file_name_format = (
            "{{ author }} - {{ title }} - {{ track }} - {{ chapter }}.mp3"
        )
    file_name_format = get_input(
        "File name format of existing mp3 files", f"{file_name_format}"
    )
    new_total_sections = mp3_new_metadata.get("total_sections", None) or max(
        [int(chapter["section"]) for chapter in mp3_new_metadata["chapters"]]
    )
    new_total_sections = get_input("New total sections", f"{new_total_sections}")
    if int(new_total_sections) > 1:
        new_file_name_format = "{{ author }} - {{ title }} - {{ section }} - {{ track }} - {{ chapter }}.mp3"
    else:
        new_file_name_format = (
            "{{ author }} - {{ title }} - {{ track }} - {{ chapter }}.mp3"
        )
    new_file_name_format = get_input(
        "File name format for new mp3 files", f"{new_file_name_format}"
    )
    for chapter in mp3_new_metadata["chapters"]:
        old_chapter = [
            c for c in mp3_old_metadata["chapters"] if c["id"] == chapter["id"]
        ][0]
        mp3_file = os.path.join(
            dir, (render(file_name_format, merge_dicts(mp3_old_metadata, old_chapter)))
        )
        new_mp3_file = os.path.join(
            dir, (render(new_file_name_format, merge_dicts(mp3_new_metadata, chapter)))
        )
        total_tracks_in_section = len(
            [
                c
                for c in mp3_new_metadata["chapters"]
                if c["section"] == chapter["section"]
            ]
        )
        track = f"{chapter['track']}/{total_tracks_in_section}"
        if int(total_sections) > 1:
            section = f"{chapter['section']}/{total_sections}"
        else:
            section = None
        set_mp3_tags(
            mp3=mp3_file,
            artist=mp3_new_metadata["author"],
            album=mp3_new_metadata["title"],
            title=chapter["chapter"],
            year=mp3_new_metadata["year"],
            track=track,
            cover=image,
            disc=section,
        )
        if mp3_file != new_mp3_file:
            os.rename(mp3_file, new_mp3_file)


if __name__ == "__main__":
    main()
