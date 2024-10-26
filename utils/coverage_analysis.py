import numpy as np

def analyze_coverage(floor_plan, components):
    """Analyze coverage and interference of VLC network with detailed modeling"""
    # Create grid for analysis
    grid_resolution = 0.1  # 10cm resolution
    x = np.arange(0, floor_plan['width'], grid_resolution)
    y = np.arange(0, floor_plan['height'], grid_resolution)
    xx, yy = np.meshgrid(x, y)
    
    coverage_map = np.zeros_like(xx)
    interference_map = np.zeros_like(xx)
    sinr_map = np.zeros_like(xx)
    
    # System parameters
    noise_power = 1e-9  # Thermal noise power in W/m²
    responsivity = 0.5  # Photodetector responsivity
    reflection_coeff = 0.3  # Surface reflection coefficient
    
    # Calculate direct and reflected power for each light source
    light_sources = [c for c in components if c['type'] == "Light Source"]
    receivers = [c for c in components if c['type'] == "Receiver"]
    
    for point_y in range(len(y)):
        for point_x in range(len(x)):
            point_pos = np.array([x[point_x], y[point_y]])
            total_signal = 0
            total_interference = 0
            
            for ls in light_sources:
                # Direct path calculations
                pos = np.array(ls['position'])
                distance = np.linalg.norm(point_pos - pos)
                
                if distance <= ls['properties']['coverage_radius']:
                    # Calculate incidence angle
                    incidence_angle = np.arctan2(distance, 2.0)  # Assuming 2m height
                    
                    # Lambertian radiation pattern
                    m = -np.log(2) / np.log(np.cos(np.radians(ls['properties']['beam_angle']/2)))
                    lambertian = (m + 1) / (2 * np.pi) * np.power(np.cos(incidence_angle), m)
                    
                    # Direct path power
                    direct_power = (ls['properties']['power'] * lambertian * 
                                  np.exp(-distance/ls['properties']['coverage_radius']))
                    
                    # Wavelength-specific attenuation
                    wavelength = ls['properties']['wavelength']
                    attenuation = calculate_wavelength_attenuation(wavelength)
                    direct_power *= attenuation
                    
                    # Calculate multipath (first-order reflections)
                    reflected_power = calculate_reflected_power(
                        ls, point_pos, floor_plan, reflection_coeff, wavelength
                    )
                    
                    total_signal += direct_power + reflected_power
                    
                    # Calculate interference based on wavelength overlap
                    for other_ls in light_sources:
                        if other_ls != ls:
                            wavelength_overlap = calculate_wavelength_overlap(
                                wavelength, other_ls['properties']['wavelength']
                            )
                            if wavelength_overlap > 0:
                                other_pos = np.array(other_ls['position'])
                                other_distance = np.linalg.norm(point_pos - other_pos)
                                if other_distance <= other_ls['properties']['coverage_radius']:
                                    interference_power = (other_ls['properties']['power'] * 
                                                       wavelength_overlap * 
                                                       np.exp(-other_distance/other_ls['properties']['coverage_radius']))
                                    total_interference += interference_power
            
            # Calculate SINR
            if total_signal > 0:
                sinr = total_signal / (total_interference + noise_power)
                sinr_map[point_y, point_x] = 10 * np.log10(sinr)  # Convert to dB
            
            coverage_map[point_y, point_x] = total_signal
            interference_map[point_y, point_x] = total_interference
    
    # Calculate metrics
    total_points = xx.size
    covered_points = np.sum(coverage_map > noise_power)
    interference_points = np.sum(interference_map > 0.1 * coverage_map)
    avg_sinr = np.mean(sinr_map[sinr_map != 0])
    
    return {
        'coverage_percentage': (covered_points / total_points) * 100,
        'interference_points': int(interference_points),
        'coverage_map': coverage_map,
        'interference_map': interference_map,
        'sinr_map': sinr_map,
        'average_sinr': float(avg_sinr),
        'min_sinr': float(np.min(sinr_map[sinr_map != 0])),
        'max_sinr': float(np.max(sinr_map))
    }

def calculate_wavelength_attenuation(wavelength):
    """Calculate atmospheric attenuation based on wavelength"""
    # Simplified model based on wavelength
    if 380 <= wavelength <= 780:
        # Visible light spectrum
        # Maximum transmission around 550nm (green)
        return np.exp(-0.1 * abs(wavelength - 550) / 230)
    return 0.5  # Default attenuation for other wavelengths

def calculate_wavelength_overlap(wavelength1, wavelength2):
    """Calculate interference overlap between two wavelengths"""
    # Simplified gaussian model for spectral overlap
    sigma = 15  # nm (spectral width)
    overlap = np.exp(-0.5 * ((wavelength1 - wavelength2) / sigma) ** 2)
    return overlap

def calculate_reflected_power(light_source, point_pos, floor_plan, reflection_coeff, wavelength):
    """Calculate reflected power contributions"""
    total_reflected = 0
    pos = np.array(light_source['position'])
    power = light_source['properties']['power']
    
    # Consider reflections from walls
    wall_points = [
        (pos[0], 0),           # Bottom wall
        (pos[0], floor_plan['height']),  # Top wall
        (0, pos[1]),           # Left wall
        (floor_plan['width'], pos[1])    # Right wall
    ]
    
    for wall_point in wall_points:
        # Calculate reflection angle and distance
        incident_vec = np.array(wall_point) - pos
        reflected_vec = np.array(point_pos) - np.array(wall_point)
        
        incident_distance = np.linalg.norm(incident_vec)
        reflected_distance = np.linalg.norm(reflected_vec)
        
        if (incident_distance <= light_source['properties']['coverage_radius'] and 
            reflected_distance <= light_source['properties']['coverage_radius']):
            
            # Calculate reflection angle
            incident_angle = np.arccos(np.clip(np.dot(incident_vec, np.array([0, 1])) / 
                                             incident_distance, -1.0, 1.0))
            
            # Calculate reflected power using Phong reflection model
            reflected_power = (power * reflection_coeff * 
                             np.cos(incident_angle) / (incident_distance * reflected_distance))
            
            # Add wavelength-dependent attenuation
            reflected_power *= calculate_wavelength_attenuation(wavelength)
            
            total_reflected += reflected_power
    
    return total_reflected
