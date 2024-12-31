import serial
import threading
from collections import deque
from PyQt6 import QtWidgets
from GUI import MainWindow, FFTWindow, Measurement_Window
from collections import deque
from threading import Lock


baud_rate = 9600
# port config
ser = serial.Serial(port='COM3', baudrate=baud_rate, timeout=1)

# the buffer length determine how much signal you can see in once 
# bigger buffer result in more sata visible at a time
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
                pass 

if __name__ == "__main__":

    sample_rate = 1000
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

    # GUI
    app = QtWidgets.QApplication([])
    
    # the actualal range of x(time) is x_range/x_factor, so by defult is 0s to 0.05s
    main = MainWindow(data_buffer=data_buffer,sample_rate=sample_rate, x_range=(0, 50), y_range=(-500,500), x_factor=2000)
    fft = FFTWindow(data_buffer=data_buffer, sample_rate=sample_rate, x_range=(0,5000), x_res=1, y_range=(0, 20), y_res=1, fps=30)
    measurements = Measurement_Window(data_buffer=data_buffer, sample_rate=sample_rate,fps=30)

    main.show()
    fft.show()
    measurements.show()

    app.exec()
