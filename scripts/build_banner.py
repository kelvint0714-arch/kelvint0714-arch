"""Turn a video clip in banners/ into the README banner.

  assets/banner.webp         looping animated WebP with rounded corners and soft edges
  assets/banner-static.webp  one still frame, shown to visitors who ask for reduced motion

Settings live in banners/config.json. The clip itself is not committed (see
.gitignore); only the converted images are. Needs ffmpeg and Pillow.

  python scripts/build_banner.py            build from the clip in banners/
  python scripts/build_banner.py --remove   drop the banner from the README
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
BANNERS = ROOT / "banners"
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
VIDEO_TYPES = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
START, END = "<!-- BANNER:START -->", "<!-- BANNER:END -->"
MAX_BYTES = 9_000_000


def find_source(config: dict) -> Path:
    if config.get("source"):
        path = BANNERS / config["source"]
        if not path.exists():
            raise SystemExit(f"banners/{config['source']} does not exist")
        return path
    clips = sorted(p for p in BANNERS.iterdir() if p.suffix.lower() in VIDEO_TYPES)
    if not clips:
        raise SystemExit("Put a video clip (mp4, mov, webm…) in banners/ first")
    if len(clips) > 1:
        print(f"several clips found; using {clips[0].name} (set \"source\" in banners/config.json to choose)")
    return clips[0]


def probe(path: Path) -> tuple[int, int, float]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
         "-of", "json", str(path)], check=True, capture_output=True, text=True,
    ).stdout
    info = json.loads(out)
    stream = info["streams"][0]
    return int(stream["width"]), int(stream["height"]), float(info["format"].get("duration", 0))


def extract(path: Path, config: dict, size: tuple[int, int], workdir: Path) -> list[Image.Image]:
    in_w, in_h = size
    crop_h = min(in_h, round(in_w / config["aspect"]))
    crop_w = min(in_w, round(crop_h * config["aspect"]))
    x = (in_w - crop_w) // 2
    y = round((in_h - crop_h) * config["focus_y"])
    width = config["width"]
    height = round(width / config["aspect"]) // 2 * 2
    vf = f"fps={config['fps']},crop={crop_w}:{crop_h}:{x}:{y},scale={width}:{height}:flags=lanczos"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(config["start"]), "-t", str(config["duration"]), "-i", str(path),
         "-vf", vf, "-pix_fmt", "rgb24", str(workdir / "f%04d.png")], check=True,
    )
    frames = [Image.open(p).convert("RGB") for p in sorted(workdir.glob("f*.png"))]
    if not frames:
        raise SystemExit("ffmpeg produced no frames; check start and duration in banners/config.json")
    return frames


def loop_blend(frames: list[Image.Image], seconds: float, fps: int) -> list[Image.Image]:
    """Cross-fade the tail into the head so the loop has no visible jump."""
    overlap = min(int(seconds * fps), len(frames) // 3)
    if overlap < 2:
        return frames
    tail = frames[-overlap:]
    head = [Image.blend(tail[i], frames[i], (i + 1) / (overlap + 1)) for i in range(overlap)]
    return head + frames[overlap:-overlap]


def mask(size: tuple[int, int]) -> Image.Image:
    """Rounded corners plus a soft fade on every edge, so the clip melts into the page."""
    w, h = size
    scale = 4
    big = Image.new("L", (w * scale, h * scale), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * scale - 1, h * scale - 1), radius=24 * scale * w // 1280, fill=255)
    shape = big.resize(size, Image.LANCZOS)
    edge = Image.new("L", size, 0)
    inset = max(6, w // 90)
    ImageDraw.Draw(edge).rectangle((inset, inset, w - inset, h - inset), fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(inset * .8))
    return ImageChops.multiply(shape, edge)


def save(frames: list[Image.Image], alpha: Image.Image, config: dict, poster_index: int) -> tuple[int, int]:
    rgba = []
    for frame in frames:
        frame = frame.convert("RGBA")
        frame.putalpha(alpha)
        rgba.append(frame)
    out = ASSETS / "banner.webp"
    rgba[0].save(out, save_all=True, append_images=rgba[1:], duration=round(1000 / config["fps"]), loop=0,
                 quality=config["quality"], alpha_quality=90, method=5)
    still = ASSETS / "banner-static.webp"
    rgba[min(poster_index, len(rgba) - 1)].save(still, quality=88, alpha_quality=95, method=6)
    return out.stat().st_size, still.stat().st_size


def readme_block(config: dict, show: bool) -> None:
    readme = README.read_text(encoding="utf-8")
    if START not in readme:
        return
    if show:
        alt = config.get("alt", "").replace('"', "&quot;")
        body = (
            "<picture>\n"
            '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/banner-static.webp" />\n'
            f'  <img src="./assets/banner.webp" width="100%" alt="{alt}" />\n'
            "</picture>"
        )
        if config.get("credit"):
            body += f'\n<p align="center"><sub>{config["credit"]}</sub></p>'
    else:
        body = ""
    start, end = readme.index(START) + len(START), readme.index(END)
    updated = readme[:start] + "\n" + body + ("\n" if body else "") + readme[end:]
    if updated != readme:
        README.write_text(updated, encoding="utf-8")


def main(argv: list[str]) -> int:
    config = json.loads((BANNERS / "config.json").read_text(encoding="utf-8"))
    if "--remove" in argv:
        readme_block(config, show=False)
        for name in ("banner.webp", "banner-static.webp"):
            (ASSETS / name).unlink(missing_ok=True)
        print("banner removed")
        return 0
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} is required (macOS: brew install ffmpeg)")
    source = find_source(config)
    in_w, in_h, duration = probe(source)
    print(f"{source.name}: {in_w}×{in_h}, {duration:.1f}s")
    with tempfile.TemporaryDirectory() as tmp:
        frames = extract(source, config, (in_w, in_h), Path(tmp))
    poster = round((config["poster_at"] - config["start"]) * config["fps"])
    frames = loop_blend(frames, config["loop_blend"], config["fps"])
    animated, still = save(frames, mask(frames[0].size), config, max(0, poster))
    print(f"assets/banner.webp: {len(frames)} frames, {animated / 1e6:.1f} MB; banner-static.webp {still / 1e3:.0f} kB")
    if animated > MAX_BYTES:
        print("warning: the banner is large; lower duration, fps, width or quality in banners/config.json")
    readme_block(config, show=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
