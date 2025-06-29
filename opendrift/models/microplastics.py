# This file is part of OpenDrift.
#
# OpenDrift is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# OpenDrift is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenDrift.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2023

import numpy as np
import logging
logger = logging.getLogger(__name__)

from opendrift.models.oceandrift import OceanDrift, Lagrangian3DArray
from opendrift.models.basemodel import OpenDriftSimulation
from opendrift.config import CONFIG_LEVEL_ESSENTIAL, CONFIG_LEVEL_BASIC, CONFIG_LEVEL_ADVANCED


# Define microplastic element properties
class MicroplasticElement(Lagrangian3DArray):
    """Extending Lagrangian3DArray for elements representing microplastic particles"""
    
    variables = Lagrangian3DArray.add_variables([
        ('diameter', {'dtype': np.float32,
                     'units': 'mm',
                     'default': 1.0,
                     'description': 'Diameter of microplastic particle'}),
        ('density', {'dtype': np.float32,
                    'units': 'kg/m3',
                    'default': 920.0,  # Typical density of polyethylene
                    'description': 'Density of microplastic particle material'}),
        ('shape_factor', {'dtype': np.float32,
                         'units': '1',
                         'default': 1.0,  # 1.0 for perfect sphere
                         'description': 'Shape factor affecting drag coefficient (1.0 for perfect sphere)'}),
        ('biofouling_level', {'dtype': np.float32,
                             'units': '1',
                             'default': 0.0,  # 0.0 means no biofouling
                             'description': 'Biofouling level, affecting buoyancy (0-1)'}),
        ('degradation_state', {'dtype': np.float32,
                              'units': '1',
                              'default': 0.0,  # 0.0 means new, 1.0 fully degraded
                              'description': 'Degradation state of particle (0-1)'})
        ])


