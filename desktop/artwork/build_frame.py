"""Compose the PERRE'UTT cabinet from the existing CRT and original brand art.

Run with .venv-desktop/Scripts/python.exe desktop/artwork/build_frame.py.
No image generation API, model, credentials or network calls are used.
"""
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor, QPen, QTransform
from PySide6.QtSvg import QSvgRenderer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pixels(image):
    return np.frombuffer(image.bits(), np.uint8).reshape(image.height(), image.bytesPerLine())[:, :image.width()*4].reshape(image.height(), image.width(), 4)


def trimmed(image):
    image = image.convertToFormat(QImage.Format_RGBA8888)
    y, x = np.nonzero(pixels(image)[:, :, 3] > 15)
    return image.copy(int(x.min()), int(y.min()), int(x.max()-x.min()+1), int(y.max()-y.min()+1))


def brand(chrome=False, ink="#151119"):
    if chrome:
        image = QImage(str(HERE / "references/perreutt-chrome.png"))
    else:
        image = QImage(1589, 887, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        QSvgRenderer(str(HERE / "references/perreutt-logo.svg")).render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), QColor(ink))
        painter.end()
    # Level the original orbital mark before printing it on the sticker.
    return trimmed(image.transformed(QTransform().rotate(23), Qt.SmoothTransformation))


def sticker(painter, logo, x, y, width, height, angle, paper, edge):
    painter.save()
    painter.translate(x, y)
    painter.rotate(angle)
    rect = QRectF(-width/2, -height/2, width, height)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0, 130))
    painter.drawRoundedRect(rect.translated(2, 3), 8, 8)
    painter.setBrush(QColor(paper))
    painter.setPen(QPen(QColor(edge), 1.3))
    painter.drawRoundedRect(rect, 8, 8)
    scale = min((width-14)/logo.width(), (height-10)/logo.height())
    w, h = logo.width()*scale, logo.height()*scale
    painter.drawImage(QRectF(-w/2, -h/2, w, h), logo)
    # Fine specular edge, like a laminated vinyl sticker.
    painter.setPen(QPen(QColor(255, 255, 255, 95), .7))
    painter.drawLine(rect.topLeft()+QPointF(9, 2), rect.topRight()+QPointF(-9, 2))
    painter.restore()


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    original = QImage(str(ROOT / 'tv-frame-clean.png')).convertToFormat(QImage.Format_RGBA8888)
    if original.isNull():
        raise RuntimeError('Missing base CRT artwork')
    source = pixels(original).copy()
    frame = original.copy()
    target = pixels(frame)
    h, w = source.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x, y = xx/w, yy/h
    light = source[:, :, :3].astype(np.float32) @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # Retain the photographed relief and scratches, replacing aged gold with
    # graphite/chrome and reflected magenta/cyan from the association artwork.
    metal = np.clip(light*1.18, 0, 255)
    rgb = metal[:, :, None]*np.array([.88, .92, 1.03])
    magenta = np.exp(-((x-.13)/.32)**2-((y-.18)/.8)**2)
    cyan = np.exp(-((x-.9)/.22)**2-((y-.57)/.65)**2)
    reflection = np.clip(light/80, 0, 1)
    rgb += magenta[:, :, None]*reflection[:, :, None]*np.array([39, -7, 34])
    rgb += cyan[:, :, None]*reflection[:, :, None]*np.array([-7, 18, 33])
    target[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    painter = QPainter(frame)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    sticker(painter, brand(chrome=True), 242, 48, 178, 62, -3, '#101016', '#9b8caf')
    sticker(painter, brand(ink='#fa25ab'), 900, 48, 184, 55, 4, '#160d18', '#f442b5')
    sticker(painter, brand(), 740, 938, 248, 74, -1.5, '#e9e7e0', '#b8b1b9')
    painter.end()
    # Exact original screen cutout; no logo, glow or paper can cover the lyrics.
    target = pixels(frame)
    target[:, :, 3] = source[:, :, 3]
    target[source[:, :, 3] == 0, :3] = 0
    output = HERE / 'tv-frame-perreutt-v1.png'
    if not frame.save(str(output)):
        raise RuntimeError('Could not save the PERREUTT cabinet')
    print(f'Saved {output.relative_to(ROOT)} ({w}x{h}); original alpha preserved.')


if __name__ == '__main__':
    main()
