import json
import numpy as np

def export_configuration(floor_plan, components, coverage_analysis):
    """Export VLC network configuration to JSON format"""
    config = {
        'floor_plan': {
            'width': floor_plan['width'],
            'height': floor_plan['height'],
            'type': floor_plan['type']
        },
        'components': [
            {
                'id': comp['id'],
                'type': comp['type'],
                'position': comp['position'],
                'properties': comp['properties']
            }
            for comp in components
        ],
        'analysis': {
            'coverage_percentage': float(coverage_analysis['coverage_percentage']),
            'interference_points': int(coverage_analysis['interference_points'])
        }
    }
    
    return json.dumps(config, indent=2)
