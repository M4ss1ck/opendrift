# MicroplasticDrift Model for OpenDrift

This module simulates the drift and behavior of microplastic particles in the marine environment. It extends the OceanDrift model with specific properties and processes relevant to microplastic transport.

## Features

The MicroplasticDrift model includes:

- Simulation of different types of microplastics based on material density
- Variable particle sizes and shapes
- Biofouling processes (which increase effective density over time)
- Degradation processes (affecting particle size and properties)
- Specific interactions with coastlines (stranding behavior)
- Resuspension from seafloor
- Vertical positioning based on buoyancy (calculated using Stokes' Law)

## Microplastic Properties

Each microplastic particle has the following properties:

- `diameter`: Size of the particle in mm
- `density`: Material density in kg/m³
- `shape_factor`: Affects drag coefficient (1.0 for spherical particles)
- `biofouling_level`: Biofouling level (0-1) affecting buoyancy
- `degradation_state`: Degradation state (0-1) affecting size and properties

## Configuration Options

The model provides several configuration options:

### Seeding Configuration

- `seed:diameter`: Default diameter of seeded particles (mm)
- `seed:density`: Default density of seeded particles (kg/m³)
- `seed:shape_factor`: Default shape factor of seeded particles

### Process Configuration

- `microplastic:biofouling_rate`: Daily rate of biofouling increase (0-1)
- `microplastic:degradation_rate`: Daily rate of degradation (0-1)
- `microplastic:resuspension_rate`: Daily rate of resuspension from seafloor (0-1)
- `microplastic:coastline_interaction`: How particles interact with coastlines:
  - `none`: No special interaction
  - `stranding`: Particles remain stranded on coastlines
  - `partial_stranding`: Some particles remain stranded, others are moved away

## Example Usage

Here's a simple example of how to use the model:

```python
from opendrift.models.microplastics import MicroplasticDrift
from datetime import datetime, timedelta

# Create a new simulation object
o = MicroplasticDrift(loglevel=20)  # 20=info

# Add environmental data (ocean currents, wind, etc.)
# ... add readers here ...

# Configure the simulation
o.set_config('vertical_mixing:diffusivitymodel', 'environment')
o.set_config('drift:vertical_mixing', True)
o.set_config('microplastic:biofouling_rate', 0.05)  # 5% biofouling increase per day
o.set_config('microplastic:degradation_rate', 0.01)  # 1% degradation per day
o.set_config('microplastic:coastline_interaction', 'partial_stranding')

# Seed with different types of microplastics
# Low-density polyethylene (LDPE)
o.seed_elements(lon=4.0, lat=62.0, number=100,
                density=920, diameter=1.0, shape_factor=1.0,
                time=datetime.now())

# Polystyrene (PS)
o.seed_elements(lon=4.0, lat=62.0, number=100,
                density=1050, diameter=0.5, shape_factor=1.2,
                time=datetime.now())

# Run the simulation
o.run(duration=timedelta(days=10),
      time_step=1800,  # 30 minutes
      outfile='microplastics_simulation.nc')

# Create plots
o.plot(fast=False)
o.plot(fast=False, key='density', colorbar=True)
o.animation_profile()  # Vertical distribution over time
```

For a complete example, see the file `examples/example_microplastic.py`.

## References

The model implementation is based on the following research:

1. Kooi, M., et al. (2017). The effect of particle properties on the depth profile of buoyant plastics in the ocean. Scientific Reports, 7(1), 1-10.
2. Chubarenko, I., et al. (2016). On some physical and dynamical properties of microplastic particles in marine environment. Marine Pollution Bulletin, 108(1-2), 105-112.
3. Koelmans, A. A., et al. (2017). All is not lost: deriving a top-down mass budget of plastic at sea. Environmental Research Letters, 12(11), 114028.

## Extensions

The model could be extended in future versions with:

- More complex biofouling processes based on environmental conditions
- Fragmentation processes (large particles breaking into smaller ones)
- Integration with ecological models (ingestion by marine organisms)
- Improved physical processes for transport in the water column

## Contact

For questions or suggestions, please contact the OpenDrift development team.
