import numpy as np
import base64
from io import BytesIO

class FloorPlanManager:
    @staticmethod
    def load_floor_plan(file, floor_level=0):
        """Load and process an uploaded floor plan"""
        try:
            content = file.read()
            return {
                'type': 'uploaded',
                'content': base64.b64encode(content).decode(),
                'width': 20.0,  # Default width in meters
                'height': 15.0,  # Default height in meters
                'floor_level': floor_level,
                'ceiling_height': 3.0  # Default ceiling height in meters
            }
        except Exception as e:
            raise ValueError(f"Error loading floor plan: {str(e)}")

    @staticmethod
    def create_new(width, height, floor_level=0, ceiling_height=3.0):
        """Create a new empty floor plan with given dimensions"""
        return {
            'type': 'empty',
            'width': width,
            'height': height,
            'floor_level': floor_level,
            'ceiling_height': ceiling_height,
            'grid': np.zeros((int(height * 10), int(width * 10)))  # 10cm resolution
        }
    
    @staticmethod
    def get_floor_height(floor_level, floor_plans):
        """Calculate the absolute height of a floor level"""
        height = 0
        for level in range(floor_level):
            if level in floor_plans:
                height += floor_plans[level]['ceiling_height']
        return height
