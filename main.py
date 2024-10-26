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
        st.subheader("VLC Components")
        component_type = st.selectbox("Add Component", ["Light Source", "Receiver"])
        if st.button("Add Component"):
            VLCComponentManager.add_component(component_type)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Network Layout")
        if st.session_state.floor_plan is not None:
            network_viz = NetworkVisualizer(st.session_state.floor_plan, st.session_state.vlc_components)
            fig = network_viz.plot()
            st.plotly_chart(fig, use_container_width=True)

            if st.button("Optimize Placement"):
                optimized_positions = optimize_placement(st.session_state.floor_plan, 
                                                      st.session_state.vlc_components)
                st.session_state.vlc_components = optimized_positions

    with col2:
        st.subheader("Analysis")
        if st.session_state.floor_plan is not None:
            coverage_map = analyze_coverage(st.session_state.floor_plan, 
                                         st.session_state.vlc_components)
            st.session_state.coverage_map = coverage_map
            
            st.metric("Coverage (%)", f"{coverage_map['coverage_percentage']:.1f}%")
            st.metric("Interference Points", coverage_map['interference_points'])

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