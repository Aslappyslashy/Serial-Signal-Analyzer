import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
import sys
import random
from collections import deque
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QCheckBox, QHBoxLayout, QFrame, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QDoubleValidator  
from PyQt6.QtWidgets import QComboBox  
import pyqtgraph as pg
import numpy as np
import time
import scipy.signal as signal



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, data_buffer, sample_rate=9600, x_range=(0, 100), y_range=(-5000,5000), x_factor=2000):
        super().__init__()


        self.x_range = x_range
        self.y_range = y_range
        self.x_factor = x_factor

        self.baud_rate = sample_rate
        self.data_buffer = data_buffer  # Rolling buffer
        self.is_paused = False

        self.Lowpass = 0
        self.Highpass = 0
        self.notch = 0


        self.setWindowTitle("Real-Time Signal Viewer")
        

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('k')
        self.plot_graph.showGrid(x=True, y=True)


        self.line_unfiltered = self.plot_graph.plot([], [], pen=pg.mkPen(color='w', width=1), name="Unfiltered")
        self.lowpass_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='g', width=1), name="Low-pass")
        self.highpass_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='b', width=1), name="High-pass")
        self.notch_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='m', width=1), name="Notch")
        self.code_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='r', width=1), name="code")

        main_layout = QHBoxLayout()


        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.Shape.Box)

        graphs_frame = QFrame()
        graphs_frame.setFrameShape(QFrame.Shape.Box)

        controls_layout = QVBoxLayout()
        graphs_layout = QVBoxLayout()


        self.create_slider_and_input(controls_layout)
        
        self.trigger_value_label = QLabel("Trigger Value:")
        self.trigger_value_input = QLineEdit("0") 
        self.trigger_value_input.setValidator(QDoubleValidator()) 

        self.trigger_edge_label = QLabel("Trigger Edge:")
        self.trigger_edge_combo = QComboBox()
        self.trigger_edge_combo.addItems(["Rising", "Falling"]) 

        controls_layout.addWidget(self.trigger_value_label)
        controls_layout.addWidget(self.trigger_value_input)
        controls_layout.addWidget(self.trigger_edge_label)
        controls_layout.addWidget(self.trigger_edge_combo)


        self.checkbox_lowpass = QCheckBox("Low Pass filter")
        self.checkbox_lowpass.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.checkbox_lowpass)

        self.LowpassValue = QLineEdit()
        self.LowpassValue.setText(str(self.Lowpass))
        controls_layout.addWidget(self.LowpassValue)

        self.checkbox_highpass = QCheckBox("High Pass filter")
        self.checkbox_highpass.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.checkbox_highpass)

        self.HighpassValue = QLineEdit()
        self.HighpassValue.setText(str(self.Highpass))
        controls_layout.addWidget(self.HighpassValue)

        self.checkbox_notch = QCheckBox("Notch filter")
        self.checkbox_notch.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.checkbox_notch)

        self.NotchValue = QLineEdit()
        self.NotchValue.setText(str(self.notch))
        controls_layout.addWidget(self.NotchValue)

        self.NotchQValue = QLineEdit()
        self.NotchQValue.setText("4") 
        controls_layout.addWidget(self.NotchQValue)


        self.checkbox_code = QCheckBox("Code")
        self.checkbox_code.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.checkbox_code)
        self.Code = QLineEdit()
        self.Code.setText("hp:500;lp:50;n:50,1") 
        controls_layout.addWidget(self.Code)
        
        # add control
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button)

        self.toggle_unfiltered_button = QPushButton("Toggle Unfiltered Line")
        self.toggle_unfiltered_button.clicked.connect(self.toggle_unfiltered_visibility)
        controls_layout.addWidget(self.toggle_unfiltered_button)

        self.toggle_filtered_button = QPushButton("Toggle Filtered Line")
        self.toggle_filtered_button.clicked.connect(self.toggle_filtered_visibility)
        controls_layout.addWidget(self.toggle_filtered_button)


        controls_frame.setLayout(controls_layout)


        main_layout.addWidget(self.plot_graph, stretch=3)
        main_layout.addWidget(controls_frame, stretch=1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def create_slider_and_input(self, layout):
        """Create sliders and input boxes for adjusting X and Y ranges."""
        self.x_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.x_range_slider.setRange(self.x_range[0],self.x_range[1]) 
        self.x_range_slider.setValue(100)
        self.x_range_slider.valueChanged.connect(self.update_x_range)
        
        self.y_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.y_range_slider.setRange(self.y_range[0],self.y_range[1]) 
        self.y_range_slider.setValue(5000)
        self.y_range_slider.valueChanged.connect(self.update_y_range)
        
        self.x_range_input = QLineEdit()
        self.y_range_input = QLineEdit()
        self.x_range_input.setText(str(self.x_range_slider.value()))
        self.y_range_input.setText(str(self.y_range_slider.value()))
        self.x_range_input.textChanged.connect(self.update_x_range_from_input)
        self.y_range_input.textChanged.connect(self.update_y_range_from_input)
        layout.addWidget(QLabel("Time Domain Control"))
        layout.addWidget(self.x_range_slider)
        layout.addWidget(self.x_range_input)
        layout.addWidget(QLabel("Voltage Control"))
        layout.addWidget(self.y_range_slider)
        layout.addWidget(self.y_range_input)
    
    def auto_set_trigger_value(self):
        if self.data_buffer:
            avg_value = sum(self.data_buffer) / len(self.data_buffer)
            self.trigger_value_input.setText(f"{avg_value:.2f}")

    
    def find_trigger_point(self, data):
        try:
            trigger_value = float(self.trigger_value_input.text()) 
            trigger_edge = self.trigger_edge_combo.currentText()  


            for i in range(1, len(data)):
                if trigger_edge == "Rising" and data[i - 1] < trigger_value <= data[i]:
                    return i  
                elif trigger_edge == "Falling" and data[i - 1] > trigger_value >= data[i]:
                    return i  


            return None
        except ValueError:
            print("Invalid trigger value.")
            return None

    def update_plot(self):
        if not self.is_paused:
            data = list(self.data_buffer)  
            if not data:
                return

            # trigger alignment
            trigger_index = self.find_trigger_point(data)
            if trigger_index is not None:
                data = data[trigger_index:] + data[:trigger_index]
            else:
                print("No trigger point found. Displaying unaligned data.")

            # time axis
            x = [i * (1 / self.baud_rate) for i in range(len(data))]

            # Unfiltered data
            y_unfiltered = data
            self.line_unfiltered.setData(x, y_unfiltered)

            #FILTERS
            if self.checkbox_lowpass.isChecked():
                lowpass_data = self.lowpass_filter(data)
                self.lowpass_line.setData(x, lowpass_data)
            else:
                self.lowpass_line.clear()

            if self.checkbox_highpass.isChecked():
                highpass_data = self.highpass_filter(data)
                self.highpass_line.setData(x, highpass_data)
            else:
                self.highpass_line.clear()

            if self.checkbox_notch.isChecked():
                notch_data = self.notch_filter(data)
                self.notch_line.setData(x, notch_data)
            else:
                self.notch_line.clear()

            if self.checkbox_code.isChecked():
                code_data = self.apply_custom_filters(data)
                self.code_line.setData(x, code_data)
            else:
                self.code_line.clear()

    def lowpass_filter(self, data):
        try:
            cutoff = int(self.LowpassValue.text())
            nyquist = 0.5 * self.baud_rate
            if cutoff <= 0 or cutoff >= nyquist:
                raise ValueError("Cutoff frequency out of range.")
            normalized_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            return signal.filtfilt(b, a, data)
        except ValueError as e:
            print(f"Low-pass filter error: {e}")
            return data

    def highpass_filter(self, data):
        try:
            cutoff = int(self.HighpassValue.text())
            nyquist = 0.5 * self.baud_rate
            if cutoff <= 0 or cutoff >= nyquist:
                raise ValueError("Cutoff frequency out of range.")
            normalized_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='high')
            return signal.filtfilt(b, a, data)
        except ValueError as e:
            print(f"High-pass filter error: {e}")
            return data

    def notch_filter(self, data):
        try:
            freq = float(self.NotchValue.text())
            nyquist = 0.5 * self.baud_rate
            if freq <= 0 or freq >= nyquist:
                raise ValueError("Notch frequency out of range.")
            Q = int(self.NotchQValue.text())
            b, a = signal.iirnotch(freq / nyquist, Q)
            return signal.filtfilt(b, a, data)
        except ValueError as e:
            print(f"Notch filter error: {e}")
            return data




    def update_x_range(self):
        value = self.x_range_slider.value()/self.x_factor
        self.plot_graph.setXRange(0, value)
        self.x_range_input.setText(str(value))

    def update_x_range_from_input(self):
        try:
            value = int(self.x_range_input.text())
            self.x_range_slider.setValue(value)
        except ValueError:
            pass

    def update_y_range(self):
        value = self.y_range_slider.value()
        self.plot_graph.setYRange(-value, value)
        self.y_range_input.setText(str(value))

    def update_y_range_from_input(self):
        try:
            value = int(self.y_range_input.text())
            self.y_range_slider.setValue(value)
        except ValueError:
            pass

    def toggle_pause(self):
        self.is_paused = not self.is_paused

    def toggle_unfiltered_visibility(self):
        self.line_unfiltered.setVisible(not self.line_unfiltered.isVisible())

    def toggle_filtered_visibility(self):

        self.lowpass_line.setVisible(not self.lowpass_line.isVisible())
        self.highpass_line.setVisible(not self.highpass_line.isVisible())
        self.notch_line.setVisible(not self.notch_line.isVisible())
        self.code_line.setVisible(not self.code_line.isVisible())


        
        
    def apply_custom_filters(self, data):
        commands = self.Code.text().split(';')
        #i = 0
        for cmd in commands:
            cmd_d = cmd.split(':')
            if cmd_d[0] == 'hp':  
                try:
                    cutoff = int(cmd_d[1])
                    nyquist = 0.5 * self.baud_rate
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(4, normalized_cutoff, btype='high')
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    print("Invalid highpass filter command. Format: hp:<cutoff_frequency>")
            elif cmd_d[0] == 'lp':  
                try:
                    cutoff = int(cmd_d[1])
                    nyquist = 0.5 * self.baud_rate
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(4, normalized_cutoff, btype='low')
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    print("Invalid lowpass filter command. Format: lp:<cutoff_frequency>")
            elif cmd_d[0] == 'n':  # Notch filter
                try:
                    cmd_d_d = cmd_d[1].split(',')
                    freq = float(cmd_d_d[0])
                    nyquist = 0.5 * self.baud_rate
                    Q = int(cmd_d_d[1])
                    b, a = signal.iirnotch(freq / nyquist, Q)
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    print("Invalid notch filter command. Format: n:<frequency>,<Q-factor>")
            else:
                print(f"Unknown command: {cmd_d[0]}. Use 'hp', 'lp', or 'n'.")
            #print(i)
            #i+=1
        return data




