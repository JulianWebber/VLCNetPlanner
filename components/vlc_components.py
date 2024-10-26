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
        
        st.session_state.vlc_components.append(new_component)

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
