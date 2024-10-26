import json
import numpy as np

def export_configuration(floor_plans, components, coverage_analysis):
    """Export VLC network configuration to JSON format"""
    config = {
        'floor_plans': {
            level: {
                'width': floor_data['width'],
                'height': floor_data['height'],
                'type': floor_data['type'],
                'ceiling_height': floor_data.get('ceiling_height', 3.0)
            }
            for level, floor_data in floor_plans.items()
        },
        'components': [
            {
                'id': comp['id'],
                'type': comp['type'],
                'position': comp['position'],
                'floor_level': comp.get('floor_level', 0),
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
