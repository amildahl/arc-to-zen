#!/usr/bin/env python3
"""Generate PNG, ICO, and ICNS assets from assets/app-icon.svg."""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = REPO_ROOT / "assets" / "app-icon.svg"
PNG_PATH = REPO_ROOT / "assets" / "app-icon.png"
ICO_PATH = REPO_ROOT / "assets" / "app-icon.ico"
ICNS_PATH = REPO_ROOT / "assets" / "app-icon.icns"
ICO_SIZES = [16, 32, 48, 64, 128, 256]


def render_png(renderer: QSvgRenderer, size: int, output: Path) -> None:
    image = QImage(QSize(size, size), QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    if not image.save(str(output), "PNG"):
        raise RuntimeError(f"Failed to write {output}")


def build_ico(renderer: QSvgRenderer, output: Path) -> None:
    png_entries: list[tuple[int, bytes]] = []

    for size in ICO_SIZES:
        image = QImage(QSize(size, size), QImage.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))
        painter = QPainter(image)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()

        buffer = bytearray()
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice

        data = QByteArray()
        qbuffer = QBuffer(data)
        qbuffer.open(QIODevice.WriteOnly)
        image.save(qbuffer, "PNG")
        buffer.extend(bytes(data))
        png_entries.append((size, bytes(buffer)))

    header_size = 6 + len(png_entries) * 16
    offset = header_size
    directory = bytearray()
    payload = bytearray()

    for size, png_data in png_entries:
        width = 0 if size == 256 else size
        height = 0 if size == 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(png_data),
                offset,
            )
        )
        payload.extend(png_data)
        offset += len(png_data)

    output.write_bytes(struct.pack("<HHH", 0, 1, len(png_entries)) + directory + payload)


def build_icns(renderer: QSvgRenderer, output: Path) -> None:
    iconutil = shutil.which("iconutil")
    if not iconutil:
        print("iconutil is unavailable; skipping ICNS generation", file=sys.stderr)
        return

    with tempfile.TemporaryDirectory(prefix="arc-to-zen-iconset-") as temp_dir:
        iconset = Path(temp_dir) / "app-icon.iconset"
        iconset.mkdir()

        for size in (16, 32, 128, 256, 512):
            render_png(renderer, size, iconset / f"icon_{size}x{size}.png")
            render_png(renderer, size * 2, iconset / f"icon_{size}x{size}@2x.png")

        subprocess.run([iconutil, "-c", "icns", str(iconset), "-o", str(output)], check=True)


def main() -> int:
    QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(SVG_PATH))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG: {SVG_PATH}")

    render_png(renderer, 1024, PNG_PATH)
    build_ico(renderer, ICO_PATH)
    build_icns(renderer, ICNS_PATH)

    print(PNG_PATH)
    print(ICO_PATH)
    if ICNS_PATH.exists():
        print(ICNS_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
