import numpy as np
import scipy.io.wavfile as wv
SAMP_RATE = 44100

def sine_wave(freq, time):
    t = np.linspace(0, time, time*SAMP_RATE)
    return np.sin(2*np.pi*freq*t)

def generate(N):
    frequencies = 2*np.logspace(1, 4, N)

    for freq in frequencies:
        values = sine_wave(freq, 10)
        wv.write("sine_%d_Hz.wav"%freq, SAMP_RATE, values)

generate(20)