class FFTWindow(QtWidgets.QWidget):
    def __init__(self, data_buffer, sample_rate, x_range=(0,5000), x_res=1, y_range=(0, 20), y_res=1, fps=30):
        super().__init__()
        
        self.x_range = x_range
        self.x_resolution = x_res
        self.y_range = y_range
        self.y_resolution = y_res
        self.fps = fps
        
        self.is_paused = False
        layout = QVBoxLayout()
        self.baud_rate = sample_rate  # very important that this is the sample rate
        self.data_buffer = data_buffer

        self.freq = []
        self.fft_values = []

        # FFT window
        self.setWindowTitle("FFT Viewer")
        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.fft_line = self.plot.plot([], [], pen=pg.mkPen(color='w', width=1))
        

        self.x_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.x_range_slider.setRange(self.x_range[0], self.x_range[1])
        self.x_range_slider.setValue(100)
        self.x_range_slider.setTickInterval(self.x_resolution)
        self.x_range_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.x_range_slider.valueChanged.connect(self.update_x_range)

        self.y_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.y_range_slider.setRange(self.y_range[0], self.y_range[1])
        self.y_range_slider.setValue(0)
        self.y_range_slider.setTickInterval(self.y_resolution)
        self.y_range_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.y_range_slider.valueChanged.connect(self.update_y_range)
        
        layout.addWidget(self.x_range_slider)
        layout.addWidget(self.y_range_slider)
        
        
        
        self.x_range_input = QLineEdit()
        self.y_range_input = QLineEdit()
        self.x_range_input.setText(str(self.x_range_slider.value()))
        self.y_range_input.setText(str(self.y_range_slider.value()))
        
        self.x_range_input.textChanged.connect(self.update_x_range_from_input)
        self.y_range_input.textChanged.connect(self.update_y_range_from_input)
        
        layout.addWidget(self.x_range_input)
        layout.addWidget(self.y_range_input)
        


        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_button)
        
        self.setLayout(layout)


        self.timer = QTimer()
        self.timer.setInterval(int((1/self.fps)*1000)) # set fps for FFT window, too high migh result in low performace
        self.timer.timeout.connect(self.update_fft_plot)
        self.timer.start()

    def update_fft_plot(self):
        """Update the FFT plot with new data."""
        if len(self.data_buffer) > 0:
            data = list(self.data_buffer)  
            self.freq, self.fft_values = self.calculate_fft(data)
            self.fft_line.setData(self.freq, self.fft_values)  

    def log_scaling(self, values):
        values = np.array(values)
        values = np.log1p(values)  
        return (values - np.min(values)) / (np.max(values) - np.min(values)) * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

    def min_max_scaling(self, values):
        values = np.array(values)
        min_val, max_val = np.min(values), np.max(values)
        return (values - min_val) / (max_val - min_val) * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

    def calculate_fft(self, data):
        """Calculate FFT of the data"""

        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1/self.baud_rate)
        return freqs, self.min_max_scaling(fft_values)
    
    def update_x_range(self):
        """Update the x-axis range based on slider value"""
        x_range_value = self.x_range_slider.value()
        self.plot.setXRange(0, x_range_value)
        self.x_range_input.setText(str(x_range_value))
        
    def update_x_range_from_input(self):
        """Update the x-range slider based on input box value"""
        try:
            new_value = int(self.x_range_input.text())
            if self.x_range[0] <= new_value <= self.x_range[1]:
                self.x_range_slider.setValue(new_value)
        except ValueError:
            self.x_range_slider.setValue(self.x_range_slider.value()) 
            
    def update_y_range(self):
        """Update the y-axis range based on slider value"""
        y_min = -self.y_range_slider.value()
        y_max = self.y_range_slider.value()
        self.plot.setYRange(y_min, y_max)
        self.y_range_input.setText(str(y_min))
    
    def update_y_range_from_input(self):
        """Update the y-range slider based on input box value"""
        try:
            new_value = int(self.y_range_input.text())
            if self.y_range[0] <= new_value <= self.y_range[1]:
                self.y_range_slider.setValue(new_value)
        except ValueError:
            pass  
    
    def toggle_pause(self):
        # Pause/resume the updates
        self.is_paused = not self.is_paused

    def low_pass_filter(self, data, cutoff_freq):
        """Apply a low-pass filter to the data."""
        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1/self.baud_rate)
        filtered_fft = np.where(np.abs(freqs) > cutoff_freq, 0, fft_values)
        return np.fft.ifft(filtered_fft).real
    
    def high_pass_filter(self, data, cutoff_freq):
        """Apply a high-pass filter to the data."""
        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1/self.baud_rate)
        filtered_fft = np.where(np.abs(freqs) < cutoff_freq, 0, fft_values)
        return np.fft.ifft(filtered_fft).real
    
    def band_pass_filter(self, data, low_cutoff, high_cutoff):
        """Apply a band-pass filter to the data."""
        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1/self.baud_rate)
        filtered_fft = np.where((np.abs(freqs) < low_cutoff) | (np.abs(freqs) > high_cutoff), 0, fft_values)
        return np.fft.ifft(filtered_fft).real
    
    def notch_filter(self, data, notch_freq, bandwidth):
        """Apply a notch filter to the data."""
        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1/self.baud_rate)
        filtered_fft = fft_values.copy()
        filtered_fft[np.abs(freqs - notch_freq) < bandwidth] = 0
        return np.fft.ifft(filtered_fft).real
