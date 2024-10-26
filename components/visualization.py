import plotly.graph_objects as go
import numpy as np
import streamlit as st

class NetworkVisualizer:
    def __init__(self, floor_plan, components):
        self.floor_plan = floor_plan
        self.components = components

    def plot(self):
        """Create an interactive plot of the VLC network"""
        # Initialize undo/redo history if not exists
        if 'component_history' not in st.session_state:
            st.session_state.component_history = [self.components.copy()]
            st.session_state.history_index = 0

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

        # Add components with drag support
        selected_id = st.session_state.get('selected_component', None)
        for component in self.components:
            if component['type'] == "Light Source":
                self._add_light_source(fig, component, selected=component['id'] == selected_id)
            else:
                self._add_receiver(fig, component, selected=component['id'] == selected_id)

        # Update layout with drag mode
        fig.update_layout(
            showlegend=True,
            hovermode='closest',
            dragmode='drawopenpath',  # Enable drag mode
            plot_bgcolor='white',
            width=800,
            height=600,
            xaxis=dict(
                range=[-1, self.floor_plan['width'] + 1],
                showgrid=True,
                title="Width (meters)",
                constrain="domain"
            ),
            yaxis=dict(
                range=[-1, self.floor_plan['height'] + 1],
                showgrid=True,
                title="Height (meters)",
                scaleanchor="x",
                scaleratio=1
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="Drag Mode",
                         method="relayout",
                         args=[{"dragmode": "drawopenpath"}]),
                    dict(label="Select Mode",
                         method="relayout",
                         args=[{"dragmode": "select"}]),
                    dict(label="Zoom Mode",
                         method="relayout",
                         args=[{"dragmode": "zoom"}])
                ]
            )],
            modebar=dict(
                add=['drawline', 'drawopenpath', 'eraseshape']
            )
        )

        # Add event listeners for drag interactions
        fig.data = [self._add_drag_listeners(trace) for trace in fig.data]
        
        return fig

    def _calculate_coverage_interference(self):
        """Calculate coverage and interference maps with reflections"""
        x = np.linspace(0, self.floor_plan['width'], 50)
        y = np.linspace(0, self.floor_plan['height'], 50)
        xx, yy = np.meshgrid(x, y)
        
        coverage_map = np.zeros_like(xx)
        interference_map = np.zeros_like(xx)
        
        reflection_coefficient = 0.3  # Wall reflection coefficient
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                
                # Direct path coverage
                distance = np.sqrt((xx - pos[0])**2 + (yy - pos[1])**2)
                direct_coverage = np.where(distance <= radius, 
                                         power * (1 - distance/radius), 
                                         0)
                
                # Add first-order reflections from walls
                wall_reflections = [
                    (pos[0], -pos[1]),  # Bottom wall
                    (pos[0], 2*self.floor_plan['height'] - pos[1]),  # Top wall
                    (-pos[0], pos[1]),  # Left wall
                    (2*self.floor_plan['width'] - pos[0], pos[1])  # Right wall
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((xx - refl_pos[0])**2 + (yy - refl_pos[1])**2)
                    refl_coverage = np.where(refl_distance <= radius,
                                           power * reflection_coefficient * (1 - refl_distance/radius),
                                           0)
                    direct_coverage += refl_coverage
                
                coverage_map += direct_coverage
                interference_map += (direct_coverage > 0).astype(float)
        
        return coverage_map, interference_map - 1

    def _add_light_source(self, fig, component, selected=False):
        """Add light source visualization with drag support"""
        pos = component['position']
        properties = component['properties']
        
        coverage_val = self._get_coverage_at_point(pos[0], pos[1])
        interference_val = self._get_interference_at_point(pos[0], pos[1])
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°<br>"
            f"Wavelength: {properties['wavelength']}nm<br>"
            f"Coverage Radius: {properties['coverage_radius']}m<br>"
            f"Coverage Level: {coverage_val:.1f}<br>"
            f"Interference Level: {interference_val:.1f}<br>"
            f"<i>Drag to reposition</i>"
        )

        marker_color = 'yellow' if not selected else 'gold'
        marker_line_width = 2 if not selected else 4

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
            hoverinfo='text',
            customdata=[component['id']],
            dragmode=True
        ))

    def _add_receiver(self, fig, component, selected=False):
        """Add receiver visualization with drag support"""
        pos = component['position']
        properties = component['properties']
        
        coverage_val = self._get_coverage_at_point(pos[0], pos[1])
        interference_val = self._get_interference_at_point(pos[0], pos[1])
        
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Sensitivity: {properties['sensitivity']}dBm<br>"
            f"FOV: {properties['fov']}°<br>"
            f"Active Area: {properties['active_area']*1e4:.2f}cm²<br>"
            f"Received Power: {coverage_val:.1f}W<br>"
            f"Interference Level: {interference_val:.1f}<br>"
            f"<i>Drag to reposition</i>"
        )

        marker_color = 'blue' if not selected else 'royalblue'
        marker_line_width = 2 if not selected else 4

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
            hoverinfo='text',
            customdata=[component['id']],
            dragmode=True
        ))

    def _add_drag_listeners(self, trace):
        """Add drag event listeners to update component positions"""
        trace.on_click(self._handle_click)
        trace.on_drag(self._handle_drag)
        return trace

    def _handle_click(self, trace, points, state):
        """Handle click events for component selection"""
        if points.point_inds:
            point_index = points.point_inds[0]
            component_id = trace.customdata[point_index]
            st.session_state.selected_component = component_id

    def _handle_drag(self, trace, points, state):
        """Handle drag events to update component positions"""
        if points.point_inds:
            point_index = points.point_inds[0]
            component_id = trace.customdata[point_index]
            new_x = points.xs[point_index]
            new_y = points.ys[point_index]
            
            # Update component position
            for component in self.components:
                if component['id'] == component_id:
                    old_pos = component['position'].copy()
                    component['position'] = [new_x, new_y]
                    
                    # Add to undo history
                    self._add_to_history()
                    break

    def _add_to_history(self):
        """Add current state to undo history"""
        if st.session_state.history_index < len(st.session_state.component_history) - 1:
            # Remove future states if we're in the middle of the history
            st.session_state.component_history = st.session_state.component_history[:st.session_state.history_index + 1]
        
        st.session_state.component_history.append(self.components.copy())
        st.session_state.history_index = len(st.session_state.component_history) - 1

    def undo(self):
        """Undo last component movement"""
        if st.session_state.history_index > 0:
            st.session_state.history_index -= 1
            self.components = st.session_state.component_history[st.session_state.history_index].copy()

    def redo(self):
        """Redo last undone component movement"""
        if st.session_state.history_index < len(st.session_state.component_history) - 1:
            st.session_state.history_index += 1
            self.components = st.session_state.component_history[st.session_state.history_index].copy()

    def _get_coverage_at_point(self, x, y):
        """Calculate coverage value at a specific point with reflections"""
        total_coverage = 0
        reflection_coefficient = 0.3
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                
                # Direct path
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    total_coverage += power * (1 - distance/radius)
                
                # Wall reflections
                wall_reflections = [
                    (pos[0], -pos[1]),  # Bottom wall
                    (pos[0], 2*self.floor_plan['height'] - pos[1]),  # Top wall
                    (-pos[0], pos[1]),  # Left wall
                    (2*self.floor_plan['width'] - pos[0], pos[1])  # Right wall
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((x - refl_pos[0])**2 + (y - refl_pos[1])**2)
                    if refl_distance <= radius:
                        total_coverage += power * reflection_coefficient * (1 - refl_distance/radius)
        
        return total_coverage

    def _get_interference_at_point(self, x, y):
        """Calculate interference level at a specific point with reflections"""
        interfering_sources = 0
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                
                # Direct path interference
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    interfering_sources += 1
                
                # Wall reflection interference
                wall_reflections = [
                    (pos[0], -pos[1]),  # Bottom wall
                    (pos[0], 2*self.floor_plan['height'] - pos[1]),  # Top wall
                    (-pos[0], pos[1]),  # Left wall
                    (2*self.floor_plan['width'] - pos[0], pos[1])  # Right wall
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((x - refl_pos[0])**2 + (y - refl_pos[1])**2)
                    if refl_distance <= radius:
                        interfering_sources += 0.3  # Reduced interference from reflections
        
        return max(0, interfering_sources - 1)
