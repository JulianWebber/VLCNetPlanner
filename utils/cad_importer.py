import ezdxf
import numpy as np
import base64
from io import BytesIO
import svgwrite

def convert_dxf_to_svg(dxf_content):
    """Convert DXF content to SVG format"""
    try:
        # Read DXF from binary content
        dxf = ezdxf.read(BytesIO(dxf_content))
        
        # Get modelspace
        msp = dxf.modelspace()
        
        # Get bounds of the drawing
        bounds = get_drawing_bounds(msp)
        if not bounds:
            raise ValueError("Empty or invalid DXF file")
            
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y
        
        # Create SVG drawing with padding
        padding = 10
        dwg = svgwrite.Drawing(size=(width + 2*padding, height + 2*padding))
        
        # Add a white background
        dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='white'))
        
        # Create a group for the floor plan with coordinate transformation
        group = dwg.g(transform=f'translate({padding-min_x},{padding-min_y})')
        
        # Convert DXF entities to SVG
        for entity in msp:
            if entity.dxftype() == 'LINE':
                group.add(dwg.line(
                    start=(entity.dxf.start[0], entity.dxf.start[1]),
                    end=(entity.dxf.end[0], entity.dxf.end[1]),
                    stroke='black',
                    stroke_width=1
                ))
            elif entity.dxftype() == 'CIRCLE':
                group.add(dwg.circle(
                    center=(entity.dxf.center[0], entity.dxf.center[1]),
                    r=entity.dxf.radius,
                    stroke='black',
                    stroke_width=1,
                    fill='none'
                ))
            elif entity.dxftype() == 'ARC':
                path = create_arc_path(entity)
                if path:
                    group.add(dwg.path(d=path, stroke='black', stroke_width=1, fill='none'))
        
        dwg.add(group)
        
        # Convert to string
        svg_output = BytesIO()
        dwg.write(svg_output)
        
        return {
            'content': base64.b64encode(svg_output.getvalue()).decode(),
            'width': float(width),
            'height': float(height)
        }
        
    except Exception as e:
        raise ValueError(f"Error converting DXF to SVG: {str(e)}")

def get_drawing_bounds(modelspace):
    """Get the bounds of the DXF drawing"""
    bounds = None
    for entity in modelspace:
        if hasattr(entity, 'get_points'):
            points = entity.get_points()
            for point in points:
                if bounds is None:
                    bounds = [point[0], point[1], point[0], point[1]]
                else:
                    bounds[0] = min(bounds[0], point[0])  # min_x
                    bounds[1] = min(bounds[1], point[1])  # min_y
                    bounds[2] = max(bounds[2], point[0])  # max_x
                    bounds[3] = max(bounds[3], point[1])  # max_y
    return bounds

def create_arc_path(arc):
    """Create SVG path for an arc entity"""
    try:
        center = arc.dxf.center
        radius = arc.dxf.radius
        start_angle = np.radians(arc.dxf.start_angle)
        end_angle = np.radians(arc.dxf.end_angle)
        
        # Calculate start and end points
        start_x = center[0] + radius * np.cos(start_angle)
        start_y = center[1] + radius * np.sin(start_angle)
        end_x = center[0] + radius * np.cos(end_angle)
        end_y = center[1] + radius * np.sin(end_angle)
        
        # Determine if arc is larger than 180 degrees
        large_arc = abs(end_angle - start_angle) > np.pi
        
        return (f'M {start_x},{start_y} '
                f'A {radius},{radius} 0 {int(large_arc)},1 {end_x},{end_y}')
    except:
        return None
