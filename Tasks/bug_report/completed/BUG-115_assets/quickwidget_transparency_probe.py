"""Minimal isolation of the QQuickWidget-in-QtWidgets transparency mechanism.

Top-level QWidget painted #111318 (like Panel/SURFACE). Inside: a QQuickWidget
whose QML draws one red square and leaves the rest transparent. We then read
what actually reached the SCREEN (QScreen.grabWindow) vs widget.grab().

MODE env var:
  transparent  - setClearColor(Qt.transparent)          (what the app does today)
  opaque       - setClearColor(#111318)                  (candidate fix A)
  qmlbg        - transparent clear + QML root Rectangle painted Theme colour (candidate fix B)
  translucent  - transparent clear + top-level WA_TranslucentBackground (Qt docs' recipe)
"""

import os
import sys
import time

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

MODE = os.environ.get("MODE", "transparent")
SURFACE = "#111318"
QML_DIR = os.path.dirname(os.path.abspath(__file__))

qml_plain = """
import QtQuick
Item {
    Rectangle { x: 20; y: 20; width: 40; height: 40; color: "red" }
}
"""
qml_bg = """
import QtQuick
Rectangle {
    color: "#111318"
    Rectangle { x: 20; y: 20; width: 40; height: 40; color: "red" }
}
"""

with open(os.path.join(QML_DIR, "exp_plain.qml"), "w") as f:
    f.write(qml_plain)
with open(os.path.join(QML_DIR, "exp_bg.qml"), "w") as f:
    f.write(qml_bg)

app = QApplication(sys.argv)
top = QWidget()
top.setObjectName("top")
top.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
top.setStyleSheet(f"#top {{ background-color: {SURFACE}; }}")
if MODE == "translucent":
    top.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
lay = QVBoxLayout(top)
lay.setContentsMargins(30, 30, 30, 30)

quick = QQuickWidget()
quick.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
if MODE == "opaque":
    quick.setClearColor(QColor(SURFACE))
else:
    quick.setClearColor(Qt.GlobalColor.transparent)
src = "exp_bg.qml" if MODE == "qmlbg" else "exp_plain.qml"
quick.setSource(QUrl.fromLocalFile(os.path.join(QML_DIR, src)))
assert quick.status() == QQuickWidget.Status.Ready, quick.errors()
lay.addWidget(quick)
top.resize(300, 300)
top.show()

t0 = time.time()
while time.time() - t0 < 1.5:
    app.processEvents()
    time.sleep(0.02)

screen = QGuiApplication.primaryScreen()
shot = screen.grabWindow(top.winId()).toImage()
grab = top.grab().toImage()


def px(img, x, y):
    return QColor(img.pixel(x, y)).name()


# (100,100) is inside the QQuickWidget but outside the red square -> "transparent" region
# (52,52) is inside the red square (quick at 30,30 offset + 20,20)
# (10,10) is the top-level's own margin
print(
    f"MODE={MODE:12s} platform={QGuiApplication.platformName()} "
    f"backend={os.environ.get('QT_QUICK_BACKEND', 'rhi')} | "
    f"SCREEN: margin={px(shot, 10, 10)} qml-transparent={px(shot, 100, 100)} red={px(shot, 55, 55)} | "
    f"GRAB: margin={px(grab, 10, 10)} qml-transparent={px(grab, 100, 100)} red={px(grab, 55, 55)}"
)
