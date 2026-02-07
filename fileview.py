#!/usr/bin/env python3
"""
fileview - Browse and view files (images, GIFs, videos) from your phone's browser.

Usage:
    python3 fileview.py [PORT] [ROOT_DIR]

    PORT     - default 8080
    ROOT_DIR - default is your home directory

Then open http://<your-machine-ip>:8080 on your phone.
"""

import http.server
import html
import json
import mimetypes
import os
import socket
import sys
import urllib.parse
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.home()

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.avif'}
VIDEO_EXTS = {'.mp4', '.webm', '.mkv', '.avi', '.mov', '.ogv'}
AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.flac', '.aac', '.m4a'}
TEXT_EXTS = {'.txt', '.md', '.log', '.json', '.xml', '.csv', '.py', '.sh', '.js', '.html', '.css', '.c', '.cpp', '.h', '.java', '.rs', '.go', '.toml', '.yaml', '.yml', '.ini', '.conf', '.cfg'}

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FileView - {title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #1a1a2e; color: #e0e0e0; min-height: 100vh; }}
  header {{ background: #16213e; padding: 12px 16px; position: sticky; top: 0; z-index: 10;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
  header h1 {{ font-size: 16px; font-weight: 600; color: #e94560; }}
  .breadcrumb {{ font-size: 13px; margin-top: 6px; word-break: break-all; }}
  .breadcrumb a {{ color: #0f3460; background: #e94560; padding: 2px 8px; border-radius: 4px;
                   text-decoration: none; font-weight: 500; }}
  .breadcrumb span {{ color: #888; }}
  .controls {{ padding: 10px 16px; display: flex; gap: 8px; flex-wrap: wrap; }}
  .controls button {{ background: #0f3460; color: #e0e0e0; border: none; padding: 8px 14px;
                      border-radius: 6px; font-size: 13px; cursor: pointer; }}
  .controls button.active {{ background: #e94560; color: #fff; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
           gap: 10px; padding: 10px 16px; }}
  .list {{ padding: 0 16px; }}
  .item {{ background: #16213e; border-radius: 8px; overflow: hidden;
           text-decoration: none; color: #e0e0e0; display: flex; flex-direction: column; }}
  .grid .item {{ }}
  .list .item {{ flex-direction: row; align-items: center; margin-bottom: 6px; padding: 8px 12px; }}
  .thumb {{ width: 100%; aspect-ratio: 1; object-fit: cover; background: #0f3460; display: flex;
            align-items: center; justify-content: center; font-size: 36px; min-height: 80px; }}
  .thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
  .list .thumb {{ width: 48px; height: 48px; min-height: 48px; aspect-ratio: 1;
                  border-radius: 6px; font-size: 22px; flex-shrink: 0; }}
  .label {{ padding: 8px; font-size: 12px; word-break: break-word; line-height: 1.3; }}
  .list .label {{ padding: 0 0 0 12px; font-size: 14px; }}
  .dir-icon {{ color: #e94560; }}
  .size {{ font-size: 11px; color: #888; margin-top: 2px; }}
  .viewer {{ padding: 16px; text-align: center; }}
  .viewer img, .viewer video {{ max-width: 100%; max-height: 80vh; border-radius: 8px; }}
  .viewer pre {{ text-align: left; background: #16213e; padding: 16px; border-radius: 8px;
                 overflow-x: auto; font-size: 13px; max-height: 80vh; white-space: pre-wrap;
                 word-break: break-word; }}
  .back {{ display: inline-block; margin: 10px 16px; color: #e94560; text-decoration: none;
           font-weight: 600; font-size: 14px; }}
  .search {{ flex: 1; min-width: 120px; padding: 8px 12px; border-radius: 6px; border: none;
             background: #0a0a1a; color: #e0e0e0; font-size: 13px; }}
  .search::placeholder {{ color: #555; }}
  .empty {{ padding: 40px 16px; text-align: center; color: #555; }}
</style>
</head>
<body>
<header>
  <h1>FileView</h1>
  <div class="breadcrumb">{breadcrumb}</div>
</header>
{body}
<script>
{script}
</script>
</body>
</html>
"""

BROWSE_SCRIPT = """\
const grid = document.getElementById('grid');
const items = document.querySelectorAll('.item');
const searchBox = document.getElementById('search');
let viewMode = localStorage.getItem('viewMode') || 'grid';

function setView(mode) {
  viewMode = mode;
  localStorage.setItem('viewMode', mode);
  grid.className = mode;
  document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
}
setView(viewMode);

if (searchBox) {
  searchBox.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    items.forEach(item => {
      const name = item.dataset.name.toLowerCase();
      item.style.display = name.includes(q) ? '' : 'none';
    });
  });
}
"""


def human_size(size):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} B"
        size /= 1024
    return f"{size:.1f} PB"


def icon_for(path: Path):
    if path.is_dir():
        return '<span class="dir-icon">\U0001F4C1</span>'
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return '\U0001F5BC'
    if ext in VIDEO_EXTS:
        return '\U0001F3AC'
    if ext in AUDIO_EXTS:
        return '\U0001F3B5'
    if ext in TEXT_EXTS:
        return '\U0001F4C4'
    return '\U0001F4CE'


def make_breadcrumb(rel_path: str):
    parts = [p for p in rel_path.split('/') if p]
    crumbs = [f'<a href="/">\U0001F3E0</a>']
    for i, part in enumerate(parts):
        href = '/' + '/'.join(parts[:i+1]) + '/'
        crumbs.append(f' <span>/</span> <a href="{html.escape(href)}">{html.escape(part)}</a>')
    return ''.join(crumbs)


def safe_resolve(requested: str) -> Path | None:
    """Resolve path and ensure it's under ROOT."""
    decoded = urllib.parse.unquote(requested)
    target = (ROOT / decoded.lstrip('/')).resolve()
    if target == ROOT or str(target).startswith(str(ROOT) + os.sep):
        return target
    return None


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = safe_resolve(parsed.path)

        if path is None or not path.exists():
            self.send_error(404, "Not Found")
            return

        if path.is_dir():
            self.serve_directory(path, parsed.path)
        else:
            self.serve_file(path, parsed.path)

    def serve_directory(self, dirpath: Path, url_path: str):
        if not url_path.endswith('/'):
            self.send_response(301)
            self.send_header('Location', url_path + '/')
            self.end_headers()
            return

        try:
            entries = sorted(dirpath.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            self.send_error(403, "Permission Denied")
            return

        rel = str(dirpath.relative_to(ROOT))
        if rel == '.':
            rel = ''

        items_html = []
        for entry in entries:
            if entry.name.startswith('.'):
                continue
            name = entry.name
            href = urllib.parse.quote(name)
            if entry.is_dir():
                href += '/'

            ext = entry.suffix.lower()
            is_image = ext in IMAGE_EXTS and entry.is_file()

            if is_image:
                thumb_content = f'<img loading="lazy" src="{html.escape(href)}" alt="">'
            else:
                thumb_content = icon_for(entry)

            try:
                size_str = human_size(entry.stat().st_size) if entry.is_file() else ''
            except OSError:
                size_str = ''

            size_html = f'<div class="size">{size_str}</div>' if size_str else ''

            items_html.append(
                f'<a class="item" href="{html.escape(href)}" data-name="{html.escape(name)}">'
                f'<div class="thumb">{thumb_content}</div>'
                f'<div class="label">{html.escape(name)}{size_html}</div></a>'
            )

        if items_html:
            body_inner = ''.join(items_html)
        else:
            body_inner = '<div class="empty">Empty directory</div>'

        controls = (
            '<div class="controls">'
            '<input class="search" id="search" type="text" placeholder="Filter...">'
            '<button class="view-btn" data-mode="grid" onclick="setView(\'grid\')">Grid</button>'
            '<button class="view-btn" data-mode="list" onclick="setView(\'list\')">List</button>'
            '</div>'
        )

        body = controls + f'<div id="grid" class="grid">{body_inner}</div>'

        page = HTML_TEMPLATE.format(
            title=html.escape(rel or 'Home'),
            breadcrumb=make_breadcrumb(rel),
            body=body,
            script=BROWSE_SCRIPT
        )

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode())

    def serve_file(self, filepath: Path, url_path: str):
        ext = filepath.suffix.lower()
        parent_url = '/'.join(url_path.rstrip('/').split('/')[:-1]) + '/'

        # For inline viewing of supported types
        if 'view' not in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query):
            # Check if browser is directly requesting the raw file (e.g. for <img> tags)
            accept = self.headers.get('Accept', '')
            if 'text/html' not in accept:
                self.send_raw_file(filepath)
                return

            # Show viewer page for supported types
            if ext in IMAGE_EXTS:
                raw_url = html.escape(urllib.parse.quote(filepath.name))
                media = f'<img src="{raw_url}" alt="{html.escape(filepath.name)}">'
                self.send_viewer(filepath, parent_url, media)
                return

            if ext in VIDEO_EXTS:
                mime = mimetypes.guess_type(filepath.name)[0] or 'video/mp4'
                raw_url = html.escape(urllib.parse.quote(filepath.name))
                media = f'<video controls autoplay><source src="{raw_url}" type="{mime}">Not supported.</video>'
                self.send_viewer(filepath, parent_url, media)
                return

            if ext in AUDIO_EXTS:
                mime = mimetypes.guess_type(filepath.name)[0] or 'audio/mpeg'
                raw_url = html.escape(urllib.parse.quote(filepath.name))
                media = f'<audio controls><source src="{raw_url}" type="{mime}">Not supported.</audio>'
                self.send_viewer(filepath, parent_url, media)
                return

            if ext in TEXT_EXTS:
                try:
                    text = filepath.read_text(errors='replace')[:500_000]
                    media = f'<pre>{html.escape(text)}</pre>'
                    self.send_viewer(filepath, parent_url, media)
                    return
                except Exception:
                    pass

        self.send_raw_file(filepath)

    def send_viewer(self, filepath, parent_url, media_html):
        rel = str(filepath.relative_to(ROOT))
        body = (
            f'<a class="back" href="{html.escape(parent_url)}">\u2190 Back</a>'
            f'<div class="viewer">{media_html}</div>'
            f'<div style="text-align:center;padding:10px;color:#888;font-size:13px">'
            f'{html.escape(filepath.name)} &mdash; {human_size(filepath.stat().st_size)}</div>'
        )
        page = HTML_TEMPLATE.format(
            title=html.escape(filepath.name),
            breadcrumb=make_breadcrumb(rel),
            body=body,
            script=''
        )
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode())

    def send_raw_file(self, filepath: Path):
        mime = mimetypes.guess_type(filepath.name)[0] or 'application/octet-stream'
        try:
            size = filepath.stat().st_size
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(size))
            self.send_header('Cache-Control', 'public, max-age=300')
            self.end_headers()
            with open(filepath, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except PermissionError:
            self.send_error(403, "Permission Denied")
        except Exception as e:
            self.send_error(500, str(e))


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    ip = get_local_ip()
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"\n  FileView is running!\n")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://{ip}:{PORT}")
    print(f"  Root:    {ROOT}\n")
    print(f"  Open the Network URL on your phone (same WiFi).")
    print(f"  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == '__main__':
    main()
