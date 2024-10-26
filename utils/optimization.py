import numpy as np
from scipy.optimize import minimize

def optimize_placement(floor_plan, components):
    """Optimize the placement of VLC components"""
    def objective_function(positions):
        # Reshape positions into component locations
        locations = positions.reshape(-1, 2)
        
        # Calculate coverage score
        coverage_score = calculate_coverage_score(floor_plan, locations)
        
        # Calculate interference penalty
        interference_penalty = calculate_interference_penalty(locations)
        
        return -coverage_score + interference_penalty

    # Extract current positions
    initial_positions = np.array([comp['position'] for comp in components]).flatten()
    
    # Define bounds for optimization
    bounds = [(0, floor_plan['width']) if i % 2 == 0 else (0, floor_plan['height']) 
             for i in range(len(initial_positions))]
    
    # Optimize
    result = minimize(objective_function, initial_positions, bounds=bounds, method='SLSQP')
    
    # Update component positions
    optimized_positions = result.x.reshape(-1, 2)
    optimized_components = components.copy()
    for i, comp in enumerate(optimized_components):
        comp['position'] = optimized_positions[i].tolist()
    
    return optimized_components

def calculate_coverage_score(floor_plan, locations):
    """Calculate coverage score for given component locations"""
    grid_size = 100
    x = np.linspace(0, floor_plan['width'], grid_size)
    y = np.linspace(0, floor_plan['height'], grid_size)
    xx, yy = np.meshgrid(x, y)
    
    coverage = np.zeros_like(xx)
    for loc in locations:
        distance = np.sqrt((xx - loc[0])**2 + (yy - loc[1])**2)
        coverage += (distance < 3.0).astype(float)  # 3.0m coverage radius
    
    return np.mean(coverage > 0)

def calculate_interference_penalty(locations):
    """Calculate interference penalty between components"""
    if len(locations) < 2:
        return 0
    
    penalty = 0
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            distance = np.linalg.norm(locations[i] - locations[j])
            if distance < 2.0:  # Minimum separation distance
                penalty += (2.0 - distance) ** 2
    
    return penalty
