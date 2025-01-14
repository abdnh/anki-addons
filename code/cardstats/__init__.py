# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Show statistics about the current and previous card while reviewing.
# Activate from the tools menu.
#

from anki.hooks import addHook
from aqt import colors, mw
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.webview import AnkiWebView


class CardStats(object):
    def __init__(self, mw):
        self.mw = mw
        self.shown = False
        addHook("showQuestion", self._update)
        addHook("deckClosing", self.hide)
        addHook("reviewCleanup", self.hide)

    def _addDockable(self, title, w):
        class DockableWithClose(QDockWidget):
            closed = pyqtSignal()

            def closeEvent(self, evt):
                self.closed.emit()
                QDockWidget.closeEvent(self, evt)

        dock = DockableWithClose(title, mw)
        dock.setObjectName(title)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        dock.setWidget(w)
        if mw.width() < 600:
            mw.resize(QSize(600, mw.height()))
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        return dock

    def _remDockable(self, dock):
        mw.removeDockWidget(dock)

    def show(self):
        if not self.shown:

            class ThinAnkiWebView(AnkiWebView):
                def sizeHint(self):
                    return QSize(200, 100)

            self.web = ThinAnkiWebView()
            self.shown = self._addDockable(("Card Info"), self.web)
            self.shown.closed.connect(self._onClosed)
        self._update()

    def hide(self):
        if self.shown:
            self._remDockable(self.shown)
            self.shown = None
            # actionself.mw.form.actionCstats.setChecked(False)

    def toggle(self):
        if self.shown:
            self.hide()
        else:
            self.show()

    def _onClosed(self):
        # schedule removal for after evt has finished
        self.mw.progress.timer(100, self.hide, False)

    def _update(self):
        if not self.shown:
            return
        txt = ""
        r = self.mw.reviewer
        d = self.mw.col
        if r.card:
            txt += "<h3>Current</h3>"
            txt += d.cardStats(r.card)
        lc = r.lastCard()
        if lc:
            txt += "<h3>Last</h3>"
            txt += d.cardStats(lc)
        if not txt:
            txt = "No current card or last card."
        style = self._style()
        self.web.setHtml(
            """
<html><head>
</head><style>%s</style>
<body><center>%s</center></body></html>"""
            % (style, txt)
        )

    def _style(self):
        return f"""
td {{
    font-size: 80%; }}
body {{
    background: {theme_manager.color(colors.WINDOW_BG)} }}
td, h3, center {{ 
    color: {theme_manager.color(colors.TEXT_FG)}
}}
"""


_cs = CardStats(mw)


def cardStats(on):
    _cs.toggle()


action = QAction(mw)
action.setText("Card Stats")
action.setCheckable(True)
action.setShortcut(QKeySequence("Ctrl+Alt+C"))
mw.form.menuTools.addAction(action)
action.toggled.connect(cardStats)  # type: ignore
