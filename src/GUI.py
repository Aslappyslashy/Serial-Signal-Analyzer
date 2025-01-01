import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
import sys
import random
from collections import deque
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QCheckBox, QHBoxLayout, QFrame, QLabel, QSlider
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QDoubleValidator  
from PyQt6.QtWidgets import QComboBox  
import pyqtgraph as pg
import numpy as np
import time
import scipy.signal as signal
from scipy.signal import find_peaks
import math

g_highpass = []
g_lowpass = []
g_notch = []
g_code = []

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
        global g_highpass
        global g_lowpass
        global g_notch
        global g_code
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
                g_lowpass = lowpass_data
                self.lowpass_line.setData(x, lowpass_data)
            else:
                self.lowpass_line.clear()

            if self.checkbox_highpass.isChecked():
                highpass_data = self.highpass_filter(data)
                g_highpass = highpass_data
                self.highpass_line.setData(x, highpass_data)
            else:
                self.highpass_line.clear()

            if self.checkbox_notch.isChecked():
                notch_data = self.notch_filter(data)
                g_notch = notch_data
                self.notch_line.setData(x, notch_data)
            else:
                self.notch_line.clear()

            if self.checkbox_code.isChecked():
                code_data = self.apply_custom_filters(data)
                g_code = code_data
                #print("g_code:",g_code)
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
            #print(f"Low-pass filter error: {e}")
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
            #print(f"High-pass filter error: {e}")
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
            #print(f"Notch filter error: {e}")
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
            if cmd_d[0] == 'hp':  # High-pass filter
                try:
                    cutoff = int(cmd_d[1])
                    nyquist = 0.5 * self.baud_rate
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(4, normalized_cutoff, btype='high')
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    #print("Invalid highpass filter command. Format: hp:<cutoff_frequency>")
                    pass
            elif cmd_d[0] == 'lp':  # Low-pass filter
                try:
                    cutoff = int(cmd_d[1])
                    nyquist = 0.5 * self.baud_rate
                    normalized_cutoff = cutoff / nyquist
                    b, a = signal.butter(4, normalized_cutoff, btype='low')
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    #print("Invalid lowpass filter command. Format: lp:<cutoff_frequency>")
                    pass
            elif cmd_d[0] == 'n':  # Notch filter
                try:
                    cmd_d_d = cmd_d[1].split(',')
                    freq = float(cmd_d_d[0])
                    nyquist = 0.5 * self.baud_rate
                    Q = int(cmd_d_d[1])
                    b, a = signal.iirnotch(freq / nyquist, Q)
                    data = signal.filtfilt(b, a, data)
                except (ValueError, IndexError):
                    #print("Invalid notch filter command. Format: n:<frequency>,<Q-factor>")
                    pass
            else:
                print(f"Unknown command: {cmd_d[0]}. Use 'hp', 'lp', or 'n'.")
            #print(i)
            #i+=1
        return data




