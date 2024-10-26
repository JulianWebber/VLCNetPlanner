import numpy as np
import base64
from io import BytesIO

class FloorPlanManager:
    @staticmethod
    def load_floor_plan(file):
        """Load and process an uploaded floor plan"""
        try:
            content = file.read()
            return {
                'type': 'uploaded',
                'content': base64.b64encode(content).decode(),
                'width': 20.0,  # Default width in meters
                'height': 15.0  # Default height in meters
            }
        except Exception as e:
            raise ValueError(f"Error loading floor plan: {str(e)}")

    @staticmethod
    def create_new(width, height):
        """Create a new empty floor plan with given dimensions"""
        return {
            'type': 'empty',
            'width': width,
            'height': height,
            'grid': np.zeros((int(height * 10), int(width * 10)))  # 10cm resolution
        }
