import winsound
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QObject
import logging

logger = logging.getLogger(__name__)

class CaptchaAlerter(QObject):
    """Handles alerting user when captcha is detected."""

    def __init__(self, main_window: QMainWindow = None):
        super().__init__()
        self.main_window = main_window

    def set_window(self, window: QMainWindow):
        """Set the main window reference for focus activation."""
        self.main_window = window

    def play_alert(self):
        """
        Play alert sound and bring window to attention.
        Called when captcha is detected.
        """
        logger.info("Captcha alert triggered!")

        # 1. Play system alert sound (Windows)
        try:
            # MB_ICONEXCLAMATION plays the system exclamation sound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as e:
            logger.warning(f"Could not play alert sound: {e}")

        # 2. Bring window to front / request attention
        if self.main_window:
            try:
                # Activate the window
                self.main_window.activateWindow()
                self.main_window.raise_()

                # Flash taskbar if minimized (Windows)
                if self.main_window.isMinimized():
                    self.main_window.showNormal()

                # Request attention via alert (taskbar flash on Windows)
                app = QApplication.instance()
                if app:
                    app.alert(self.main_window, 0)  # 0 = indefinite flash
            except Exception as e:
                logger.warning(f"Could not activate window: {e}")
