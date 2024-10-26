import numpy as np

def analyze_coverage(floor_plan, components):
    """Analyze coverage and interference of VLC network"""
    # Create grid for analysis
    grid_resolution = 0.1  # 10cm resolution
    x = np.arange(0, floor_plan['width'], grid_resolution)
    y = np.arange(0, floor_plan['height'], grid_resolution)
    xx, yy = np.meshgrid(x, y)
    
    coverage_map = np.zeros_like(xx)
    interference_map = np.zeros_like(xx)
    
    # Calculate coverage for each light source
    light_sources = [c for c in components if c['type'] == "Light Source"]
    for ls in light_sources:
        pos = ls['position']
        radius = ls['properties']['coverage_radius']
        
        distance = np.sqrt((xx - pos[0])**2 + (yy - pos[1])**2)
        coverage = (distance <= radius).astype(float)
        
        coverage_map += coverage
        interference_map += (coverage_map > 1).astype(float)
    
    # Calculate metrics
    total_points = xx.size
    covered_points = np.sum(coverage_map > 0)
    interference_points = np.sum(interference_map > 0)
    
    return {
        'coverage_percentage': (covered_points / total_points) * 100,
        'interference_points': int(interference_points),
        'coverage_map': coverage_map,
        'interference_map': interference_map
    }
