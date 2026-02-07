# FileView

A zero-dependency Python file browser you can access from your phone's browser. Browse directories, view images, GIFs, videos, and text files over your local network.

## Quick Start

```bash
# Run with defaults (port 8080, serves your home directory)
python3 fileview.py

# Or specify port and root directory
python3 fileview.py 9000 /path/to/folder
```

Then open the **Network URL** printed in the terminal on your phone's browser (e.g. `http://192.168.x.x:8080`). Both devices must be on the same WiFi network.

## Features

- Mobile-friendly dark UI
- Grid and list view toggle
- Image and GIF thumbnails with full-size viewer
- Video and audio playback
- Text/code file viewer
- Search/filter files by name
- Hidden files (dotfiles) are excluded
- No dependencies — uses only the Python standard library

## Supported File Types

| Type   | Extensions                                              |
|--------|---------------------------------------------------------|
| Images | jpg, jpeg, png, gif, bmp, webp, svg, ico, tiff, avif   |
| Video  | mp4, webm, mkv, avi, mov, ogv                          |
| Audio  | mp3, ogg, wav, flac, aac, m4a                          |
| Text   | txt, md, log, json, xml, csv, py, sh, js, html, css, c, cpp, h, java, rs, go, toml, yaml, yml, ini, conf, cfg |

## Usage

```
python fileview.py [PORT] [ROOT_DIR]
```

| Argument   | Default         | Description                        |
|------------|-----------------|------------------------------------|
| `PORT`     | `8080`          | Port to serve on                   |
| `ROOT_DIR` | Home directory  | Root directory to browse           |

## Stopping

Press `Ctrl+C` in the terminal to stop the server.
