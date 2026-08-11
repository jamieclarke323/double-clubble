"""One-off helper script: turns the source sword artwork into the icon
assets used throughout the site (header logo, favicon, PWA home-screen
icons) and the base sword mark used to build the shareable result image.

Not imported by the app at runtime - run manually whenever the source
artwork changes:

    python3 scripts/build_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

SOURCE = Path(
    "/Users/jamieclarke/Library/Application Support/Code/User/"
    "workspaceStorage/vscode-chat-images/image-1786401415762.png"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "img"

THEME_RED = (208, 2, 27, 255)  # matches --charlton-red in style.css


def _load_mask() -> Image.Image:
    """Return an RGBA image: opaque white where the source sword is drawn,
    fully transparent everywhere else (the source's solid red background)."""
    src = Image.open(SOURCE).convert("RGB")
    w, h = src.size
    # The source PNG's very last pixel row is a 1px white export artefact
    # (a straight line, not part of the sword drawing) - drop it.
    src = src.crop((0, 0, w, h - 1))
    w, h = src.size
    px = src.load()
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if g > 120 and b > 120:  # white sword pixel (red bg has low g/b)
                mpx[x, y] = (255, 255, 255, 255)
    return mask.crop(mask.getbbox())


def _tinted(mask: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    solid = Image.new("RGBA", mask.size, (*rgb, 0))
    solid.putalpha(mask.split()[3])
    return solid


def _square_app_icon(mask: Image.Image, size: int, safe_ratio: float = 0.62) -> Image.Image:
    """Sword mark in white, centred on a themed-red square, sized so it sits
    comfortably inside the ~80% "safe zone" adaptive-icon platforms use."""
    canvas = Image.new("RGBA", (size, size), THEME_RED)
    target_h = int(size * safe_ratio)
    scale = target_h / mask.size[1]
    target_w = max(1, int(mask.size[0] * scale))
    icon = mask.resize((target_w, target_h), Image.LANCZOS)
    white_icon = Image.new("RGBA", icon.size, (255, 255, 255, 0))
    white_icon.putalpha(icon.split()[3])
    x = (size - target_w) // 2
    y = (size - target_h) // 2
    canvas.paste(white_icon, (x, y), white_icon)
    return canvas


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mask = _load_mask()

    # Transparent sword marks for use directly in page UI.
    _tinted(mask, (255, 255, 255)).save(OUT_DIR / "sword-icon-white.png")
    _tinted(mask, (16, 16, 16)).save(OUT_DIR / "sword-icon-black.png")

    # Square app/home-screen icons on the site's theme red.
    for size, name in [
        (16, "favicon-16.png"),
        (32, "favicon-32.png"),
        (48, "favicon-48.png"),
        (180, "apple-touch-icon.png"),
        (192, "icon-192.png"),
        (512, "icon-512.png"),
    ]:
        _square_app_icon(mask, size).save(OUT_DIR / name)

    favicon_sizes = [16, 32, 48]
    favicon_frames = [
        Image.open(OUT_DIR / f"favicon-{s}.png") for s in favicon_sizes
    ]
    favicon_frames[0].save(
        OUT_DIR / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in favicon_sizes],
    )

    print(f"Wrote icon assets to {OUT_DIR}")


if __name__ == "__main__":
    main()
