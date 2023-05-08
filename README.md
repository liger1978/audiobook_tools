# audiobook_tools

## Requirements

- poetry
- ffprobe
- ffmpeg

## Setup
```bash
poetry install
```

## m4b2mp3
```console
$ bin/m4b2mp3 -h
usage: m4b2mp3 [-h] [--log-level {debug,info,warning,error,critical}] m4b

positional arguments:
  m4b                   m4b file

options:
  -h, --help            show this help message and exit
  --log-level {debug,info,warning,error,critical}, -l {debug,info,warning,error,critical}
                        log level
```

# fixmetadata
```console
$ fixmetadata -h
usage: fixmetadata [-h] [--log-level {debug,info,warning,error,critical}]

options:
  -h, --help            show this help message and exit
  --log-level {debug,info,warning,error,critical}, -l {debug,info,warning,error,critical}
                        log level
```
