#
#  gmsk.py
#
#  Copyright The GRS Demodulator Contributors.
#
#  This file is part of GRS Demodulator.
#
#  GRS Demodulator is free software; you can redistribute it
#  and/or modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  GRS Demodulator is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with GRS Demodulator; if not, see <http://www.gnu.org/licenses/>.
#
#

import numpy as np
from scipy.signal import upfirdn, lfilter, butter
from .timing_sync.timing_sync import TimeSync

_GMSK_DEFAULT_OVERSAMPLING_FACTOR = 100

class GMSK:
    """
    GMSK modulator.
    """
    def __init__(self, bt, baud):
        """
        Constructor.

        :param bt: BT product (bandwidth x bit period) for GMSK
        :param baud: The desired data rate in bps
        """
        self._bt = bt
        self._baudrate = baud

    def modulate(self, data, L=_GMSK_DEFAULT_OVERSAMPLING_FACTOR):
        """
        Function to modulate an integer stream using GMSK modulation.

        :param data: input integer list to modulate (bytes as integers)
        :param L: oversampling factor

        :return: s_complex: baseband GMSK signal (I+jQ)
        :return: samp: Sample rate S/s
        :return: dur: Signal duration in seconds
        """
        I, Q, fs, dur = self.get_iq(data, L)
        s_complex = I + 1j*Q    # Complex baseband representation

        return s_complex, fs, dur

    def get_iq(self, data, L=_GMSK_DEFAULT_OVERSAMPLING_FACTOR):
        """
        Computes the IQ data of the GMSK modulated signal.

        :param data: input integer list to modulate (bytes as integers)
        :param L: oversampling factor

        :return: I: I data of the modulated signal
        :return: Q: Q data of the modulated signal
        :return: samp: Sample rate S/s
        :return: dur: Signal duration in seconds
        """
        # Convert to array of bits
        data = self._int_list_to_bit_list(data)

        data = np.array(data)

        # Timing parameters
        fc = self._baudrate                         # Carrier frequency = Data transfer rate in bps
        fs = L*fc                                   # Sample frequency in Hz
        Ts = np.float64(1.0)/fs                     # Sample period in seconds
        Tb = L*Ts                                   # Bit period in seconds

        c_t = upfirdn(h=[1]*L, x=2*data-1, up = L)  # NRZ pulse train c(t)
        k = 1                                       # Truncation length for Gaussian LPF
        h_t = self._gaussian_lpf(Tb, L, k)          # Gaussian LPF
        b_t = np.convolve(h_t, c_t, 'full')         # Convolve c(t) with Gaussian LPF to get b(t)
        bnorm_t = b_t/np.max(np.abs(b_t))           # Normalize the output of Gaussian LPF to +/-1

        # Integrate to get phase information
        h = np.float64(0.5)                         # Modulation index (GMSK = 0.5)
        phi_t = lfilter(b = [1], a=[1,-1], x=bnorm_t*Ts) * h*np.pi/Tb
        I = np.cos(phi_t)
        Q = np.sin(phi_t)                           # Cross-correlated baseband I/Q signals

        # Sampling values
        dur = len(data)*Tb                          # Transmission duration in seconds

        return I, Q, fs, dur

    def modulate_time_domain(self, data, L=_GMSK_DEFAULT_OVERSAMPLING_FACTOR):
        """
        Generates the GMSK modulated signal in time domain.

        :param data: input integer list to modulate (bytes as integers)
        :param L: oversampling factor

        :return: s_t: GMSK modulated signal with carrier s(t) (time domain)
        :return: samp: Sample rate S/s
        :return: dur: Signal duration in seconds
        """
        I, Q, samp, dur = self.get_iq(data, L)

        fc = self._baudrate                         # Carrier frequency = Data transfer rate in bps
        fs = L*fc
        Ts = 1/fs

        t = Ts*np.arange(start=0, stop=len(I))      # Time base for RF carrier
        sI_t = I*np.cos(2*np.pi*fc*t)
        sQ_t = Q*np.sin(2*np.pi*fc*t)
        s_t = sI_t - sQ_t                           # s(t) - GMSK with RF carrier

        return s_t, t, samp, dur

    def _gaussian_lpf(self, Tb, L, k):
        """
        Generate filter coefficients of Gaussian low pass filter (used in gmsk_mod).

        :param Tb: bit period
        :param L: oversampling factor (number of samples per bit)
        :param k: span length of the pulse (bit interval)

        :return h_norm: normalized filter coefficients of Gaussian LPF
        """
        B = self._bt/Tb     # Bandwidth of the filter
        # Truncated time limits for the filter
        t = np.arange(start = -k*Tb, stop = k*Tb + Tb/L, step = Tb/L)
        h = B*np.sqrt(2*np.pi/(np.log(2)))*np.exp(-2 * (t*np.pi*B)**2 /(np.log(2)))
        h_norm = h / np.sum(h)
        return h_norm
    
    def _low_pass_filter(self, iq_samples, fs, cutoff):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        
        # 5th order Butterworth filter
        b, a = butter(5, normal_cutoff, btype='low', analog=False)
        
        # Apply filter to the complex samples
        return lfilter(b, a, iq_samples)

    def _int_list_to_bit_list(self, n):
        """
        Converts a integer list (bytes) to a bit list.

        :param n: An integer list.

        :return res: The given integer list as a bit list
        """
        res = list()
        
        for i in n:
            res = res + [int(digit) for digit in bin(i)[2:].zfill(8)]

        return res

    def demodulate(self, fs, iq_samples):
        """
        Perform GMSK demodulation.

        :param fs: TODO
        :param iq_samples: TODO

        :return res: TODO
        """
        sps = int(fs/self._baudrate)
        
        # Apply low pass filter
        cutoff_freq = 1.5 * self._baudrate
        low_pass_iq = self._low_pass_filter(iq_samples, fs, cutoff_freq)

        # Frequency discriminator
        freq_deviation = self._frequency_discriminator(low_pass_iq)

        # Apply Gaussian matched filter
        gaussian_filter = self._gaussian_filter(sps, span = 1, bt = 2)
        filtered_signal = np.convolve(freq_deviation, gaussian_filter, mode='same')

        # Normalization
        filtered_signal = self._normalize(filtered_signal)
        
        # Timing recovery
        time_sync = TimeSync(samp_rate=fs, baud=self._baudrate)
        soft_symbols = np.array(time_sync.get_bitstream(filtered_signal))
                
        # Decision thresholding
        demod_bits = (soft_symbols > 0).astype(int)
        
        return list(demod_bits), soft_symbols, filtered_signal

    def _frequency_discriminator(self, iq_samples):
        """
        Extract frequency deviations using phase changes in IQ samples.

        :param iq_samples: TODO

        :return res: TODO
        """
        phase = np.angle(iq_samples)                    # Extract phase
        unwrapped_phase = np.unwrap(phase)              # Unwrap to avoid phase discontinuities
        freq_deviation = np.diff(unwrapped_phase)       # Phase derivative

        return np.concatenate([[0], freq_deviation])    # Keep length consistent

    def _gaussian_filter(self, sps, span, bt):
        """
        Generate a Gaussian matched filter.

        :param span: TODO

        :return res: TODO
        """
        _bt = self._bt if bt is None else bt
        
        t = np.arange(-span*sps, span*sps + 1)
        alpha = (2 * np.pi * _bt) / (np.sqrt(np.log(2)) * sps)        
        h = np.exp(-0.5 * (alpha * t) ** 2)
        return h / np.sum(h)
    
    def _bit_list_to_int_list(self, b):
        """
        Converts a list of bits to a list of integers (bytes)
        
        :param b: The list of bits
        :return res: The list of integers for the given list of bits
        """
    
        return [int("".join(map(str, b[i:i+8])), 2) for i in range(0, len(b), 8)]
    
    def _normalize(self, x):
        """
        Normalizes sample
        """
        x = x - np.mean(x)
        s = np.std(x)
        if s != 0:
            return x/s
        return x
    
    def _remove_matched_filter_delay(self, x, sps, span):
        """
        Removes group delay introduced by the Gaussian matched filter.
        """
        delay = span * sps
        if len(x) <= 2 * delay:
            return x
        return x[delay:-delay]


    
