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
        st.session_state.show_interference = False
        st.session_state.show_sinr = False

    # Main content layout
    col1, col2 = st.columns([2, 1])

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Floor Management Section
        st.subheader("Floor Management")
        floor_level = st.number_input("Floor Level", min_value=0, max_value=10, 
                                    value=st.session_state.current_floor_level,
                                    key='floor_level_sidebar')
        st.session_state.current_floor_level = floor_level
        
        ceiling_height = st.number_input("Ceiling Height (m)", min_value=2.0, max_value=5.0, value=3.0)
        
        # Floor Plan Section
        st.subheader("Floor Plan")
        upload_option = st.radio("Floor Plan Input", ["Upload", "Create New"])
        
        if upload_option == "Upload":
            uploaded_file = st.file_uploader("Upload Floor Plan", 
                                          type=['dxf', 'svg', 'png', 'jpg', 'jpeg'],
                                          help="Supported formats: DXF (CAD), SVG, PNG, JPG")
            if uploaded_file:
                try:
                    st.session_state.floor_plans[floor_level] = FloorPlanManager.load_floor_plan(
                        uploaded_file, floor_level=floor_level
                    )
                    st.success(f"Floor plan loaded successfully for floor {floor_level}")
                except Exception as e:
                    st.error(f"Error loading floor plan: {str(e)}")
        else:
            dimensions = st.columns(2)
            width = dimensions[0].number_input("Width (m)", 5.0, 100.0, 20.0)
            height = dimensions[1].number_input("Height (m)", 5.0, 100.0, 15.0)
            if st.button("Create Floor Plan"):
                st.session_state.floor_plans[floor_level] = FloorPlanManager.create_new(
                    width, height, floor_level=floor_level, ceiling_height=ceiling_height
                )

        # Rest of the main function remains unchanged
        # ... [Previous main function code continues here]

if __name__ == "__main__":
    main()
