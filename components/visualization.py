import plotly.graph_objects as go
import numpy as np
import streamlit as st

class NetworkVisualizer:
    def __init__(self, floor_plans, components):
        self.floor_plans = floor_plans if isinstance(floor_plans, dict) else {0: floor_plans}
        self.components = components
        self.view_3d = False

    def plot(self):
        """Create an interactive plot of the VLC network"""
        # Initialize undo/redo history if not exists
        if 'component_history' not in st.session_state:
            st.session_state.component_history = [self.components.copy()]
            st.session_state.history_index = 0

        if self.view_3d:
            return self._plot_3d()
        else:
            return self._plot_2d()

    def _plot_3d(self):
        """Create 3D visualization of the VLC network"""
        fig = go.Figure()

        # Add floor planes for each level
        for level, floor_plan in self.floor_plans.items():
            base_height = level * 3.0  # 3 meters per floor
            
            # Add floor surface
            vertices = [
                [0, 0, base_height],
                [floor_plan['width'], 0, base_height],
                [floor_plan['width'], floor_plan['height'], base_height],
                [0, floor_plan['height'], base_height]
            ]
            i = [0, 0, 0]
            j = [1, 2, 3]
            k = [2, 3, 1]

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
            base_height = floor_level * 3.0  # 3 meters per floor
            
            if component['type'] == "Light Source":
                self._add_light_source_3d(fig, component, base_height)
            else:
                self._add_receiver_3d(fig, component, base_height)

        fig.update_layout(
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Height (m)",
                zaxis_title="Level Height (m)",
                aspectmode='data'
            ),
            showlegend=True,
            width=800,
            height=600
        )

        return fig

    def _plot_2d(self):
        """Create 2D visualization for current floor level"""
        current_floor = st.session_state.get('current_floor_level', 0)
        floor_plan = self.floor_plans.get(current_floor, self.floor_plans[0])
        
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[0, floor_plan['width'], floor_plan['width'], 0, 0],
            y=[0, 0, floor_plan['height'], floor_plan['height'], 0],
            mode='lines',
            line=dict(color='black'),
            name=f'Floor {current_floor}'
        ))

        coverage_map, interference_map = self._calculate_coverage_interference(current_floor)

        x = np.linspace(0, floor_plan['width'], 50)
        y = np.linspace(0, floor_plan['height'], 50)
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

        selected_id = st.session_state.get('selected_component', None)
        for component in self.components:
            if component.get('floor_level', 0) == current_floor:
                if component['type'] == "Light Source":
                    self._add_light_source(fig, component, selected=component['id'] == selected_id)
                else:
                    self._add_receiver(fig, component, selected=component['id'] == selected_id)

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
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="Drag Mode",
                         method="relayout",
                         args=[{"dragmode": "dragopenpath"}]),
                    dict(label="Select Mode",
                         method="relayout",
                         args=[{"dragmode": "select"}]),
                    dict(label="Zoom Mode",
                         method="relayout",
                         args=[{"dragmode": "zoom"}])
                ]
            )]
        )

        return fig

    def _add_light_source_3d(self, fig, component, base_height):
        pos = component['position']
        properties = component['properties']
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°"
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

    def _calculate_coverage_interference(self, current_floor):
        floor_plan = self.floor_plans.get(current_floor, self.floor_plans[0])
        x = np.linspace(0, floor_plan['width'], 50)
        y = np.linspace(0, floor_plan['height'], 50)
        xx, yy = np.meshgrid(x, y)
        
        coverage_map = np.zeros_like(xx)
        interference_map = np.zeros_like(xx)
        
        floor_attenuation = 30  # dB per floor
        reflection_coefficient = 0.3
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                comp_floor = component.get('floor_level', 0)
                
                floor_diff = abs(current_floor - comp_floor)
                attenuation = 10 ** (-floor_attenuation * floor_diff / 10) if floor_diff > 0 else 1
                
                distance = np.sqrt((xx - pos[0])**2 + (yy - pos[1])**2)
                coverage = np.where(distance <= radius,
                                   power * attenuation * (1 - distance/radius),
                                   0)
                
                wall_reflections = [
                    (pos[0], -pos[1]),
                    (pos[0], 2*floor_plan['height'] - pos[1]),
                    (-pos[0], pos[1]),
                    (2*floor_plan['width'] - pos[0], pos[1])
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((xx - refl_pos[0])**2 + (yy - refl_pos[1])**2)
                    refl_coverage = np.where(refl_distance <= radius,
                                            power * attenuation * reflection_coefficient * (1 - refl_distance/radius),
                                            0)
                    coverage += refl_coverage
                
                coverage_map += coverage
                interference_map += (coverage > 0).astype(float)
        
        return coverage_map, interference_map - 1

    def _add_light_source(self, fig, component, selected=False):
        pos = component['position']
        properties = component['properties']
        
        coverage_val = self._get_coverage_at_point(pos[0], pos[1], component.get('floor_level', 0))
        interference_val = self._get_interference_at_point(pos[0], pos[1], component.get('floor_level', 0))
        
        hover_text = (
            f"Light Source {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Power: {properties['power']}W<br>"
            f"Beam Angle: {properties['beam_angle']}°<br>"
            f"Coverage Level: {coverage_val:.1f}<br>"
            f"Interference Level: {interference_val:.1f}"
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
            customdata=[component['id']]
        ))

    def _add_receiver(self, fig, component, selected=False):
        pos = component['position']
        properties = component['properties']
        
        coverage_val = self._get_coverage_at_point(pos[0], pos[1], component.get('floor_level', 0))
        interference_val = self._get_interference_at_point(pos[0], pos[1], component.get('floor_level', 0))
        
        hover_text = (
            f"Receiver {component['id']}<br>"
            f"Floor Level: {component.get('floor_level', 0)}<br>"
            f"Sensitivity: {properties['sensitivity']}dBm<br>"
            f"FOV: {properties['fov']}°<br>"
            f"Received Power: {coverage_val:.1f}W<br>"
            f"Interference Level: {interference_val:.1f}"
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
            customdata=[component['id']]
        ))

    def _add_drag_listeners(self, trace):
        trace.on_click(self._handle_click)
        trace.on_drag(self._handle_drag)
        return trace

    def _handle_click(self, trace, points, state):
        if points.point_inds:
            point_index = points.point_inds[0]
            component_id = trace.customdata[point_index]
            st.session_state.selected_component = component_id

    def _handle_drag(self, trace, points, state):
        if points.point_inds:
            point_index = points.point_inds[0]
            component_id = trace.customdata[point_index]
            new_x = points.xs[point_index]
            new_y = points.ys[point_index]
            
            for component in self.components:
                if component['id'] == component_id:
                    component['position'] = [new_x, new_y]
                    self._add_to_history()
                    break

    def _add_to_history(self):
        if st.session_state.history_index < len(st.session_state.component_history) - 1:
            st.session_state.component_history = st.session_state.component_history[:st.session_state.history_index + 1]
        
        st.session_state.component_history.append(self.components.copy())
        st.session_state.history_index = len(st.session_state.component_history) - 1

    def undo(self):
        if st.session_state.history_index > 0:
            st.session_state.history_index -= 1
            self.components = st.session_state.component_history[st.session_state.history_index].copy()

    def redo(self):
        if st.session_state.history_index < len(st.session_state.component_history) - 1:
            st.session_state.history_index += 1
            self.components = st.session_state.component_history[st.session_state.history_index].copy()

    def _get_coverage_at_point(self, x, y, floor_level):
        total_coverage = 0
        floor_attenuation = 30
        reflection_coefficient = 0.3
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                power = component['properties']['power']
                comp_floor = component.get('floor_level', 0)
                
                floor_diff = abs(floor_level - comp_floor)
                attenuation = 10 ** (-floor_attenuation * floor_diff / 10) if floor_diff > 0 else 1
                
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    total_coverage += power * attenuation * (1 - distance/radius)
                
                wall_reflections = [
                    (pos[0], -pos[1]),
                    (pos[0], 2*self.floor_plans[floor_level]['height'] - pos[1]),
                    (-pos[0], pos[1]),
                    (2*self.floor_plans[floor_level]['width'] - pos[0], pos[1])
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((x - refl_pos[0])**2 + (y - refl_pos[1])**2)
                    if refl_distance <= radius:
                        total_coverage += power * attenuation * reflection_coefficient * (1 - refl_distance/radius)
        
        return total_coverage

    def _get_interference_at_point(self, x, y, floor_level):
        interfering_sources = 0
        floor_attenuation = 30
        
        for component in self.components:
            if component['type'] == "Light Source":
                pos = component['position']
                radius = component['properties']['coverage_radius']
                comp_floor = component.get('floor_level', 0)
                
                floor_diff = abs(floor_level - comp_floor)
                attenuation = 10 ** (-floor_attenuation * floor_diff / 10) if floor_diff > 0 else 1
                
                distance = np.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if distance <= radius:
                    interfering_sources += attenuation
                
                wall_reflections = [
                    (pos[0], -pos[1]),
                    (pos[0], 2*self.floor_plans[floor_level]['height'] - pos[1]),
                    (-pos[0], pos[1]),
                    (2*self.floor_plans[floor_level]['width'] - pos[0], pos[1])
                ]
                
                for refl_pos in wall_reflections:
                    refl_distance = np.sqrt((x - refl_pos[0])**2 + (y - refl_pos[1])**2)
                    if refl_distance <= radius:
                        interfering_sources += 0.3 * attenuation
        
        return max(0, interfering_sources - 1)
