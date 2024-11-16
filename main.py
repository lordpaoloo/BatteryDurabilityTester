import sys
import os
import time
import psutil
import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel


def resource_path(relative_path):
    """Helper function to access resources in PyInstaller bundled app."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class BatteryTestApp(QMainWindow):
    def __init__(self, video_file):
        super().__init__()
        self.setWindowTitle('Battery Duration Test')

        # Set application icon
        icon_path = resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # Video display label
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_label)
        self.video_label.setScaledContents(True)

        # Timer label
        self.timer_label = QLabel(self.video_label)
        self.timer_label.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 24, QFont.Bold)
        self.timer_label.setFont(font)
        self.timer_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 0.6);")
        self.timer_label.setGeometry(10, 10, 300, 50)  # Initial size, adjusted dynamically

        # Battery label
        self.battery_label = QLabel(self.video_label)
        self.battery_label.setAlignment(Qt.AlignCenter)
        self.battery_label.setFont(font)
        self.battery_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 0.6);")
        self.battery_label.setGeometry(10, 300, 300, 50)  # Initial size, adjusted dynamically

        # Load video
        self.cap = cv2.VideoCapture(resource_path(video_file))
        if not self.cap.isOpened():
            print("Error opening video stream or file")
            sys.exit()

        # Timers
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_frame)
        self.video_timer.start(30)

        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(1000)  # Updates every second

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.save_battery_report)
        self.log_timer.start(5 * 60 * 1000)  # Save log every 5 minutes

        # Stopwatch variables
        self.start_time = time.time()
        self.update_timer_label()

    def update_frame(self):
        """Update video frames."""
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        """Release resources when the app is closed."""
        self.cap.release()
        event.accept()

    def update_battery_status(self):
        """Update battery status on the label."""
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            status = 'Charging' if battery.power_plugged else 'Discharging'
            self.battery_label.setText(f"Battery: {percent}% - {status}")
        else:
            self.battery_label.setText("Battery: Not Available")

    def save_battery_report(self):
        """Save battery status log to a file."""
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            status = 'Charging' if battery.power_plugged else 'Discharging'

            elapsed_time = time.time() - self.start_time
            hours, remainder = divmod(int(elapsed_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

            report_line = f"{elapsed_time_str} - Battery: {percent}% - {status}\n"
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", "Battery Report.txt")
            with open(file_path, "a") as f:
                f.write(report_line)

    def update_timer_label(self):
        """Update the stopwatch timer label."""
        elapsed_time = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed_time), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.setText(f"Time: {hours:02}:{minutes:02}:{seconds:02}")
        QTimer.singleShot(1000, self.update_timer_label)

    def resizeEvent(self, event):
        """Resize event handler to adjust the labels' positions."""
        self.video_label.resize(self.width(), self.height())
        # Place labels at the bottom
        label_width = 300
        label_height = 50
        bottom_offset = 10
        self.battery_label.setGeometry(
            (self.width() - label_width) // 2, self.height() - label_height * 2 - bottom_offset, label_width, label_height
        )
        self.timer_label.setGeometry(
            (self.width() - label_width) // 2, self.height() - label_height - bottom_offset, label_width, label_height
        )
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_file = "test.mp4"  # Name of the video file
    player = BatteryTestApp(video_file)
    player.showFullScreen()
    sys.exit(app.exec_())
