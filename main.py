import serial
import threading
from collections import deque
from PyQt6 import QtWidgets
from GUI import MainWindow, FFTWindow
from collections import deque
from threading import Lock

# Serial port configuration
ser = serial.Serial(port='COM3', baudrate=38400, timeout=1)


data_buffer = deque(maxlen=4096)
buffer_lock = Lock()

def read_serial():
    while True:
        line = ser.readline()
        if line:
            try:
                with buffer_lock:
                    value = float(line.decode().strip())
                    data_buffer.append(value)
            except ValueError:
                pass  # Handle invalid data


if __name__ == "__main__":
    # Start the serial reader thread
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

    # Start the GUI application
    app = QtWidgets.QApplication([])
    main = MainWindow(data_buffer=data_buffer, baud_rate=5000)
    fft = FFTWindow(data_buffer=data_buffer, baud_rate=5000)

    main.show()
    fft.show()

    app.exec()
