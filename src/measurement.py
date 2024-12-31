import math
import numpy as np
from scipy.signal import find_peaks

class Measurement:
    def __init__(self, data_buffer, sample_rate):
        if sample_rate <= 0:
            raise ValueError("Sample rate must be greater than zero.")
        
        self.data_buffer = list(data_buffer)
        self.sample_rate = sample_rate
        self.duration = len(data_buffer) / sample_rate
        self.t = np.linspace(0, self.duration, len(data_buffer))
    
    def max_frequcy(self, threshold=0.5):
        # Perform FFT
        N = len(self.data_buffer)  # Number of samples
        
        if 1/self.sample_rate == 0:
            raise ValueError("Sample rate must be greater than zero.")
        
        freqs = np.fft.fftfreq(N, 1 / self.sample_rate)
        fft_values = np.fft.fft(self.data_buffer)             # FFT computation
        fft_magnitudes = np.abs(fft_values[:N // 2])  # Magnitude (positive frequencies only)

        # Find peaks in the frequency domain
        average = np.mean(fft_magnitudes) * threshold
        peaks, _ = find_peaks(fft_magnitudes, height=average)  # Adjust 'height' as needed
        peak_freqs = freqs[peaks]
        
        return peak_freqs
    
    def peak_to_peak(self):
        return max(self.data_buffer) - min(self.data_buffer)
    
    def rms(self):
        return math.sqrt(np.mean(np.square(self.data_buffer)))
    
    def mean(self):
        return np.mean(self.data_buffer)
    
    def peak_to_rms(self):
        return self.peak_to_peak() / self.rms()
