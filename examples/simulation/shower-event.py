#! /usr/bin/env python3

import os.path as osp


import numpy as np
from matplotlib import pyplot as plt
from grand import (
    ECEF,
    Geodetic,
    LTP,
    GRANDCS,
    SphericalRepresentation,
    CartesianRepresentation,
    GRAND_DATA_PATH,
    get_root_grand_git,
)


from grand.simulation import Antenna, ShowerEvent, TabulatedAntennaModel
import grand.manage_log as mlg

# define a handler for logger : standart output and file log.txt
mlg.create_output_for_logger("debug", log_file="log.txt", log_stdout=True)

# specific logger definition for script because __mane__ is "__main__"
logger = mlg.get_logger_for_script(__file__)
logger.info(mlg.string_begin_script())

# Load the radio shower simulation data
showerdir = osp.join(get_root_grand_git(), "tests/simulation/data/zhaires")
shower = ShowerEvent.load(showerdir)

if shower.frame is None:
    shower.localize(39.5, 90.5)  # Coreas showers have no
    # localization info. This must
    # be set manually
print("---------------------------------")
print("Zenith (Zhaires?!) =", shower.zenith)
print("Azimuth (Zhaires?!) =", shower.azimuth)
print("Xmax=", shower.maximum.flatten())
print("Core=", shower.core.flatten())
print("obstime=", shower.frame.obstime, "\n")
print(vars(shower.frame), "Shower frame")
print("---------------------------------", "\n")

# Define an antenna model
#
# A tabulated model of the Butterfly antenna is used. Note that a single EW
# arm is assumed here for the sake of simplicity
path_ant = osp.join(GRAND_DATA_PATH, "HorizonAntenna_EWarm_leff_loaded.npy")
antenna_model = TabulatedAntennaModel.load(path_ant)

counter = 0
# Loop over electric fields and compute the corresponding voltages
for antenna_index, field in shower.fields.items():
    counter += 1
    if counter == 2:
        break

    # Compute the antenna local frame
    #
    # The antenna is placed within the shower frame. It is oriented along the
    # local magnetic North by using an ENU/LTP frame (x: East, y: North, z: Upward)
    antpos_wrt_shower = (
        field.electric.r
    )  # RK: if antenna location was saved in LTP frame in zhaires.py, next step would not required.
    antenna_location = LTP(
        x=antpos_wrt_shower.x,
        y=antpos_wrt_shower.y,
        z=antpos_wrt_shower.z,
        frame=shower.frame,
    )
    antenna_frame = LTP(
        location=antenna_location,
        orientation="NWU",
        magnetic=True,
        obstime=shower.frame.obstime,
    )
    antenna = Antenna(model=antenna_model, frame=antenna_frame)

    print(antenna_index, "Antenna pos in shower frame", antpos_wrt_shower.flatten())
    print(
        vars(antenna_location),
        antenna_location.flatten(),
        "antenna pos LTP in shower frame",
    )
    print("---------------------------------", "\n")
    print(vars(antenna_frame), "antenna frame")
    print("---------------------------------", "\n")

    # Compute the voltage on the antenna
    #
    # The electric field is assumed to be a plane-wave originating from the
    # shower axis at the depth of maximum development. Note that the direction
    # of observation and the electric field components are provided in the
    # shower frame. This is indicated by the `frame` named argument.
    Exyz = field.electric.E

    logger.info(mlg.chrono_start())
    # Xmax, Efield, and input frame are all in shower frame.
    field.voltage = antenna.compute_voltage(shower.maximum, field.electric, frame=shower.frame)

    logger.info(mlg.chrono_string_duration())

    print("\nVpp=", max(field.voltage.V) - min(field.voltage.V), "\n")

    plt.figure()
    plt.subplot(211)
    plt.plot(field.electric.t, Exyz.x, label="Ex")
    plt.plot(field.electric.t, Exyz.y, label="Ey")
    plt.plot(field.electric.t, Exyz.z, label="Ez")
    plt.xlabel("Time (ns)")
    plt.ylabel(r"Efield ($\mu$V/m)")
    plt.legend(loc="best")
    plt.subplot(212)
    plt.plot(field.voltage.t, field.voltage.V, label="V$_{EW}$")
    plt.xlabel("Time (ns)")
    plt.ylabel(r"Voltage ($\mu$V)")
    plt.legend(loc="best")

logger.info(mlg.string_end_script())
plt.show()
