import numpy as np
from scipy.optimize import minimize, differential_evolution
import random

class PSOptimizer:
    def __init__(self, n_particles, dimensions, bounds):
        self.n_particles = n_particles
        self.dimensions = dimensions
        self.bounds = bounds
        self.positions = np.random.uniform(
            low=[b[0] for b in bounds],
            high=[b[1] for b in bounds],
            size=(n_particles, dimensions)
        )
        self.velocities = np.zeros((n_particles, dimensions))
        self.best_positions = self.positions.copy()
        self.best_scores = np.full(n_particles, float('inf'))
        self.global_best_position = None
        self.global_best_score = float('inf')

    def update(self, objective_func, w=0.7, c1=1.5, c2=1.5):
        scores = np.array([objective_func(p) for p in self.positions])
        
        # Update personal bests
        improved = scores < self.best_scores
        self.best_positions[improved] = self.positions[improved]
        self.best_scores[improved] = scores[improved]
        
        # Update global best
        min_score_idx = np.argmin(scores)
        if scores[min_score_idx] < self.global_best_score:
            self.global_best_score = scores[min_score_idx]
            self.global_best_position = self.positions[min_score_idx].copy()
        
        # Update velocities and positions
        r1, r2 = np.random.rand(2)
        self.velocities = (w * self.velocities +
                         c1 * r1 * (self.best_positions - self.positions) +
                         c2 * r2 * (self.global_best_position - self.positions))
        
        self.positions += self.velocities
        
        # Enforce bounds
        for i, (low, high) in enumerate(self.bounds):
            self.positions[:, i] = np.clip(self.positions[:, i], low, high)

def optimize_placement(floor_plan, components, optimization_params=None):
    """Advanced optimization of VLC component placement using multi-objective optimization"""
    if optimization_params is None:
        optimization_params = {
            'coverage_weight': 0.4,
            'interference_weight': 0.3,
            'power_weight': 0.3,
            'min_distance': 2.0,  # Minimum distance between components
            'wall_margin': 0.5,   # Minimum distance from walls
            'max_iterations': 100
        }

    def multi_objective_function(positions):
        # Reshape positions into component locations
        locations = positions.reshape(-1, 2)
        
        # Calculate coverage score
        coverage_score = calculate_coverage_score(floor_plan, locations)
        
        # Calculate interference penalty
        interference_penalty = calculate_interference_penalty(locations)
        
        # Calculate power efficiency
        power_efficiency = calculate_power_efficiency(locations, components)
        
        # Calculate wall distance penalty
        wall_penalty = calculate_wall_penalty(locations, floor_plan, optimization_params['wall_margin'])
        
        # Calculate spacing penalty
        spacing_penalty = calculate_spacing_penalty(locations, optimization_params['min_distance'])
        
        # Combine objectives with weights
        total_score = (
            -optimization_params['coverage_weight'] * coverage_score +
            optimization_params['interference_weight'] * interference_penalty +
            optimization_params['power_weight'] * (1 - power_efficiency) +
            5.0 * wall_penalty +  # High weight for wall constraints
            5.0 * spacing_penalty  # High weight for spacing constraints
        )
        
        return total_score

    # Extract initial positions and prepare bounds
    initial_positions = np.array([comp['position'] for comp in components]).flatten()
    bounds = []
    for _ in range(len(components)):
        bounds.extend([
            (optimization_params['wall_margin'], floor_plan['width'] - optimization_params['wall_margin']),
            (optimization_params['wall_margin'], floor_plan['height'] - optimization_params['wall_margin'])
        ])

    # Initialize PSO optimizer
    n_particles = min(20, 4 * len(components))  # Adaptive particle count
    pso = PSOptimizer(n_particles, len(initial_positions), bounds)
    
    # Run PSO optimization
    for _ in range(optimization_params['max_iterations']):
        pso.update(multi_objective_function)
        if pso.global_best_score < -0.95:  # Early stopping if good solution found
            break
    
    # Fine-tune with local search
    result = minimize(
        multi_objective_function,
        pso.global_best_position,
        method='SLSQP',
        bounds=bounds,
        options={'maxiter': 100}
    )
    
    # Update component positions
    optimized_positions = result.x.reshape(-1, 2)
    optimized_components = components.copy()
    for i, comp in enumerate(optimized_components):
        comp['position'] = optimized_positions[i].tolist()
    
    return optimized_components

def calculate_coverage_score(floor_plan, locations):
    """Calculate coverage score with distance-weighted contribution"""
    grid_size = 100
    x = np.linspace(0, floor_plan['width'], grid_size)
    y = np.linspace(0, floor_plan['height'], grid_size)
    xx, yy = np.meshgrid(x, y)
    
    coverage = np.zeros_like(xx)
    for loc in locations:
        distance = np.sqrt((xx - loc[0])**2 + (yy - loc[1])**2)
        coverage += np.exp(-0.5 * (distance / 3.0)**2)  # Gaussian coverage profile
    
    return np.mean(coverage > 0.2)  # Threshold for effective coverage

def calculate_interference_penalty(locations):
    """Calculate interference penalty between components with exponential decay"""
    if len(locations) < 2:
        return 0
    
    penalty = 0
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            distance = np.linalg.norm(locations[i] - locations[j])
            if distance < 2.0:
                penalty += np.exp(-distance)  # Exponential penalty for close components
    
    return penalty

def calculate_power_efficiency(locations, components):
    """Calculate power efficiency based on coverage area per unit power"""
    total_power = sum(comp['properties']['power'] for comp in components 
                     if comp['type'] == "Light Source")
    if total_power == 0:
        return 0
    
    coverage_area = calculate_coverage_score(
        {'width': max(loc[0] for loc in locations) + 3,
         'height': max(loc[1] for loc in locations) + 3},
        locations
    )
    
    return coverage_area / total_power

def calculate_wall_penalty(locations, floor_plan, margin):
    """Calculate penalty for components too close to walls"""
    penalty = 0
    for loc in locations:
        dist_to_walls = min(
            loc[0],  # Distance to left wall
            floor_plan['width'] - loc[0],  # Distance to right wall
            loc[1],  # Distance to bottom wall
            floor_plan['height'] - loc[1]  # Distance to top wall
        )
        if dist_to_walls < margin:
            penalty += (margin - dist_to_walls) ** 2
    return penalty

def calculate_spacing_penalty(locations, min_distance):
    """Calculate penalty for components too close to each other"""
    penalty = 0
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            distance = np.linalg.norm(locations[i] - locations[j])
            if distance < min_distance:
                penalty += (min_distance - distance) ** 2
    return penalty
