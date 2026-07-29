import sys
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ERR = sys.stderr.isatty()
_OUT = sys.stdout.isatty()
_R = "\033[38;2;255;84;84m" if _ERR else ""
_C = "\033[38;2;125;255;253m" if _OUT else ""
_W = "\033[38;2;255;255;255m" if (_ERR or _OUT) else ""
_BG = "\033[48;2;18;18;18m" if (_ERR or _OUT) else ""
_BR = "\033[38;2;41;41;41m" if _OUT else ""
_GL = "\033[38;2;84;255;110m" if _OUT else ""
_X = "\033[0m" if (_ERR or _OUT) else ""


def err(msg: str):
    colored = _BG + msg.replace("ERROR:", f"{_R}ERROR:{_W}", 1) + _X
    print(f"\n{colored}", file=sys.stderr)


def usage(msg: str):
    colored = _BG + msg.replace("USAGE:", f"{_C}USAGE:{_W}", 1) + _X
    print(f"\n{colored}")


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_upload_date(url: str) -> str | None:
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        err("ERROR: The library 'yt-dlp' couldn't be found.\n"
            'Please install it with: pip install yt-dlp')
        return None
    except subprocess.TimeoutExpired:
        err("ERROR: time out.")
        return None

    if result.returncode != 0:
        err(f"ERROR: {result.stderr.strip()}")
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        err("ERROR: JSON couldn't be resolved.")
        return None

    ts = data.get("timestamp")
    if ts and isinstance(ts, (int, float)):
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (OSError, ValueError):
            pass

    raw = data.get("upload_date")
    if raw:
        try:
            dt = datetime.strptime(raw, "%Y%m%d").replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ValueError:
            pass

    err("ERROR: The upload date couldn't be found.")
    return None


def draw_box(lines: list[str]) -> str:
    term_w = shutil.get_terminal_size().columns
    inner_w = max(len(l) for l in lines) + 4
    box_w = inner_w + 2
    pad = (term_w - box_w) // 2
    if pad < 0:
        pad = 0
        box_w = term_w
        inner_w = box_w - 2

    pad_s = " " * pad
    horz = _BR + "\u2500" * inner_w + _X
    top = pad_s + _BR + "\u250C" + _X + horz + _BR + "\u2510" + _X
    bot = pad_s + _BR + "\u2514" + _X + horz + _BR + "\u2518" + _X
    mid = []
    for l in lines:
        left = (inner_w - len(l)) // 2
        right = inner_w - len(l) - left
        col_l = " " * left + l + " " * right
        for label in ("Video ID:", "Upload Date:"):
            if label in col_l:
                pre, rest = col_l.split(label, 1)
                col_l = pre + _GL + label + _W + rest
                break
        mid.append(pad_s + _BR + "\u2502" + _X + _W + col_l + _X + _BR + "\u2502" + _X)
    return "\n".join([top] + mid + [bot])


def main():
    if len(sys.argv) < 2:
        usage("USAGE: when.exe <url>")
        sys.exit(1)

    url = sys.argv[1]
    video_id = extract_video_id(url)
    if not video_id:
        err("ERROR: Please enter a valid YouTube URL.")
        sys.exit(1)

    date_str = get_upload_date(url)
    if date_str is None:
        sys.exit(1)

    print(f"\n{draw_box([
        f"Video ID: {video_id}",
        f"Upload Date: {date_str}",
    ])}\n", end="")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
