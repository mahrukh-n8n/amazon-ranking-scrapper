import logging
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import QObject, pyqtSignal

class LogHandler(logging.Handler, QObject):
    # Signal to emit log message to UI thread
    new_log = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self) # Initialize QObject
        logging.Handler.__init__(self) # Initialize logging.Handler
        self.widget = None

    def set_widget(self, widget: QPlainTextEdit):
        self.widget = widget
        self.new_log.connect(self.append_log)

    def emit(self, record):
        msg = self.format(record)
        self.new_log.emit(msg)

    def append_log(self, msg):
        if self.widget:
            self.widget.appendPlainText(msg)
            # Auto-scroll
            self.widget.verticalScrollBar().setValue(
                self.widget.verticalScrollBar().maximum()
            )
