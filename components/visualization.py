import plotly.graph_objects as go
import numpy as np

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

        # Update layout
        fig.update_layout(
            showlegend=True,
            hovermode='closest',
            dragmode='pan',
            plot_bgcolor='white',
            width=800,
            height=600,
            xaxis=dict(
                range=[-1, self.floor_plan['width'] + 1],
                showgrid=True
            ),
            yaxis=dict(
                range=[-1, self.floor_plan['height'] + 1],
                showgrid=True
            )
        )

        return fig

    def _add_light_source(self, fig, component):
        """Add light source visualization"""
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
            name=f"Light Source {component['id']}"
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
            name=f"Coverage LS {component['id']}"
        ))

    def _add_receiver(self, fig, component):
        """Add receiver visualization"""
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
            name=f"Receiver {component['id']}"
        ))