class FFTWindow(QtWidgets.QWidget):
    def __init__(self, data_buffer, sample_rate, x_range=(0, 5000), x_res=1, y_range=(0, 20), y_res=1, fps=30, maxlen=4096):
        super().__init__()
        self.data_buffers = {
            "Original": deque(maxlen=maxlen),
            "Highpass": deque(maxlen=maxlen),
            "Lowpass": deque(maxlen=maxlen),
            "Notch": deque(maxlen=maxlen),
            "Code": deque(maxlen=maxlen),
        }
        self.data_buffer = data_buffer
        self.data_buffers["Original"].extend(data_buffer)
        self.data_buffers["Highpass"].extend(g_highpass)
        self.data_buffers["Lowpass"].extend(g_lowpass)
        self.data_buffers["Notch"].extend(g_notch)
        self.data_buffers["Code"].extend(g_code)
        
        self.sample_rate = sample_rate
        self.x_range = x_range
        self.y_range = y_range
        self.fps = fps
        self.is_paused = False
        self.x_res = x_res
        self.y_res = y_res
        self.active_lines = {}

        # main layout
        main_layout = QHBoxLayout()
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('k')
        self.plot_graph.showGrid(x=True, y=True)

        main_layout.addWidget(self.plot_graph, stretch=3)

        # controls layout
        controls_layout = QVBoxLayout()
        self.create_checkboxes(controls_layout)
        self.create_x_axis_controls(controls_layout)
        self.create_y_axis_controls(controls_layout)

        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button)

        
        main_layout.addLayout(controls_layout, stretch=1)
        self.setLayout(main_layout)

        
        self.timer = QTimer()
        self.timer.setInterval(int((1 / self.fps) * 1000))
        self.timer.timeout.connect(self.update_fft_plot)
        self.timer.start()

    def create_checkboxes(self, layout):
        """Create checkboxes for selecting which data to display."""
        layout.addWidget(QLabel("Select Data Sources:"))

        self.checkboxes = {}
        self.colors = {'Original': 'w', 'Highpass': 'r', 'Lowpass': 'b', 'Notch': 'g', 'Code': 'y'}

        for key, color in self.colors.items():
            checkbox = QCheckBox(f"{key} Data")
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.toggle_line_visibility)
            layout.addWidget(checkbox)
            self.checkboxes[key] = checkbox

    def toggle_line_visibility(self):
        """Toggle the visibility of a data source line."""
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                if key not in self.active_lines:
                    
                    self.active_lines[key] = self.plot_graph.plot([], [], pen=pg.mkPen(color=self.colors[key], width=1))
            else:
                if key in self.active_lines:
                    
                    self.plot_graph.removeItem(self.active_lines[key])
                    del self.active_lines[key]

    def update_fft_plot(self):
        """Update the FFT plot for all active data sources."""
        self.data_buffers["Original"].extend(self.data_buffer)
        self.data_buffers["Highpass"].extend(g_highpass)
        self.data_buffers["Lowpass"].extend(g_lowpass)
        self.data_buffers["Notch"].extend(g_notch)
        self.data_buffers["Code"].extend(g_code)
        
        if self.is_paused:
            return

        for key, line in self.active_lines.items():
            if key in self.data_buffers:
                data = list(self.data_buffers[key]) 
                if len(data) > 0:
                    freqs, fft_values = self.calculate_fft(data)
                    line.setData(freqs, fft_values)
        '''
        for key, buffer in self.data_buffers.items():
            print(f"{key}: {list(buffer)}")
        '''
    def calculate_fft(self, data):
        """Calculate FFT of the data."""
        fft_values = np.abs(np.fft.fft(data))
        freqs = np.fft.fftfreq(len(data), d=1 / self.sample_rate)
        return freqs, self.min_max_scaling(fft_values)

    def min_max_scaling(self, values):
        """Scale FFT values to fit Y-axis range."""
        values = np.array(values)
        min_val, max_val = np.min(values), np.max(values)
        if max_val - min_val == 0:  # avoid division by zero
            return values
        return (values - min_val) / (max_val - min_val) * (self.y_range[1] - self.y_range[0]) + self.y_range[0]

    def create_x_axis_controls(self, layout):
        """Create controls for adjusting the X-axis."""
        layout.addWidget(QLabel("X-Axis Range:"))
        x_range_layout = QHBoxLayout()
        self.x_range_slider = QSlider(Qt.Orientation.Horizontal)
        self.x_range_slider.setRange(self.x_range[0], self.x_range[1])
        self.x_range_slider.setValue(100)
        self.x_range_slider.setTickInterval(self.x_res)
        self.x_range_slider.valueChanged.connect(self.update_x_range)
        x_range_layout.addWidget(self.x_range_slider)

        self.x_range_input = QLineEdit(str(self.x_range_slider.value()))
        self.x_range_input.textChanged.connect(self.update_x_range_from_input)
        x_range_layout.addWidget(self.x_range_input)
        layout.addLayout(x_range_layout)

    def create_y_axis_controls(self, layout):
        """Create controls for adjusting the Y-axis."""
        layout.addWidget(QLabel("Y-Axis Range:"))
        y_range_layout = QHBoxLayout()
        self.y_range_slider = QSlider(Qt.Orientation.Horizontal)
        self.y_range_slider.setRange(self.y_range[0], self.y_range[1])
        self.y_range_slider.setValue(0)
        self.y_range_slider.setTickInterval(self.y_res)
        self.y_range_slider.valueChanged.connect(self.update_y_range)
        y_range_layout.addWidget(self.y_range_slider)

        self.y_range_input = QLineEdit(str(self.y_range_slider.value()))
        self.y_range_input.textChanged.connect(self.update_y_range_from_input)
        y_range_layout.addWidget(self.y_range_input)
        layout.addLayout(y_range_layout)

    def update_x_range(self):
        """Update the X-axis range."""
        x_range_value = self.x_range_slider.value()
        self.plot_graph.setXRange(0, x_range_value)
        self.x_range_input.setText(str(x_range_value))

    def update_x_range_from_input(self):
        """Update the X-axis range from input."""
        try:
            new_value = int(self.x_range_input.text())
            if self.x_range[0] <= new_value <= self.x_range[1]:
                self.x_range_slider.setValue(new_value)
        except ValueError:
            pass

    def update_y_range(self):
        """Update the Y-axis range."""
        y_min = -self.y_range_slider.value()
        y_max = self.y_range_slider.value()
        self.plot_graph.setYRange(y_min, y_max)
        self.y_range_input.setText(str(y_min))

    def update_y_range_from_input(self):
        """Update the Y-axis range from input."""
        try:
            new_value = int(self.y_range_input.text())
            if self.y_range[0] <= new_value <= self.y_range[1]:
                self.y_range_slider.setValue(new_value)
        except ValueError:
            pass

    def toggle_pause(self):
        """Pause or resume the FFT plot updates."""
        self.is_paused = not self.is_paused



