import streamlit as st
import numpy as np

class VLCComponentManager:
    @staticmethod
    def add_component(component_type):
        """Add a new VLC component to the network"""
        if 'vlc_components' not in st.session_state:
            st.session_state.vlc_components = []
        
        new_component = {
            'type': component_type,
            'id': len(st.session_state.vlc_components),
            'position': [0, 0],  # Default position
            'properties': VLCComponentManager._get_default_properties(component_type)
        }
        
        # Add component configuration form
        st.subheader(f"Configure {component_type}")
        with st.form(f"component_config_{new_component['id']}"):
            if component_type == "Light Source":
                new_component['properties']['power'] = st.number_input(
                    "Power (W)", 
                    min_value=1.0, 
                    max_value=50.0, 
                    value=20.0,
                    help="Power output of the light source in Watts"
                )
                new_component['properties']['beam_angle'] = st.number_input(
                    "Beam Angle (degrees)", 
                    min_value=30.0, 
                    max_value=180.0, 
                    value=120.0,
                    help="Angle of the light beam emission"
                )
                new_component['properties']['wavelength'] = st.number_input(
                    "Wavelength (nm)", 
                    min_value=380.0, 
                    max_value=780.0, 
                    value=550.0,
                    help="Light wavelength in nanometers"
                )
                new_component['properties']['coverage_radius'] = st.number_input(
                    "Coverage Radius (m)", 
                    min_value=1.0, 
                    max_value=10.0, 
                    value=3.0,
                    help="Effective coverage radius in meters"
                )
            else:  # Receiver
                new_component['properties']['sensitivity'] = st.number_input(
                    "Sensitivity (dBm)", 
                    min_value=-60.0, 
                    max_value=-10.0, 
                    value=-30.0,
                    help="Receiver sensitivity in dBm"
                )
                new_component['properties']['fov'] = st.number_input(
                    "Field of View (degrees)", 
                    min_value=30.0, 
                    max_value=180.0, 
                    value=60.0,
                    help="Field of view angle in degrees"
                )
                new_component['properties']['active_area'] = st.number_input(
                    "Active Area (cm²)", 
                    min_value=0.01, 
                    max_value=1.0, 
                    value=0.01,
                    help="Active receiving area in square centimeters",
                    format="%.2e"
                )
            
            if st.form_submit_button("Add Component"):
                st.session_state.vlc_components.append(new_component)
                st.success(f"{component_type} added successfully!")

    @staticmethod
    def _get_default_properties(component_type):
        """Get default properties for different component types"""
        if component_type == "Light Source":
            return {
                'power': 20,  # Watts
                'beam_angle': 120,  # degrees
                'wavelength': 550,  # nm
                'coverage_radius': 3  # meters
            }
        else:  # Receiver
            return {
                'sensitivity': -30,  # dBm
                'fov': 60,  # degrees
                'active_area': 1e-4  # m^2
            }
