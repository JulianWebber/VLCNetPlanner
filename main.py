import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from components.floor_plan import FloorPlanManager
from components.vlc_components import VLCComponentManager
from components.visualization import NetworkVisualizer
from utils.optimization import optimize_placement
from utils.coverage_analysis import analyze_coverage
from utils.data_handler import export_configuration

def main():
    st.set_page_config(page_title="VLC Network Planner", layout="wide")
    
    st.title("VLC Network Planning and Optimization Tool")
    
    # Initialize session state
    if 'floor_plans' not in st.session_state:
        st.session_state.floor_plans = {}
        st.session_state.vlc_components = []
        st.session_state.coverage_map = None
        st.session_state.selected_component = None
        st.session_state.preview_mode = False
        st.session_state.component_history = []
        st.session_state.history_index = -1
        st.session_state.current_floor_level = 0
        st.session_state.view_3d = False

    # Main content layout
    col1, col2 = st.columns([2, 1])

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Floor Management Section
        st.subheader("Floor Management")
        floor_level = st.number_input("Floor Level", min_value=0, max_value=10, value=st.session_state.current_floor_level)
        st.session_state.current_floor_level = floor_level
        
        ceiling_height = st.number_input("Ceiling Height (m)", min_value=2.0, max_value=5.0, value=3.0)
        
        # Floor Plan Section
        st.subheader("Floor Plan")
        upload_option = st.radio("Floor Plan Input", ["Upload", "Create New"])
        
        if upload_option == "Upload":
            uploaded_file = st.file_uploader("Upload Floor Plan", type=['svg', 'png', 'jpg'])
            if uploaded_file:
                st.session_state.floor_plans[floor_level] = FloorPlanManager.load_floor_plan(
                    uploaded_file, floor_level=floor_level
                )
        else:
            dimensions = st.columns(2)
            width = dimensions[0].number_input("Width (m)", 5.0, 100.0, 20.0)
            height = dimensions[1].number_input("Height (m)", 5.0, 100.0, 15.0)
            if st.button("Create Floor Plan"):
                st.session_state.floor_plans[floor_level] = FloorPlanManager.create_new(
                    width, height, floor_level=floor_level, ceiling_height=ceiling_height
                )

        # VLC Components Section
        st.subheader("Add Components")
        component_type = st.selectbox("Component Type", ["Light Source", "Receiver"])
        if st.button("Add New Component"):
            new_component = VLCComponentManager.add_component(component_type)
            if new_component:
                new_component['floor_level'] = floor_level
                st.session_state.vlc_components.append(new_component)

        # Component List and Selection
        if st.session_state.vlc_components:
            st.subheader("Component List")
            for comp in st.session_state.vlc_components:
                if st.button(f"{comp['type']} {comp['id']} (Floor {comp.get('floor_level', 0)})", 
                           key=f"select_{comp['id']}",
                           help="Click to edit component"):
                    st.session_state.selected_component = comp['id']

    # Main visualization area
    with col1:
        st.subheader("Network Layout")
        if st.session_state.floor_plans:
            # View controls
            controls_col1, controls_col2, controls_col3 = st.columns(3)
            
            with controls_col1:
                view_3d = st.toggle("3D View", value=st.session_state.view_3d)
                st.session_state.view_3d = view_3d
            
            with controls_col2:
                preview_mode = st.toggle("Preview Mode", value=st.session_state.preview_mode)
                st.session_state.preview_mode = preview_mode
            
            with controls_col3:
                if st.button("Optimize Placement"):
                    current_floor_plan = st.session_state.floor_plans[st.session_state.current_floor_level]
                    current_components = [c for c in st.session_state.vlc_components 
                                       if c.get('floor_level', 0) == st.session_state.current_floor_level]
                    
                    optimized_positions = optimize_placement(current_floor_plan, current_components)
                    
                    # Update only components on current floor
                    for opt_comp in optimized_positions:
                        for comp in st.session_state.vlc_components:
                            if comp['id'] == opt_comp['id']:
                                comp['position'] = opt_comp['position']
                                break

            network_viz = NetworkVisualizer(st.session_state.floor_plans, st.session_state.vlc_components)
            network_viz.view_3d = st.session_state.view_3d
            fig = network_viz.plot()
            
            st.plotly_chart(fig, use_container_width=True)
            
            if st.session_state.preview_mode:
                st.info("Preview Mode: Drag components to see real-time coverage updates")

    # Component editor and analysis area
    with col2:
        # Component Editor
        if st.session_state.selected_component is not None:
            component = next((c for c in st.session_state.vlc_components 
                            if c['id'] == st.session_state.selected_component), None)
            if component:
                st.subheader(f"Edit {component['type']}")
                VLCComponentManager.edit_component(component)
                
                # Add floor level editor
                new_floor = st.number_input("Floor Level", 
                                          min_value=0, 
                                          max_value=10, 
                                          value=component.get('floor_level', 0))
                component['floor_level'] = new_floor
        
        # Analysis Section
        st.subheader("Network Analysis")
        if st.session_state.floor_plans:
            current_floor_plan = st.session_state.floor_plans[st.session_state.current_floor_level]
            current_components = [c for c in st.session_state.vlc_components 
                               if c.get('floor_level', 0) == st.session_state.current_floor_level]
            
            coverage_map = analyze_coverage(current_floor_plan, current_components)
            st.session_state.coverage_map = coverage_map
            
            st.metric("Coverage (%)", f"{coverage_map['coverage_percentage']:.1f}%")
            st.metric("Interference Points", coverage_map['interference_points'])
            
            # Power efficiency metrics
            total_power = sum(comp['properties']['power'] 
                            for comp in current_components 
                            if comp['type'] == "Light Source")
            coverage_ratio = coverage_map['coverage_percentage'] / 100
            efficiency = coverage_ratio / total_power if total_power > 0 else 0
            
            st.metric("Power Efficiency", f"{efficiency:.3f} %/W")

            if st.button("Export Configuration"):
                export_data = export_configuration(st.session_state.floor_plans,
                                              st.session_state.vlc_components,
                                              st.session_state.coverage_map)
                st.download_button("Download Configuration",
                                export_data,
                                file_name="vlc_configuration.json",
                                mime="application/json")

if __name__ == "__main__":
    main()
