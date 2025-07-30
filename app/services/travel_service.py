import os
import googlemaps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TravelService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            logger.warning("Google Maps API key not set. Using default estimates.")
        self.client = googlemaps.Client(key=api_key) if api_key else None

    def _map_transport_mode(self, transport_mode: str) -> str:
        """Map transport mode to Google Maps API mode"""
        mode_mapping = {
            "car": "driving",
            "walking": "walking",
            "bicycle": "bicycling",
            "public transport": "transit",
            "public_transport": "transit",
            "bike": "bicycling"
        }
        return mode_mapping.get(transport_mode.lower(), "driving")

    def calculate_travel_time(self, origin: str, destination: str, mode: str = "driving") -> int:
        """Calculate travel time in minutes"""
        if not self.client:
            # Default estimate
            return 15
        
        try:
            # Map the transport mode to Google Maps API mode
            api_mode = self._map_transport_mode(mode)
            
            now = datetime.now()
            directions = self.client.directions(origin, destination, mode=api_mode, departure_time=now)
            if directions and directions[0]['legs']:
                duration = directions[0]['legs'][0]['duration']['value']  # in seconds
                return int(duration / 60)
            return 15  # Default
        except Exception as e:
            logger.error(f"Error calculating travel time: {str(e)}")
            return 15 