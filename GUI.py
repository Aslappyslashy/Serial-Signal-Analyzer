import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
import sys
import random
from collections import deque
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QCheckBox, QHBoxLayout, QFrame, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QDoubleValidator  # For validating decimal numbers in input
from PyQt6.QtWidgets import QComboBox  # For creating dropdown menus
import pyqtgraph as pg
import numpy as np
import time
import scipy.signal as signal



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, data_buffer, baud_rate=9600):
        super().__init__()

        # Initialize parameters
        self.x_range = (0, 100)
        self.y_range = (-5000, 5000)

        self.baud_rate = baud_rate
        self.data_buffer = data_buffer  # Rolling buffer of data
        self.is_paused = False

        self.Lowpass = 0
        self.Highpass = 0
        self.notch = 0

        # Set up the window
        self.setWindowTitle("Real-Time Signal Viewer")
        
        # Graph widget
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('k')
        self.plot_graph.showGrid(x=True, y=True)

        # Create lines for plotting
        self.line_unfiltered = self.plot_graph.plot([], [], pen=pg.mkPen(color='w', width=1), name="Unfiltered")
        self.lowpass_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='g', width=1), name="Low-pass")
        self.highpass_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='b', width=1), name="High-pass")
        self.notch_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='m', width=1), name="Notch")
        self.code_line = self.plot_graph.plot([], [], pen=pg.mkPen(color='r', width=1), name="code")

        # Create main layout
        main_layout = QHBoxLayout()

        # Create control and graph frames
        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.Shape.Box)

        graphs_frame = QFrame()
        graphs_frame.setFrameShape(QFrame.Shape.Box)

        # Create layouts for controls and graphs
        controls_layout = QVBoxLayout()
        graphs_layout = QVBoxLayout()

        # Add sliders and inputs
        self.create_slider_and_input(controls_layout)
        
        self.trigger_value_label = QLabel("Trigger Value:")
        self.trigger_value_input = QLineEdit("0")  # Default trigger at 0
        self.trigger_value_input.setValidator(QDoubleValidator())  # Allow decimals

        self.trigger_edge_label = QLabel("Trigger Edge:")
        self.trigger_edge_combo = QComboBox()
        self.trigger_edge_combo.addItems(["Rising", "Falling"])  # Rising or falling edge

        controls_layout.addWidget(self.trigger_value_label)
        controls_layout.addWidget(self.trigger_value_input)
        controls_layout.addWidget(self.trigger_edge_label)
        controls_layout.addWidget(self.trigger_edge_combo)


        # Add checkboxes and their input boxes
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
        self.NotchQValue.setText("4")  # Default Q-factor value
        controls_layout.addWidget(self.NotchQValue)


        self.checkbox_code = QCheckBox("Code")
        self.checkbox_code.stateChanged.connect(self.update_plot)
        controls_layout.addWidget(self.checkbox_code)
        self.Code = QLineEdit()
        self.Code.setText("hp:500;lp:50;n:50,1")  # Default Q-factor value
        controls_layout.addWidget(self.Code)
        
        # Add control buttons
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button)

        self.toggle_unfiltered_button = QPushButton("Toggle Unfiltered Line")
        self.toggle_unfiltered_button.clicked.connect(self.toggle_unfiltered_visibility)
        controls_layout.addWidget(self.toggle_unfiltered_button)

        self.toggle_filtered_button = QPushButton("Toggle Filtered Line")
        self.toggle_filtered_button.clicked.connect(self.toggle_filtered_visibility)
        controls_layout.addWidget(self.toggle_filtered_button)

        # Assign layouts to frames
        controls_frame.setLayout(controls_layout)

        # Add frames and graph to main layout
        main_layout.addWidget(self.plot_graph, stretch=3)
        main_layout.addWidget(controls_frame, stretch=1)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Timer for updating the plot
        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def create_slider_and_input(self, layout):
        """Create sliders and input boxes for adjusting X and Y ranges."""
        self.x_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.x_range_slider.setRange(10, 2000)  # Adjusted range for X-axis
        self.x_range_slider.setValue(100)
        self.x_range_slider.valueChanged.connect(self.update_x_range)
        
        self.y_range_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.y_range_slider.setRange(100, 10000)  # Adjusted range for Y-axis
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
            trigger_value = float(self.trigger_value_input.text())  # Get trigger value
            trigger_edge = self.trigger_edge_combo.currentText()  # "Rising" or "Falling"


            for i in range(1, len(data)):
                if trigger_edge == "Rising" and data[i - 1] < trigger_value <= data[i]:
                    return i  # Trigger on rising edge
                elif trigger_edge == "Falling" and data[i - 1] > trigger_value >= data[i]:
                    return i  # Trigger on falling edge

            # If no trigger point is found, return None
            return None
        except ValueError:
            print("Invalid trigger value.")
            return None

    def update_plot(self):
        if not self.is_paused:
            data = list(self.data_buffer)  # Copy data from the rolling buffer
            if not data:
                return

            trigger_index = self.find_trigger_point(data)  # Find trigger point

            if trigger_index is not None:
                # Align the data to start from the trigger point
                data = data[trigger_index:] + data[:trigger_index]
            else:
                print("No trigger point found. Displaying unaligned data.")

            x = [i * (1 / self.baud_rate) for i in range(len(data))]  # Time axis
            y_unfiltered = data  # Original unfiltered data

            # Update unfiltered line
            self.line_unfiltered.setData(x, y_unfiltered)

            # Apply filters and update other lines (as before)
            if self.checkbox_lowpass.isChecked():
                data = self.lowpass_filter(data)
                self.lowpass_line.setData(x, data)
            else:
                self.lowpass_line.clear()

            if self.checkbox_highpass.isChecked():
                data = self.highpass_filter(data)
                self.highpass_line.setData(x, data)
            else:
                self.highpass_line.clear()

            if self.checkbox_notch.isChecked():
                data = self.notch_filter(data)
                self.notch_line.setData(x, data)
            else:
                self.notch_line.clear()

            if self.checkbox_code.isChecked():
                data = self.apply_custom_filters(data)
                self.code_line.setData(x, data)
            else:
                self.code_line.clear()



    def update_x_range(self):
        value = self.x_range_slider.value()/2000
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
        # Toggle visibility of all filtered lines
        self.lowpass_line.setVisible(not self.lowpass_line.isVisible())
        self.highpass_line.setVisible(not self.highpass_line.isVisible())
        self.notch_line.setVisible(not self.notch_line.isVisible())
        self.code_line.setVisible(not self.code_line.isVisible())


    def lowpass_filter(self, data):
        try:
            cutoff = int(self.LowpassValue.text())
            nyquist = 0.5 * self.baud_rate
            normalized_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            return signal.filtfilt(b, a, data)
        except ValueError:
            print("Invalid lowpass filter value. Please enter a valid number.")
            return data

    def highpass_filter(self, data):
        try:
            cutoff = int(self.HighpassValue.text())
            nyquist = 0.5 * self.baud_rate
            normalized_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normalized_cutoff, btype='high')
            return signal.filtfilt(b, a, data)
        except ValueError:
            print("Invalid highpass filter value. Please enter a valid number.")
            return data


    def notch_filter(self, data):
        try:
            freq = float(self.NotchValue.text())
            nyquist = 0.5 * self.baud_rate
            Q = int(self.NotchQValue.text())
            b, a = signal.iirnotch(freq / nyquist, Q)
            return signal.filtfilt(b, a, data)
        except ValueError:
            print("Invalid notch filter value or Q-factor. Please enter valid numbers.")
            return data
        
        
    def apply_custom_filters(self, data):
        commands = self.Code.text().split(';')
        #i = 0
        for cmd in commands:
            cmd_d = cmd.split(':')
            if cmd_d[0] == 'hp':  # High-pass filter
                try:
                    cutoff = int(cmd_d[1])
                    nyquist = 0.5 * self.baud_rate
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(4, normalized_cutoff, btype='high')
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    print("Invalid highpass filter command. Format: hp:<cutoff_frequency>")
            elif cmd_d[0] == 'lp':  # Low-pass filter
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
    def __init__(self, data_buffer, baud_rate):
        super().__init__()
        
        self.x_range = (0, 5000)
        self.x_resolution = 1
        self.y_range = (0, 20)
        self.y_resolution = 1
        
        self.is_paused = False
        layout = QVBoxLayout()
        self.baud_rate = baud_rate  # Adjusted baud rate for FFT
        self.data_buffer = data_buffer

        self.freq = []
        self.fft_values = []

        # FFT window setup
        self.setWindowTitle("FFT Viewer")
        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.fft_line = self.plot.plot([], [], pen=pg.mkPen(color='w', width=1))
        

        # Sliders for range adjustment
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
        # Add sliders to the layout
        layout.addWidget(self.x_range_slider)
        layout.addWidget(self.y_range_slider)
        
        
        # Input boxes for direct control of the sliders
        self.x_range_input = QLineEdit()
        self.y_range_input = QLineEdit()
        self.x_range_input.setText(str(self.x_range_slider.value()))
        self.y_range_input.setText(str(self.y_range_slider.value()))
        # Update sliders when input changes
        self.x_range_input.textChanged.connect(self.update_x_range_from_input)
        self.y_range_input.textChanged.connect(self.update_y_range_from_input)
        # Add input boxes to the layout
        layout.addWidget(self.x_range_input)
        layout.addWidget(self.y_range_input)
        


        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_button)
        
        # Set the layout for the FFT window directly
        self.setLayout(layout)

        # Timer for FFT updates
        self.timer = QTimer()
        self.timer.setInterval(50)  # Adjust this interval to control the FFT window update speed
        self.timer.timeout.connect(self.update_fft_plot)
        self.timer.start()

    def update_fft_plot(self):
        """Update the FFT plot with new data."""
        if len(self.data_buffer) > 0:
            data = list(self.data_buffer)  # Get the latest data
            self.freq, self.fft_values = self.calculate_fft(data)
            self.fft_line.setData(self.freq, self.fft_values)  # Update the FFT plot

    def log_scaling(self, values):
        values = np.array(values)
        values = np.log1p(values)  # Add 1 to avoid log(0)
        return (values - np.min(values)) / (np.max(values) - np.min(values)) * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

    def min_max_scaling(self, values):
        values = np.array(values)
        min_val, max_val = np.min(values), np.max(values)
        return (values - min_val) / (max_val - min_val) * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

    def calculate_fft(self, data):
        """Calculate FFT of the data"""
        # Perform FFT and calculate frequency and values
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
            self.x_range_slider.setValue(self.x_range_slider.value())  # Set to current slider value if invalid input
            
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
            pass  # Invalid input, do nothing
    
    def toggle_pause(self):
        # Pause/resume the updates
        self.is_paused = not self.is_paused
    
            # Signal Filter Functions
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
