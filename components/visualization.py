import plotly.graph_objects as go
import numpy as np
import streamlit as st

class NetworkVisualizer:
    def __init__(self, floor_plan, components):
        self.floor_plan = floor_plan
        self.components = components

    def plot(self):
        """Create an interactive plot of the VLC network"""
        fig = go.Figure()

        # Add floor plan
        fig.add_trace(go.Scatter(
            x=[0, self.floor_plan['width'], self.floor_plan['width'], 0, 0],
            y=[0, 0, self.floor_plan['height'], self.floor_plan['height'], 0],
            mode='lines',
            line=dict(color='black'),
            name='Floor Plan'
        ))

        # Calculate coverage and interference maps
        coverage_map, interference_map = self._calculate_coverage_interference()

        # Add coverage heatmap
        x = np.linspace(0, self.floor_plan['width'], 50)
        y = np.linspace(0, self.floor_plan['height'], 50)
        fig.add_trace(go.Heatmap(
            x=x,
            y=y,
            z=coverage_map,
            colorscale='YlOrRd',
            opacity=0.3,
            showscale=True,
            name='Coverage',
            hoverongaps=False,
            hovertemplate='Coverage: %{z:.1f}<br>X: %{x:.1f}m<br>Y: %{y:.1f}m<extra></extra>'
        ))

        # Add components
        selected_id = st.session_state.get('selected_component', None)
        for component in self.components:
            if component['type'] == "Light Source":
                self._add_light_source(fig, component, selected=component['id'] == selected_id)
            else:
                self._add_receiver(fig, component, selected=component['id'] == selected_id)

        # Update layout
        fig.update_layout(
            showlegend=True,
            hovermode='closest',
            dragmode='select',  # Enable selection mode
            plot_bgcolor='white',
            width=800,
            height=600,
            xaxis=dict(
                range=[-1, self.floor_plan['width'] + 1],
                showgrid=True,
                title="Width (meters)"
            ),
            yaxis=dict(
                range=[-1, self.floor_plan['height'] + 1],
                showgrid=True,
                title="Height (meters)"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            ),
            modebar=dict(
                add=['select2d', 'lasso2d']
            )
        )
        
        return fig

    def _calculate_coverage_interference(self):
        """Calculate coverage and interference maps"""
        x = np.linspace(0, self.floor_plan['width'], 50)
        y = np.linspace(0, self.floor_plan['height'], 50)
        xx, yy = np.meshgrid(x, y)
        
        coverage_map = np.zeros_like(xx)
        interference_map = np.zeros_like(xx)
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                
                distance = np.sqrt((xx - pos[0])**2 + (yy - pos[1])**2)
                coverage = np.where(distance <= radius, 
                                  power * (1 - distance/radius), 
                                  0)
                coverage_map += coverage
                interference_map += (coverage > 0).astype(float)
        
        return coverage_map, interference_map - 1  # Subtract 1 to show only overlapping areas

    def _add_light_source(self, fig, component, selected=False):
        """Add light source visualization"""
        pos = component['position']
        properties = component['properties']
        
        # Calculate real-time coverage at component location
        coverage_val = self._get_coverage_at_point(pos[0], pos[1])
        interference_val = self._get_interference_at_point(pos[0], pos[1])
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°<br>"
            f"Wavelength: {properties['wavelength']}nm<br>"
            f"Coverage Radius: {properties['coverage_radius']}m<br>"
            f"Coverage Level: {coverage_val:.1f}<br>"
            f"Interference Level: {interference_val:.1f}"
        )

        marker_color = 'yellow' if not selected else 'gold'
        marker_line_width = 2 if not selected else 4

        fig.add_trace(go.Scatter(
            x=[pos[0]],
            y=[pos[1]],
            mode='markers',
            marker=dict(
                symbol='star',
                size=15,
                color=marker_color,
                line=dict(color='orange', width=marker_line_width)
            ),
            name=f"Light Source {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))

    def _add_receiver(self, fig, component, selected=False):
        """Add receiver visualization"""
        pos = component['position']
        properties = component['properties']
        
        # Calculate real-time coverage at receiver location
        coverage_val = self._get_coverage_at_point(pos[0], pos[1])
        interference_val = self._get_interference_at_point(pos[0], pos[1])
        
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Sensitivity: {properties['sensitivity']}dBm<br>"
            f"FOV: {properties['fov']}°<br>"
            f"Active Area: {properties['active_area']*1e4:.2f}cm²<br>"
            f"Received Power: {coverage_val:.1f}W<br>"
            f"Interference Level: {interference_val:.1f}"
        )

        marker_color = 'blue' if not selected else 'royalblue'
        marker_line_width = 2 if not selected else 4

        fig.add_trace(go.Scatter(
            x=[pos[0]],
            y=[pos[1]],
            mode='markers',
            marker=dict(
                symbol='square',
                size=10,
                color=marker_color,
                line=dict(color='darkblue', width=marker_line_width)
            ),
            name=f"Receiver {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))

    def _get_coverage_at_point(self, x, y):
        """Calculate coverage value at a specific point"""
        total_coverage = 0
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    total_coverage += power * (1 - distance/radius)
        return total_coverage

    def _get_interference_at_point(self, x, y):
        """Calculate interference level at a specific point"""
        interfering_sources = 0
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    interfering_sources += 1
        return max(0, interfering_sources - 1)  # Subtract 1 to show only interfering sources