class MicroplasticDrift(OceanDrift):
    """Microplastic drift model based on the OpenDrift framework.
    
    This model simulates drift of microplastic particles in the marine environment,
    accounting for specific properties like density, size, shape, biofouling, and degradation.
    """
    
    ElementType = MicroplasticElement
    
    # Additional required variables beyond those needed by OceanDrift
    required_variables = {
        'x_sea_water_velocity': {'fallback': 0},
        'y_sea_water_velocity': {'fallback': 0},
        'sea_surface_height': {'fallback': 0},
        'x_wind': {'fallback': 0},
        'y_wind': {'fallback': 0},
        'upward_sea_water_velocity': {'fallback': 0},
        'ocean_vertical_diffusivity': {'fallback': 0,
                                       'profiles': True},
        'sea_water_temperature': {'fallback': 10},
        'sea_water_density': {'fallback': 1025},
        'sea_floor_depth_below_sea_level': {'fallback': 10000},
        'land_binary_mask': {'fallback': None}
    }
    
    def __init__(self, *args, **kwargs):
        # Call parent constructor
        super(MicroplasticDrift, self).__init__(*args, **kwargs)
        
        # Add specific config settings for microplastics
        self._add_config({
            'seed:diameter': {
                'type': 'float', 'default': 1.0,
                'min': 0.001, 'max': 100.0, 'units': 'mm',
                'description': 'Diameter of seeded microplastic particles',
                'level': CONFIG_LEVEL_ESSENTIAL
            },
            'seed:density': {
                'type': 'float', 'default': 920.0,
                'min': 800.0, 'max': 2500.0, 'units': 'kg/m3',
                'description': 'Density of seeded microplastic particles',
                'level': CONFIG_LEVEL_ESSENTIAL
            },
            'seed:shape_factor': {
                'type': 'float', 'default': 1.0,
                'min': 0.1, 'max': 10.0, 'units': '1',
                'description': 'Shape factor of seeded microplastic particles (1.0 for sphere)',
                'level': CONFIG_LEVEL_BASIC
            },
            'microplastic:biofouling_rate': {
                'type': 'float', 'default': 0.0, 
                'min': 0.0, 'max': 1.0, 'units': '1/day',
                'description': 'Daily rate of biofouling increase',
                'level': CONFIG_LEVEL_BASIC
            },
            'microplastic:degradation_rate': {
                'type': 'float', 'default': 0.0,
                'min': 0.0, 'max': 1.0, 'units': '1/day',
                'description': 'Daily rate of degradation',
                'level': CONFIG_LEVEL_BASIC
            },
            'microplastic:resuspension_rate': {
                'type': 'float', 'default': 0.0,
                'min': 0.0, 'max': 1.0, 'units': '1/day',
                'description': 'Daily rate of resuspension from seafloor',
                'level': CONFIG_LEVEL_BASIC
            },
            'microplastic:coastline_interaction': {
                'type': 'enum', 'enum': ['none', 'stranding', 'partial_stranding'],
                'default': 'none',
                'description': 'How microplastics interact with coastlines',
                'level': CONFIG_LEVEL_BASIC
            }
        })
    
    def update_terminal_velocity(self, *args, **kwargs):
        """Calculate terminal velocity for microplastic particles.
        
        Using Stokes Law with modifications for non-spherical particles 
        and effects of biofouling.
        """
        # Water properties
        water_density = self.environment.sea_water_density
        
        # Calculate effective density including biofouling effects
        # Biofouling increases effective density
        biofouling_factor = 1.0 + self.elements.biofouling_level  # Simple linear relationship
        effective_density = self.elements.density * biofouling_factor
        
        # Calculate Reynolds number-based drag coefficient
        # Simplified approach - in reality would depend on Reynolds number
        g = 9.81  # m/s^2, gravitational acceleration
        diameter_m = self.elements.diameter / 1000.0  # convert mm to m
        
        # Calculate buoyancy force considering Archimedes principle
        submerged_weight = g * (effective_density - water_density) / water_density
        
        # Terminal velocity using Stokes' law with shape factor adjustment
        # Negative terminal velocity means sinking, positive means rising
        # Shape factor increases drag (reduces velocity) for non-spherical particles
        water_viscosity = 0.0014  # Pa·s, approximate dynamic viscosity of seawater
        terminal_velocity = (submerged_weight * (diameter_m**2)) / (18 * water_viscosity * self.elements.shape_factor)
        
        # Update element terminal_velocity
        self.elements.terminal_velocity = terminal_velocity
        
    def update(self):
        """Update positions and properties of microplastic elements."""
        
        # Calculate time step in seconds
        time_step_seconds = self.time_step.total_seconds()
        
        # First, update microplastic specific properties
        
        # Update biofouling level
        if self.get_config('microplastic:biofouling_rate') > 0:
            biofouling_increment = self.get_config('microplastic:biofouling_rate') * time_step_seconds / 86400  # convert from daily rate
            # Biofouling accumulates more in surface waters (simplified approach)
            surface_factor = np.ones(self.num_elements_active())
            near_surface = np.where(self.elements.z > -10)[0]
            if len(near_surface) > 0:
                surface_factor[near_surface] = 2.0  # Higher biofouling near surface
            
            self.elements.biofouling_level = np.minimum(
                1.0,  # Maximum biofouling level
                self.elements.biofouling_level + biofouling_increment * surface_factor
            )
        
        # Update degradation state
        if self.get_config('microplastic:degradation_rate') > 0:
            degradation_increment = self.get_config('microplastic:degradation_rate') * time_step_seconds / 86400  # convert from daily rate
            # Degradation happens faster at surface (UV exposure)
            surface_factor = np.ones(self.num_elements_active())
            at_surface = np.where(self.elements.z > -0.5)[0]
            if len(at_surface) > 0:
                surface_factor[at_surface] = 3.0  # Much faster degradation at surface
            
            self.elements.degradation_state = np.minimum(
                1.0,  # Maximum degradation
                self.elements.degradation_state + degradation_increment * surface_factor
            )
            
            # As plastics degrade, their size decreases slightly
            size_reduction_factor = 1.0 - 0.1 * self.elements.degradation_state
            self.elements.diameter = self.elements.diameter * size_reduction_factor
        
        # Calculate terminal velocity considering all particle properties
        self.update_terminal_velocity()
        
        # Now call parent update methods for advection and mixing
        super().update()
        
    def interact_with_seafloor(self):
        """Method to handle interaction with the seafloor."""
        
        # First call the parent method
        super().interact_with_seafloor()
        
        # Check for potential resuspension based on config
        if self.get_config('microplastic:resuspension_rate') > 0:
            resuspension_probability = self.get_config('microplastic:resuspension_rate') * self.time_step.total_seconds() / 86400
            bottom_particles = np.where(
                (self.elements.z < -self.environment.sea_floor_depth_below_sea_level) & 
                (np.random.random(self.num_elements_active()) < resuspension_probability)
            )[0]
            
            if len(bottom_particles) > 0:
                logger.debug(f'Resuspending {len(bottom_particles)} particles from seafloor')
                # Move the resuspended particles slightly up
                self.elements.z[bottom_particles] = -self.environment.sea_floor_depth_below_sea_level[bottom_particles] + 0.5

    def interact_with_coastline(self):
        """Method to handle interaction with coastlines."""
        
        # Get coastline interaction setting
        interaction_type = self.get_config('microplastic:coastline_interaction')
        
        if interaction_type == 'none':
            return
        
        # Find stranded elements
        stranded = np.where(self.environment.land_binary_mask == 1)[0]
        if len(stranded) == 0:
            return
            
        if interaction_type == 'stranding':
            # All stranded particles remain on the coastline
            self.deactivate_elements(stranded, reason='stranded')
            
        elif interaction_type == 'partial_stranding':
            # Only a portion of particles remain stranded, others are moved back
            stranding_probability = 0.5  # 50% chance of stranding
            permanently_stranded = stranded[np.random.random(len(stranded)) < stranding_probability]
            
            if len(permanently_stranded) > 0:
                self.deactivate_elements(permanently_stranded, reason='stranded')
                
    def seed_elements(self, lon, lat, z=0, diameter=None, density=None, 
                      shape_factor=None, *args, **kwargs):
        """Seed microplastic elements with specific properties."""
        
        # Set default properties if not provided
        if diameter is None:
            diameter = self.get_config('seed:diameter')
            
        if density is None:
            density = self.get_config('seed:density')
            
        if shape_factor is None:
            shape_factor = self.get_config('seed:shape_factor')
            
        # Call parent seed_elements method with the additional arguments
        super(MicroplasticDrift, self).seed_elements(
            lon=lon, lat=lat, z=z, diameter=diameter, density=density, 
            shape_factor=shape_factor, *args, **kwargs
        ) 