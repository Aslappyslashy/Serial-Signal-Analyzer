# Serial-Signal-Analyzer
Vitualize and perform FFT, low pass, high pass filters, notch filters, and more on serial port signals. Connect to oscilloscope or even an arduino to gather information, and use this piece of code to help you get rid of noise, perform math to the signal.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aslappyslashy/IMG/refs/heads/main/signal%20analyzer/signal1.png" width="450" title="Signal Analyzer">
</p>

## FFT
The signal analyzer comes with a FFT window, it have only one function - to see the frequncy specturm.

<p align="center">
  <img src="https://raw.githubusercontent.com/Aslappyslashy/IMG/refs/heads/main/signal%20analyzer/fft.png" width="450" title="Signal Analyzer">
</p>

## Filters
There is three filters that can be used:
- 1. Low pass filters
  2. High pass filters
  3. notch filters

you can use them indivitually on the GUI or use them together by utilizing the ***code block***

<p align="center">
  <img src="https://github.com/Aslappyslashy/IMG/blob/main/signal%20analyzer/filter.png?raw=true" width="450" title="Filters">
</p>

## Code Block
The code block enables you to utilize multiple filters at a time, it can be coded as:
- 'lp' low pass filter
-   - cut off frequncy
    - e.g. 'lp:300'
- 'hp' low pass filter
-   - cut off frequncy
    - e.g. 'hp:100'
- 'n' notch filter
-   - nyquist
    - Q factor
    - e.g. 'lp:50,1'
 
Multiple filters can be seperated by ';', for example: 'lp:500;n:50,1' is the low pass filter follow by a notch filter at 50Hz.

## Extra
The code is not complete, you should be able to run this by just excuting the 'main.py', remember to change the baudrate and the port in the 'main.py'.
