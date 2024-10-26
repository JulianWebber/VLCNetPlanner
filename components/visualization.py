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

        # Add components
        for component in self.components:
            if component['type'] == "Light Source":
                self._add_light_source(fig, component)
            else:
                self._add_receiver(fig, component)

        # Update layout with drag mode and better tooltips
        fig.update_layout(
            showlegend=True,
            hovermode='closest',
            dragmode='drag',  # Enable drag mode
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
            # Add modebar buttons for drag interactions
            modebar=dict(
                add=['drawopenpath', 'eraseshape']
            )
        )

        # Add drag update callback
        fig.data = [self._add_drag_callback(trace) for trace in fig.data]
        
        return fig

    def _add_light_source(self, fig, component):
        """Add light source visualization"""
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Power: {component['properties']['power']}W<br>"
            f"Beam Angle: {component['properties']['beam_angle']}°<br>"
            f"Wavelength: {component['properties']['wavelength']}nm<br>"
            f"Coverage: {component['properties']['coverage_radius']}m"
        )

        fig.add_trace(go.Scatter(
            x=[component['position'][0]],
            y=[component['position'][1]],
            mode='markers',
            marker=dict(
                symbol='star',
                size=15,
                color='yellow',
                line=dict(color='orange', width=2)
            ),
            name=f"Light Source {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))

        # Add coverage area
        radius = component['properties']['coverage_radius']
        theta = np.linspace(0, 2*np.pi, 100)
        x = component['position'][0] + radius * np.cos(theta)
        y = component['position'][1] + radius * np.sin(theta)
        
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines',
            line=dict(color='rgba(255, 255, 0, 0.2)'),
            fill='toself',
            name=f"Coverage LS {component['id']}",
            hoverinfo='skip'
        ))

    def _add_receiver(self, fig, component):
        """Add receiver visualization"""
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Sensitivity: {component['properties']['sensitivity']}dBm<br>"
            f"FOV: {component['properties']['fov']}°<br>"
            f"Active Area: {component['properties']['active_area']*1e4:.2f}cm²"
        )

        fig.add_trace(go.Scatter(
            x=[component['position'][0]],
            y=[component['position'][1]],
            mode='markers',
            marker=dict(
                symbol='square',
                size=10,
                color='blue',
                line=dict(color='darkblue', width=2)
            ),
            name=f"Receiver {component['id']}",
            hovertext=hover_text,
            hoverinfo='text'
        ))

    def _add_drag_callback(self, trace):
        """Add drag callback to update component positions"""
        trace.update(
            customdata=np.column_stack([
                np.arange(len(trace.x)),  # Index for identification
                trace.x,
                trace.y
            ])
        )
        return trace

    def update_component_position(self, component_id, new_x, new_y):
        """Update component position after drag"""
        for component in self.components:
            if component['id'] == component_id:
                component['position'] = [new_x, new_y]
                break
