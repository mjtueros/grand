"""! Signal processing

- This module contains several signal processing
functionalities to be applied to simulation/data
- operations are meant to be on the signal traces 
for individual antennas, suitable to be used both
in Grandlib format/ read from hdf5 files
- expects signal traces to be of the size (3,lengthoftrace)
"""

from logging import getLogger

import numpy as np
from scipy.signal import hilbert, resample, decimate, butter, lfilter

logger = getLogger(__name__)


def get_filter(time, trace, fr_min, fr_max):
    """!Filter signal  in given bandwidth
    @note
      At present Butterworth filter only is implemented, others: what
      is close to hardware filter?

    @param time (array): [ns] time
    @param trace (array): ElectricField (muV/m)/voltage (muV) vectors to be filtered
    @param fr_min (float): [Hz] The minimal frequency of the bandpass filter
    @param fr_max (float): [Hz] The maximal frequency of the bandpass filter

    @returns: filtered trace in time domain
    """
    tstep = (time[1] - time[0]) * 1e-09  # s
    rate = 1 / tstep
    nyq = 0.5 * rate  # Nyquist limit
    low = fr_min / nyq
    high = fr_max / nyq
    order = 5
    coeff_b, coeff_a = butter(order, [low, high], btype="band")
    filtered = lfilter(coeff_b, coeff_a, trace)  # this is data in the time domain
    return filtered


def get_fft(time, trace, specialwindow=False):
    """!Compute the one-dimensional discrete Fourier Transform for real input
    @note
      - numpy rfft pack calculates only positive frequency parts exploiting Hermitian-Symmetry,
        the returned array is complex and of length N/2+1
      - for plotting purposes taking  abs(fft trace) is required
      - for now a hamming window is used, special windows help with subtle effects like signal
        leakage,might be more important when used on measured data

    @param time (array): [ns] time
    @param trace (array) : ElectricField (muV/m)/voltage (muV) vectors to be filtered, could be raw or
      filtered
    @param specialwindow (bool): if true implements a hamming window

    @returns (array): [Mhz]frequency , fft trace(complex)
    """
    dlength = trace.shape[1]  # length of  the trace
    tstep = (time[1] - time[0]) * 1e-9  # time step in sec
    freq = np.fft.rfftfreq(dlength, tstep) / 1e06  # MHz
    if not specialwindow:
        trace_fft = np.fft.rfft(trace)
    else:
        logger.debug("performing a hamming window on the signal ...")
        hammingwindow = np.hamming(dlength)
        trace_fft = np.fft.rfft(trace * hammingwindow)
    return freq, trace_fft


def get_inverse_fft(trace):
    """!Computes the inverse of rfft

    @param trace (array): signal trace same as in get_fft

    @return (array): inverse fft (time domain)
    """
    inv_fft = np.fft.irfft(trace, n=trace.shape[1])
    return inv_fft


def get_peakamptime_hilbert(time, trace, f_min, f_max, filtered=False):
    """!Get Peak and time of EField trace, either filtered or unfiltered

    @param time (array): time
    @param trace (array): ElectricField (muV/m) vectors to be filtered- expected
      size (3,dlength), dlength= size of the signal trace
    @param f_min (float): [Hz] The minimal frequency of the bandpass filter
    @param f_max (float): [Hz] The maximal frequency of the bandpass filter
    @param filtered (bool): if true filtering is applied else raw input trace is used

    @return TBD
    """
    if filtered:
        logger.debug("filtering the signal .....")
        filt = get_filter(time, trace, f_min, f_max)
    else:
        logger.debug("continuing with raw signal ...")
        filt = trace

    hilbert_amp = np.abs(hilbert(filt, axis=-1))
    peakamp = max([max(hilbert_amp[0]), max(hilbert_amp[1]), max(hilbert_amp[2])])
    peaktime = time[np.argwhere(hilbert_amp == peakamp)[0][1]]

    return peaktime, peakamp


def digitize_signal(time, trace, tsampling, downsamplingmethod=1):

    """!Performs digitization/resampling of signal trace for a given sampling rate
    @note
      There are several ways of resampling- scipy.resample seems most
      common for up/down sampling, an extra method is also added for
      downsampling-scipy.decimate - this seems to use antialiasing filter.
      these methods might change in future.

    @param time (array): [ns] time trace
    @param trace (array):  signal trace - efield(meuV/m)/Voltage(meuV/m)
    @param tsampling (integer/float): [ns] desired sampling rate in time
    @param downsamplingmethod (integer):  1 for scipy.resample, 2.scipy.decimate
    @return resampled signal and time trace
    """

    tstep = time[1] - time[0]  # ns
    samplingrate = tsampling / tstep
    dlength = trace.shape[1]

    if samplingrate < 1:
        logger.debug("performing umsampling ...")
        resampled = [resample(x, round(1 / samplingrate) * dlength) for x in trace]
        time_resampled = np.linspace(time[0], time[-1], len(resampled[0]), endpoint=False)
    else:
        if downsamplingmethod == 1:
            logger.debug("performing downsampling method 1 ...")
            resampled = [resample(x, dlength / round(samplingrate)) for x in trace]

        elif downsamplingmethod == 2:
            logger.debug("performing downsampling with method 2 ...")
            resampled = [decimate(x, round(samplingrate)) for x in trace]
        else:
            raise ValueError("choose a valid method number")
        time_resampled = np.linspace(time[0], time[-1], len(resampled[0]), endpoint=False)
    resampled = np.array(resampled).reshape(3, len(resampled[0]))

    return resampled, time_resampled


def add_noise(trace, vrms):
    """!Add normal random noise on traces

    @todo
      Later should be modified to add measured noise

    @param trace (array): voltage trace
    @param vrms (float): noise rms, e.g vrmsnoise= 15 meu-V

    @return (array): noisy voltage trace
    """

    noise = np.random.normal(0, vrms, size=trace.shape[1])
    noisy_traces = np.add(trace, noise)

    return noisy_traces
