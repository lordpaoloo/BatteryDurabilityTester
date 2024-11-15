import sys
import os
import time
import psutil
import cv2
import wmi
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel


def get_resource_path(relative_path):
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)


class BatteryTestApp(QMainWindow):
    def __init__(self, video_file):
        super().__init__()

        self.setWindowTitle('Battery Duration Test')
        self.setWindowIcon(QIcon(get_resource_path("icon.ico")))

        self._initialize_ui()
        self._initialize_video(video_file)
        self._initialize_battery_monitoring()

        self.start_time = time.time()

    def _initialize_ui(self):
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_label)
        self.video_label.setScaledContents(True)

        self.timer_label = QLabel(self.video_label)
        self.battery_label = QLabel(self.video_label)

        self._set_label_styles()

    def _initialize_video(self, video_file):
        self.cap = cv2.VideoCapture(get_resource_path(video_file))
        if not self.cap.isOpened():
            print("Error opening video stream or file")
            sys.exit()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def _initialize_battery_monitoring(self):
        self.initial_report_done = False

        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(5 * 60 * 1000)

        self.save_report_timer = QTimer(self)
        self.save_report_timer.timeout.connect(self.save_battery_report)
        self.save_report_timer.start(5 * 60 * 1000)

    def _set_label_styles(self):
        font = QFont("Arial", 24, QFont.Bold)
        self.timer_label.setFont(font)
        self.battery_label.setFont(font)
        self.timer_label.setStyleSheet("color: white;")
        self.battery_label.setStyleSheet("color: white;")

    def update_frame(self):
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

    def update_battery_status(self):
        battery = psutil.sensors_battery()
        if battery:
            self.battery_percent = battery.percent
            self.battery_status = 'Charging' if battery.power_plugged else 'Discharging'
            self.battery_time_left = battery.secsleft / 60 if battery.power_plugged else None
            self.battery_label.setText(f"Battery: {self.battery_percent}% - {self.battery_status}")
            if not self.initial_report_done:
                self.save_battery_report()
                self.initial_report_done = True
        else:
            self.battery_label.setText("Battery: No Info")
            self.battery_percent = "No B.T"
            self.battery_status = "No B.T"

    def save_battery_report(self):
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        elapsed_time_str = f"{minutes:02}:{seconds:02}"

        report_line = f"{elapsed_time_str} - Battery: {self.battery_percent} - {self.battery_status}"
        if self.battery_time_left is not None:
            report_line += f" - Time left: {self.battery_time_left:.2f} minutes"

        with open(get_resource_path("battery_report.txt"), "a") as f:
            f.write(report_line + "\n")

    def update_timer_label(self):
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        self.timer_label.setText(f"Time: {minutes:02}:{seconds:02}")
        QTimer.singleShot(1000, self.update_timer_label)

    def resizeEvent(self, event):
        self.video_label.resize(self.width(), self.height())
        self.timer_label.move(self.width() // 2 - self.timer_label.width() // 2, self.height() - 80)
        self.battery_label.move(self.width() // 2 - self.battery_label.width() // 2, self.height() - 40)
        event.accept()

    def set_brightness(self, brightness):
        try:
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(brightness, 0)
        except Exception as e:
            print("Could not set brightness:", e)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_file = 'test.mp4'
    player = BatteryTestApp(video_file)
    player.showFullScreen()
    sys.exit(app.exec_())
