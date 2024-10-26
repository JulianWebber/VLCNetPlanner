import plotly.graph_objects as go
import numpy as np
import streamlit as st

class NetworkVisualizer:
    def __init__(self, floor_plans, components):
        self.floor_plans = floor_plans if isinstance(floor_plans, dict) else {0: floor_plans}
        self.components = components
        self.view_3d = False
        self.show_interference = False
        self.show_sinr = False

    def plot(self):
        """Create an interactive plot of the VLC network"""
        if self.view_3d:
            return self._plot_3d()
        else:
            return self._plot_2d()

    def _plot_2d(self):
        """Create 2D visualization for current floor level"""
        current_floor = st.session_state.get('current_floor_level', 0)
        floor_plan = self.floor_plans.get(current_floor, self.floor_plans[0])
        
        fig = go.Figure()

        # Draw floor plan outline
        fig.add_trace(go.Scatter(
            x=[0, floor_plan['width'], floor_plan['width'], 0, 0],
            y=[0, 0, floor_plan['height'], floor_plan['height'], 0],
            mode='lines',
            line=dict(color='black'),
            name=f'Floor {current_floor}'
        ))

        # Calculate coverage and interference maps
        coverage_map, interference_map, sinr_map = self._calculate_maps(current_floor)

        # Create visualization grid
        x = np.linspace(0, floor_plan['width'], 50)
        y = np.linspace(0, floor_plan['height'], 50)

        # Add appropriate heatmap based on visualization mode
        if self.show_sinr:
            fig.add_trace(go.Heatmap(
                x=x, y=y, z=sinr_map,
                colorscale='RdYlBu',
                opacity=0.5,
                showscale=True,
                name='SINR Map',
                hoverongaps=False,
                hovertemplate='SINR: %{z:.1f} dB<br>X: %{x:.1f}m<br>Y: %{y:.1f}m<extra></extra>',
                colorbar=dict(title='SINR (dB)')
            ))
        elif self.show_interference:
            fig.add_trace(go.Heatmap(
                x=x, y=y, z=interference_map,
                colorscale='Reds',
                opacity=0.5,
                showscale=True,
                name='Interference Map',
                hoverongaps=False,
                hovertemplate='Interference: %{z:.2f}<br>X: %{x:.1f}m<br>Y: %{y:.1f}m<extra></extra>',
                colorbar=dict(title='Interference Level')
            ))
        else:
            fig.add_trace(go.Heatmap(
                x=x, y=y, z=coverage_map,
                colorscale='YlOrRd',
                opacity=0.3,
                showscale=True,
                name='Coverage Map',
                hoverongaps=False,
                hovertemplate='Coverage: %{z:.1f}<br>X: %{x:.1f}m<br>Y: %{y:.1f}m<extra></extra>',
                colorbar=dict(title='Signal Strength (W/m²)')
            ))

        # Add components
        selected_id = st.session_state.get('selected_component', None)
        for component in self.components:
            if component.get('floor_level', 0) == current_floor:
                if component['type'] == "Light Source":
                    self._add_light_source(fig, component, selected=component['id'] == selected_id)
                else:
                    self._add_receiver(fig, component, selected=component['id'] == selected_id)

        # Update layout
        fig.update_layout(
            showlegend=True,
            hovermode='closest',
            dragmode='pan',
            plot_bgcolor='white',
            width=800,
            height=600,
            xaxis=dict(
                range=[-1, floor_plan['width'] + 1],
                showgrid=True,
                title="Width (meters)",
                constrain="domain"
            ),
            yaxis=dict(
                range=[-1, floor_plan['height'] + 1],
                showgrid=True,
                title="Height (meters)",
                scaleanchor="x",
                scaleratio=1
            )
        )

        return fig

    def _calculate_maps(self, current_floor):
        """Calculate coverage, interference, and SINR maps"""
        floor_plan = self.floor_plans.get(current_floor, self.floor_plans[0])
        
        from utils.coverage_analysis import analyze_coverage
        analysis_result = analyze_coverage(floor_plan, [c for c in self.components 
                                                      if c.get('floor_level', 0) == current_floor])
        
        return (analysis_result['coverage_map'],
                analysis_result['interference_map'],
                analysis_result['sinr_map'])

    def _plot_3d(self):
        """Create 3D visualization of the VLC network"""
        fig = go.Figure()

        # Add floor planes
        for level, floor_plan in self.floor_plans.items():
            base_height = level * 3.0
            vertices = [
                [0, 0, base_height],
                [floor_plan['width'], 0, base_height],
                [floor_plan['width'], floor_plan['height'], base_height],
                [0, floor_plan['height'], base_height]
            ]
            i, j, k = [0, 0, 0], [1, 2, 3], [2, 3, 1]

            fig.add_trace(go.Mesh3d(
                x=[v[0] for v in vertices],
                y=[v[1] for v in vertices],
                z=[v[2] for v in vertices],
                i=i, j=j, k=k,
                opacity=0.6,
                color='lightgray',
                name=f'Floor {level}'
            ))

        # Add components in 3D
        for component in self.components:
            pos = component['position']
            floor_level = component.get('floor_level', 0)
            base_height = floor_level * 3.0
            
            if component['type'] == "Light Source":
                self._add_light_source_3d(fig, component, base_height)
            else:
                self._add_receiver_3d(fig, component, base_height)

        # Update 3D layout
        fig.update_layout(
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Length (m)",
                zaxis_title="Height (m)",
                aspectmode='data'
            ),
            showlegend=True,
            width=800,
            height=600
        )

        return fig

    def _add_light_source_3d(self, fig, component, base_height):
        """Add light source to 3D visualization"""
        pos = component['position']
        properties = component['properties']
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°<br>"
            f"Wavelength: {properties['wavelength']}nm"
        )

        fig.add_trace(go.Scatter3d(
            x=[pos[0]],
            y=[pos[1]],
            z=[base_height],
            mode='markers',
            marker=dict(
                symbol='diamond',
                size=8,
                color='yellow',
                line=dict(color='orange', width=2)
            ),
            name=f"Light Source {component['id']}",
            text=hover_text,
            hoverinfo='text'
        ))

    def _add_receiver_3d(self, fig, component, base_height):
        """Add receiver to 3D visualization"""
        pos = component['position']
        properties = component['properties']
        
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Sensitivity: {properties['sensitivity']}dBm<br>"
            f"FOV: {properties['fov']}°"
        )

        fig.add_trace(go.Scatter3d(
            x=[pos[0]],
            y=[pos[1]],
            z=[base_height],
            mode='markers',
            marker=dict(
                symbol='square',
                size=6,
                color='blue',
                line=dict(color='darkblue', width=2)
            ),
            name=f"Receiver {component['id']}",
            text=hover_text,
            hoverinfo='text'
        ))

    def _add_light_source(self, fig, component, selected=False):
        """Add light source to 2D visualization"""
        pos = component['position']
        properties = component['properties']
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°<br>"
            f"Wavelength: {properties['wavelength']}nm"
        )

        marker_color = 'gold' if selected else 'yellow'
        marker_line_width = 3 if selected else 1.5

        fig.add_trace(go.Scatter(
            x=[pos[0]],
            y=[pos[1]],
            mode='markers+text',
            marker=dict(
                symbol='star',
                size=15,
                color=marker_color,
                line=dict(color='orange', width=marker_line_width)
            ),
            text=f"LS{component['id']}",
            textposition="top center",
            name=f"Light Source {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))

    def _add_receiver(self, fig, component, selected=False):
        """Add receiver to 2D visualization"""
        pos = component['position']
        properties = component['properties']
        
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Sensitivity: {properties['sensitivity']}dBm<br>"
            f"FOV: {properties['fov']}°"
        )

        marker_color = 'royalblue' if selected else 'blue'
        marker_line_width = 3 if selected else 1.5

        fig.add_trace(go.Scatter(
            x=[pos[0]],
            y=[pos[1]],
            mode='markers+text',
            marker=dict(
                symbol='square',
                size=10,
                color=marker_color,
                line=dict(color='darkblue', width=marker_line_width)
            ),
            text=f"R{component['id']}",
            textposition="top center",
            name=f"Receiver {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))
