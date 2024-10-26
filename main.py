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
    if 'floor_plan' not in st.session_state:
        st.session_state.floor_plan = None
        st.session_state.vlc_components = []
        st.session_state.coverage_map = None
        st.session_state.selected_component = None
        st.session_state.preview_mode = False
        st.session_state.component_history = []
        st.session_state.history_index = -1

    # Main content layout
    col1, col2 = st.columns([2, 1])

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Floor Plan Section
        st.subheader("Floor Plan")
        upload_option = st.radio("Floor Plan Input", ["Upload", "Create New"])
        
        if upload_option == "Upload":
            uploaded_file = st.file_uploader("Upload Floor Plan", type=['svg', 'png', 'jpg'])
            if uploaded_file:
                st.session_state.floor_plan = FloorPlanManager.load_floor_plan(uploaded_file)
        else:
            dimensions = st.columns(2)
            width = dimensions[0].number_input("Width (m)", 5.0, 100.0, 20.0)
            height = dimensions[1].number_input("Height (m)", 5.0, 100.0, 15.0)
            if st.button("Create Floor Plan"):
                st.session_state.floor_plan = FloorPlanManager.create_new(width, height)

        # VLC Components Section
        st.subheader("Add Components")
        component_type = st.selectbox("Component Type", ["Light Source", "Receiver"])
        if st.button("Add New Component"):
            VLCComponentManager.add_component(component_type)

        # Component List and Selection
        if st.session_state.vlc_components:
            st.subheader("Component List")
            for comp in st.session_state.vlc_components:
                if st.button(f"{comp['type']} {comp['id']}", 
                           key=f"select_{comp['id']}",
                           help="Click to edit component"):
                    st.session_state.selected_component = comp['id']

    # Main visualization area
    with col1:
        st.subheader("Network Layout")
        if st.session_state.floor_plan is not None:
            # Interaction controls
            controls_col1, controls_col2, controls_col3 = st.columns(3)
            
            with controls_col1:
                preview_mode = st.toggle("Preview Mode", value=st.session_state.preview_mode)
                st.session_state.preview_mode = preview_mode
            
            with controls_col2:
                undo_col, redo_col = st.columns(2)
                if undo_col.button("↩ Undo"):
                    network_viz.undo()
                if redo_col.button("↪ Redo"):
                    network_viz.redo()
            
            with controls_col3:
                if st.button("Optimize Placement"):
                    optimized_positions = optimize_placement(st.session_state.floor_plan, 
                                                         st.session_state.vlc_components)
                    st.session_state.vlc_components = optimized_positions
                    # Add to history
                    if hasattr(network_viz, '_add_to_history'):
                        network_viz._add_to_history()

            network_viz = NetworkVisualizer(st.session_state.floor_plan, st.session_state.vlc_components)
            fig = network_viz.plot()
            
            st.plotly_chart(fig, use_container_width=True)
            
            if st.session_state.preview_mode:
                st.info("Preview Mode: Drag components to see real-time coverage updates")

    # Component editor and analysis area
    with col2:
        # Component Editor
        if st.session_state.selected_component is not None:
            VLCComponentManager.edit_component(st.session_state.selected_component)
        
        # Analysis Section
        st.subheader("Network Analysis")
        if st.session_state.floor_plan is not None:
            coverage_map = analyze_coverage(st.session_state.floor_plan, 
                                        st.session_state.vlc_components)
            st.session_state.coverage_map = coverage_map
            
            st.metric("Coverage (%)", f"{coverage_map['coverage_percentage']:.1f}%")
            st.metric("Interference Points", coverage_map['interference_points'])
            
            # Power efficiency metrics
            total_power = sum(comp['properties']['power'] 
                            for comp in st.session_state.vlc_components 
                            if comp['type'] == "Light Source")
            coverage_ratio = coverage_map['coverage_percentage'] / 100
            efficiency = coverage_ratio / total_power if total_power > 0 else 0
            
            st.metric("Power Efficiency", f"{efficiency:.3f} %/W")

            if st.button("Export Configuration"):
                export_data = export_configuration(st.session_state.floor_plan,
                                               st.session_state.vlc_components,
                                               st.session_state.coverage_map)
                st.download_button("Download Configuration",
                                export_data,
                                file_name="vlc_configuration.json",
                                mime="application/json")

if __name__ == "__main__":
    main()
