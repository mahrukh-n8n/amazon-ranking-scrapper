from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel,
    QPlainTextEdit, QFileDialog, QHBoxLayout, QGroupBox,
    QLineEdit, QCheckBox, QFormLayout
)
from qasync import asyncSlot
import logging
from src.scraper_controller import ScraperController
from src.ui.log_handler import LogHandler
from src.data_loader import DataLoader
from src.notification_manager import NotificationManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amazon Geo-Rank Scraper")
        self.resize(800, 700)

        self.controller = ScraperController()
        self.notifier = NotificationManager(self)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Title Label
        title = QLabel("Amazon Geo-Rank Scraper")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # File Loading Section
        file_layout = QHBoxLayout()

        self.btn_load = QPushButton("Load Job File (CSV/Excel)")
        self.btn_load.clicked.connect(self.on_load_clicked)
        file_layout.addWidget(self.btn_load)

        self.lbl_tasks = QLabel("Tasks Loaded: 0")
        file_layout.addWidget(self.lbl_tasks)

        layout.addLayout(file_layout)

        # Settings Section
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        settings_group.setLayout(settings_layout)

        self.edit_webhook = QLineEdit()
        self.edit_webhook.setPlaceholderText("https://webhook.site/...")
        self.edit_webhook.textChanged.connect(self.update_controller_settings)
        settings_layout.addRow("Webhook URL:", self.edit_webhook)

        self.cb_webhook_enabled = QCheckBox("Enable Webhook Integration")
        self.cb_webhook_enabled.stateChanged.connect(self.update_controller_settings)
        settings_layout.addRow("", self.cb_webhook_enabled)

        self.cb_notify_enabled = QCheckBox("Enable Desktop Notification on Completion")
        self.cb_notify_enabled.setChecked(True)
        settings_layout.addRow("", self.cb_notify_enabled)

        layout.addWidget(settings_group)

        # Control Buttons Layout
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("Start Job")
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_start.setEnabled(False) # Disabled until tasks are loaded
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop Job")
        self.btn_stop.setEnabled(False) # Disabled initially
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        btn_layout.addWidget(self.btn_stop)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setEnabled(False)
        btn_layout.addWidget(self.btn_pause)

        self.btn_resume = QPushButton("Resume")
        self.btn_resume.setEnabled(False)
        btn_layout.addWidget(self.btn_resume)

        # Connect button signals
        self.btn_pause.clicked.connect(self.on_pause_clicked)
        self.btn_resume.clicked.connect(self.on_resume_clicked)

        # Connect controller signals
        self.controller.paused.connect(self.on_job_paused)
        self.controller.resumed.connect(self.on_job_resumed)
        self.controller.captcha_detected.connect(self.on_captcha_detected)
        self.controller.task_started.connect(self.on_task_started)
        self.controller.job_finished.connect(self.on_job_finished)

        layout.addLayout(btn_layout)

        # Status bar
        status_layout = QHBoxLayout()

        self.lbl_status = QLabel("Status: Idle")
        self.lbl_status.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.lbl_status)

        status_layout.addStretch()

        self.lbl_progress = QLabel("Progress: 0/0")
        status_layout.addWidget(self.lbl_progress)

        layout.addLayout(status_layout)

        # Log Window
        log_label = QLabel("Activity Log:")
        layout.addWidget(log_label)

        self.log_widget = QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        layout.addWidget(self.log_widget)

        # Setup Logging
        self.setup_logging()

    def update_controller_settings(self):
        """Sync UI settings with controller."""
        self.controller.webhook_url = self.edit_webhook.text().strip()
        self.controller.webhook_enabled = self.cb_webhook_enabled.isChecked()

    def setup_logging(self):
        # Create custom handler
        handler = LogHandler()
        handler.set_widget(self.log_widget)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Get root logger (or specific logger) and add handler
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def on_load_clicked(self):
        """Handle Load Job button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Job File",
            "",
            "Job Files (*.csv *.xlsx *.xls)"
        )

        if file_path:
            try:
                tasks = DataLoader.load_file(file_path)
                self.controller.set_tasks(tasks)
                self.lbl_tasks.setText(f"Tasks Loaded: {len(tasks)}")
                logging.info(f"Successfully loaded {len(tasks)} tasks from {file_path}")

                if len(tasks) > 0:
                    self.btn_start.setEnabled(True)
                else:
                    self.btn_start.setEnabled(False)

            except Exception as e:
                logging.error(f"Failed to load file: {e}")
                self.lbl_tasks.setText("Tasks Loaded: Error")
                self.btn_start.setEnabled(False)

    @asyncSlot()
    async def on_start_clicked(self):
        """Handle Start button click."""
        self.btn_start.setEnabled(False)
        self.btn_load.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.lbl_status.setText("Status: Running")
        self.lbl_status.setStyleSheet("font-weight: bold; color: green;")

        try:
            await self.controller.start_job()
        finally:
            self.on_job_finished()

    def on_stop_clicked(self):
        """Handle Stop button click."""
        # This is synchronous because we just set a flag
        self.controller.stop_job()
        self.btn_stop.setEnabled(False)

    def on_pause_clicked(self):
        """Handle Pause button click."""
        self.controller.pause_job()

    def on_resume_clicked(self):
        """Handle Resume button click."""
        self.controller.resume_job()

    def on_job_paused(self):
        """Handle job paused signal from controller."""
        self.lbl_status.setText("Status: Paused")
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)

    def on_job_resumed(self):
        """Handle job resumed signal from controller."""
        self.lbl_status.setText("Status: Running")
        self.lbl_status.setStyleSheet("font-weight: bold; color: green;")
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def on_captcha_detected(self):
        """Handle captcha detected signal from controller."""
        self.lbl_status.setText("Status: CAPTCHA - Solve and Resume")
        self.lbl_status.setStyleSheet("font-weight: bold; color: red;")
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)
        self.notifier.play_captcha_alert()

    def on_task_started(self, current: int, total: int):
        """Handle task started signal from controller."""
        self.lbl_progress.setText(f"Progress: {current}/{total}")

    def on_job_finished(self):
        """Handle job finished signal from controller."""
        # Only trigger completion notification if it's actually finishing (not just returning from await)
        # We check if it's currently Idle to avoid double-triggering
        if self.lbl_status.text() == "Status: Idle":
            return

        self.lbl_status.setText("Status: Idle")
        self.lbl_status.setStyleSheet("font-weight: bold; color: black;")
        self.lbl_progress.setText("Progress: 0/0")
        self.btn_start.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)

        if self.cb_notify_enabled.isChecked():
            self.notifier.play_completion_alert()

