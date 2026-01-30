import winsound
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)

class NotificationManager(QObject):
    """Handles alerts and notifications for the user."""

    def __init__(self, main_window: QMainWindow = None):
        super().__init__()
        self.main_window = main_window

    def set_window(self, window: QMainWindow):
        """Set the main window reference for focus activation."""
        self.main_window = window

    def play_captcha_alert(self):
        """Play alert sound and bring window to attention for CAPTCHA."""
        logger.info("Captcha alert triggered!")
        self._alert(sound=winsound.MB_ICONEXCLAMATION)

    def play_completion_alert(self):
        """Play alert sound and bring window to attention for job completion."""
        logger.info("Completion alert triggered!")
        self._alert(sound=winsound.MB_ICONASTERISK)

    def _alert(self, sound=winsound.MB_ICONEXCLAMATION):
        """Internal helper for playing sound and flashing taskbar."""
        # 1. Play system alert sound (Windows)
        try:
            winsound.MessageBeep(sound)
        except Exception as e:
            logger.warning(f"Could not play alert sound: {e}")

        # 2. Bring window to front / request attention
        if self.main_window:
            try:
                # Request attention via alert (taskbar flash on Windows)
                app = QApplication.instance()
                if app:
                    app.alert(self.main_window, 0)  # 0 = indefinite flash until focused
            except Exception as e:
                logger.warning(f"Could not trigger application alert: {e}")
