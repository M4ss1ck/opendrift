#!/usr/bin/env python
"""
Example script to demonstrate the MicroplasticDrift model.
This example simulates the drift of different types of microplastic particles
from a single release point in the Norwegian Sea.
"""

import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from opendrift.models.microplastics import MicroplasticDrift
from opendrift.readers import reader_netCDF_CF_generic


# Create a new simulation object
o = MicroplasticDrift(loglevel=20)  # 20=info

# Print configuration settings
o.list_configspec()

# Fetch currents and wind data from thredds server
reader_current = reader_netCDF_CF_generic.Reader('https://thredds.met.no/thredds/dodsC/cmems/topaz6/dataset-topaz6-arc-15min-3km-be')
reader_wind = reader_netCDF_CF_generic.Reader('https://thredds.met.no/thredds/dodsC/cmems/topaz6/dataset-topaz6-arc-1h-3km-be')

o.add_reader([reader_current, reader_wind])
print(o)

# Set up configuration
o.set_config('vertical_mixing:diffusivitymodel', 'environment')  # Use profiles from ocean model
o.set_config('drift:vertical_mixing', True)
o.set_config('drift:vertical_advection', True)
o.set_config('microplastic:biofouling_rate', 0.05)  # Biofouling rate of 5% per day
o.set_config('microplastic:degradation_rate', 0.01)  # Degradation rate of 1% per day
o.set_config('general:coastline_action', 'stranding')
o.set_config('microplastic:coastline_interaction', 'partial_stranding')  # Some particles may strand at coastlines

# Seed particles: different types of microplastics
# Coordinates and time for seeding
lon = 4.0  # Central Norwegian Sea
lat = 62.0
time = datetime.now()

# 3 types of microplastics:
# 1. Low-density polyethylene particles (LDPE, density 920 kg/m3)
o.seed_elements(lon=lon, lat=lat, number=200,
                density=920, diameter=1.0, shape_factor=1.0,
                time=time)

# 2. Polystyrene particles (PS, density 1050 kg/m3)
o.seed_elements(lon=lon+0.05, lat=lat+0.05, number=200,
                density=1050, diameter=1.0, shape_factor=1.0,
                time=time)

# 3. Polyethylene terephthalate particles (PET, density 1380 kg/m3)
o.seed_elements(lon=lon-0.05, lat=lat-0.05, number=200,
                density=1380, diameter=1.0, shape_factor=1.0,
                time=time)

# Run simulation
o.run(duration=timedelta(days=10),
      time_step=1800,  # 30 minutes
      time_step_output=3600,  # 1 hour
      outfile='microplastics_simulation.nc')

# Print final status of particles
print(o)

# Create plots
o.plot(fast=False)  # Basic plot

# Plot trajectories by plastic type (based on density)
o.plot(fast=False, key='density', colorbar=True,
       title='Microplastic transport - colored by density')

# Vertical distribution over time
o.animation_profile()

# Vertical distribution at end
o.plot_property('z', mean=True)

# Plot biofouling level at end
o.plot(key='biofouling_level', colorbar=True,
       title='Biofouling level after simulation')

# Plot degradation state at end
o.plot(key='degradation_state', colorbar=True,
       title='Degradation state after simulation')

# Now show the plots
plt.show() 