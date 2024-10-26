import streamlit as st
import numpy as np

class VLCComponentManager:
    @staticmethod
    def add_component(component_type):
        """Add a new VLC component to the network"""
        if 'vlc_components' not in st.session_state:
            st.session_state.vlc_components = []
        if 'selected_component' not in st.session_state:
            st.session_state.selected_component = None
        
        new_component = {
            'type': component_type,
            'id': len(st.session_state.vlc_components),
            'position': [0, 0],  # Default position
            'properties': VLCComponentManager._get_default_properties(component_type)
        }
        
        st.session_state.vlc_components.append(new_component)
        st.session_state.selected_component = new_component['id']
        st.success(f"{component_type} added successfully!")

    @staticmethod
    def edit_component(component_id):
        """Edit an existing VLC component"""
        component = next((c for c in st.session_state.vlc_components if c['id'] == component_id), None)
        if not component:
            return
        
        st.subheader(f"Edit {component['type']}")
        
        if component['type'] == "Light Source":
            component['properties']['power'] = st.number_input(
                "Power (W)", 
                min_value=1.0, 
                max_value=50.0, 
                value=float(component['properties']['power']),
                help="Power output of the light source in Watts",
                key=f"power_{component_id}"
            )
            component['properties']['beam_angle'] = st.number_input(
                "Beam Angle (degrees)", 
                min_value=30.0, 
                max_value=180.0, 
                value=float(component['properties']['beam_angle']),
                help="Angle of the light beam emission",
                key=f"beam_angle_{component_id}"
            )
            component['properties']['wavelength'] = st.number_input(
                "Wavelength (nm)", 
                min_value=380.0, 
                max_value=780.0, 
                value=float(component['properties']['wavelength']),
                help="Light wavelength in nanometers",
                key=f"wavelength_{component_id}"
            )
            component['properties']['coverage_radius'] = st.number_input(
                "Coverage Radius (m)", 
                min_value=1.0, 
                max_value=10.0, 
                value=float(component['properties']['coverage_radius']),
                help="Effective coverage radius in meters",
                key=f"coverage_{component_id}"
            )
        else:  # Receiver
            component['properties']['sensitivity'] = st.number_input(
                "Sensitivity (dBm)", 
                min_value=-60.0, 
                max_value=-10.0, 
                value=float(component['properties']['sensitivity']),
                help="Receiver sensitivity in dBm",
                key=f"sensitivity_{component_id}"
            )
            component['properties']['fov'] = st.number_input(
                "Field of View (degrees)", 
                min_value=30.0, 
                max_value=180.0, 
                value=float(component['properties']['fov']),
                help="Field of view angle in degrees",
                key=f"fov_{component_id}"
            )
            component['properties']['active_area'] = st.number_input(
                "Active Area (cm²)", 
                min_value=0.01, 
                max_value=1.0, 
                value=float(component['properties']['active_area']),
                help="Active receiving area in square centimeters",
                format="%.2e",
                key=f"area_{component_id}"
            )

        if st.button("Delete Component", key=f"delete_{component_id}"):
            st.session_state.vlc_components = [c for c in st.session_state.vlc_components if c['id'] != component_id]
            st.session_state.selected_component = None
            st.success("Component deleted successfully!")

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

    @staticmethod
    def select_component(component_id):
        """Select a component for editing"""
        st.session_state.selected_component = component_id

    @staticmethod
    def get_selected_component():
        """Get the currently selected component"""
        if not hasattr(st.session_state, 'selected_component'):
            st.session_state.selected_component = None
        return st.session_state.selected_component