class Measurement_Window(QtWidgets.QWidget):
    def __init__(self, data_buffer, sample_rate=1000, fps=30):
        super().__init__()

        global g_highpass
        global g_lowpass
        global g_notch
        global g_code
        self.data_buffer = data_buffer
        data_buffers = {
            "Original": data_buffer,
            "Highpass": g_highpass,
            "Lowpass": g_lowpass,
            "Notch": g_notch,
            "Code": g_code,
        }
        self.data_buffers = data_buffers   
        #self.data_buffers["Original"].extend(self.data_buffer)
        self.data_buffers["Highpass"].extend(g_highpass)
        self.data_buffers["Lowpass"].extend(g_lowpass)
        self.data_buffers["Notch"].extend(g_notch)
        self.data_buffers["Code"].extend(g_code)
         
        self.sample_rate = sample_rate
        self.fps = fps
        self.active_data_source = "Original" 
        
        self.duration = len(data_buffers["Original"]) / sample_rate if sample_rate > 0 else 0
        self.t = np.linspace(0, self.duration, len(data_buffers["Original"]))

        
        main_layout = QVBoxLayout()
        self.setWindowTitle("Measurement Values")

        
        self.plot = pg.PlotWidget()
        main_layout.addWidget(self.plot)

        # labels for measurements
        self.freq_label = QLabel("Frequencies:")
        self.freq_value_label = QLabel("")
        self.peak_to_peak_label = QLabel("Peak-to-Peak:")
        self.peak_to_peak_value_label = QLabel("")
        self.rms_label = QLabel("RMS:")
        self.rms_value_label = QLabel("")
        self.mean_label = QLabel("Mean:")
        self.mean_value_label = QLabel("")
        self.peak_to_rms_label = QLabel("Peak-to-RMS:")
        self.peak_to_rms_value_label = QLabel("")

        labels_layout = QVBoxLayout()
        for label, value_label in [
            (self.freq_label, self.freq_value_label),
            (self.peak_to_peak_label, self.peak_to_peak_value_label),
            (self.rms_label, self.rms_value_label),
            (self.mean_label, self.mean_value_label),
            (self.peak_to_rms_label, self.peak_to_rms_value_label),
        ]:
            labels_layout.addWidget(label)
            labels_layout.addWidget(value_label)

        # controls layout
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(QLabel("Select Data Source:"))
        self.checkboxes = {}
        self.colors = {'Original': 'w', 'Highpass': 'r', 'Lowpass': 'b', 'Notch': 'g', 'Code': 'y'}

        for key in self.data_buffers.keys():
            checkbox = QCheckBox(f"{key} Data")
            checkbox.setChecked(key == self.active_data_source)
            checkbox.stateChanged.connect(self.update_active_data_source)
            controls_layout.addWidget(checkbox)
            self.checkboxes[key] = checkbox

        
        combined_layout = QHBoxLayout()
        combined_layout.addLayout(labels_layout, stretch=3)
        combined_layout.addLayout(controls_layout, stretch=1)

        main_layout.addLayout(combined_layout)
        self.setLayout(main_layout)

        
        self.plot_curve = self.plot.plot(pen="y")

        
        self.timer = QTimer()
        self.timer.setInterval(int((1 / self.fps) * 1000))
        self.timer.timeout.connect(self.update_measurement)
        self.timer.start()

    def update_active_data_source(self):
        """Update the active data source based on checkbox selection."""
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                self.active_data_source = key
                break
    
    def maintain_length(self, buffer, reference_length):
        if len(buffer) > reference_length:
            del buffer[:-reference_length]  



    def update_measurement(self):
        """Update measurements for the active data source."""
        
        reference_length = len(self.data_buffers["Original"])

        self.data_buffers["Highpass"].extend(g_highpass)
        self.maintain_length(self.data_buffers["Highpass"], reference_length)

        self.data_buffers["Lowpass"].extend(g_lowpass)
        self.maintain_length(self.data_buffers["Lowpass"], reference_length)

        self.data_buffers["Notch"].extend(g_notch)
        self.maintain_length(self.data_buffers["Notch"], reference_length)

        self.data_buffers["Code"].extend(g_code)
        self.maintain_length(self.data_buffers["Code"], reference_length)
        
        
        data = self.data_buffers.get(self.active_data_source, [])
        if len(data) > 0:
            
            self.plot_curve.setData(data)

            max_frequencies = self.max_frequency(data)  
            self.freq_value_label.setText(", ".join([f"{f:.2f}" for f in max_frequencies]))
            self.peak_to_peak_value_label.setText(f"{self.peak_to_peak(data):.2f}")
            self.rms_value_label.setText(f"{self.rms(data):.2f}")
            self.mean_value_label.setText(f"{self.mean(data):.2f}")
            self.peak_to_rms_value_label.setText(f"{self.peak_to_rms(data):.2f}")
        else:
            # clear labels if no data to avoid max freq blow up
            self.freq_value_label.setText("")
            self.peak_to_peak_value_label.setText("")
            self.rms_value_label.setText("")
            self.mean_value_label.setText("")
            self.peak_to_rms_value_label.setText("")


    def max_frequency(self, data, threshold=1.5):
        N = len(data)
        if N == 0 or self.sample_rate <= 0:
            return []

        freqs = np.fft.fftfreq(N, 1 / self.sample_rate)
        fft_values = np.fft.fft(data)
        fft_magnitudes = np.abs(fft_values[:N // 2])

        average = np.mean(fft_magnitudes) * threshold
        peaks, _ = find_peaks(fft_magnitudes, height=average)
        peak_freqs = freqs[peaks]
        return peak_freqs

    def peak_to_peak(self, data):
        return max(data) - min(data)

    def rms(self, data):
        return np.sqrt(np.mean(np.square(data)))

    def mean(self, data):
        return np.mean(data)

    def peak_to_rms(self, data):
        rms_value = self.rms(data)
        return self.peak_to_peak(data) / rms_value if rms_value > 0 else 0
