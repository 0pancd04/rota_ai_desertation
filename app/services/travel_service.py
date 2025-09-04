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
        self._cache = {}
        # Region/country hints to improve geocoding
        self.default_region = os.getenv("GOOGLE_MAPS_REGION", "uk")
        self.default_country = os.getenv("GOOGLE_MAPS_COUNTRY", "United Kingdom")
        # Fast estimation mode for bulk scheduling
        self.fast_scheduler = os.getenv("FAST_SCHEDULER", "true").strip().lower() in ("1","true","yes","y")

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

    def _normalize_address(self, address: str) -> str:
        """Normalize address string; append country if missing. Return '' if unusable."""
        if not address:
            return ""
        addr = address.strip().strip(',')
        # Minimal validity check
        if len(addr) < 3:
            return ""
        # If no country hint present, append default country
        lower_addr = addr.lower()
        if self.default_country.lower() not in lower_addr:
            addr = f"{addr}, {self.default_country}"
        return addr

    def calculate_travel_time(self, origin: str, destination: str, mode: str = "driving") -> int:
        """Calculate travel time in minutes using Distance Matrix, with Directions fallback."""
        if not self.client or self.fast_scheduler:
            return self._estimate_travel_time(origin, destination, mode)
        
        # If API is available and not in fast mode
        try:
            api_mode = self._map_transport_mode(mode)
            now = datetime.now()

            # Normalize inputs
            norm_origin = self._normalize_address(origin)
            norm_destination = self._normalize_address(destination)
            if not norm_origin or not norm_destination:
                return self._estimate_travel_time(origin, destination, mode)
            if norm_origin == norm_destination:
                return 0

            # Prefer Distance Matrix for robustness
            dm = self.client.distance_matrix(origins=[norm_origin], destinations=[norm_destination], mode=api_mode, departure_time=now, region=self.default_region)
            if dm and dm.get('rows') and dm['rows'][0].get('elements'):
                el = dm['rows'][0]['elements'][0]
                if el.get('status') == 'OK' and el.get('duration'):
                    return int(el['duration']['value'] / 60)

            # Fallback to Directions API
            directions = self.client.directions(norm_origin, norm_destination, mode=api_mode, departure_time=now, region=self.default_region)
            if directions and directions[0].get('legs'):
                duration = directions[0]['legs'][0]['duration']['value']
                return int(duration / 60)

            return self._estimate_travel_time(origin, destination, mode)
        except Exception as e:
            # Reduce log noise but keep visibility
            logger.warning(f"Error calculating travel time: {str(e)}")
            return self._estimate_travel_time(origin, destination, mode)

    def _estimate_travel_time(self, origin: str, destination: str, mode: str = "driving") -> int:
        """Heuristic travel time estimate in minutes (no external calls)."""
        try:
            if not origin or not destination:
                base = 15
            else:
                o = origin.strip().upper()
                d = destination.strip().upper()
                if o == d:
                    base = 0
                else:
                    # Extract last token that looks like a postcode-ish chunk
                    def _pc(s: str) -> str:
                        parts = [p for p in s.replace(',', ' ').split() if any(ch.isdigit() for ch in p)]
                        return parts[-1] if parts else ""
                    po, pd = _pc(o).replace(" ", ""), _pc(d).replace(" ", "")
                    if po and pd and po == pd:
                        base = 6
                    elif po and pd and po[:2] == pd[:2]:
                        base = 10
                    else:
                        base = 18
            m = self._map_transport_mode(mode)
            if m == "walking":
                base += 10
            elif m == "bicycling":
                base += 5
            # clamp
            return max(1, min(base, 60))
        except Exception:
            return 15
            return 15

        try:
            api_mode = self._map_transport_mode(mode)
            now = datetime.now()

            # Normalize inputs
            norm_origin = self._normalize_address(origin)
            norm_destination = self._normalize_address(destination)
            if not norm_origin or not norm_destination:
                return 15
            if norm_origin == norm_destination:
                return 0

            # Prefer Distance Matrix for robustness
            dm = self.client.distance_matrix(origins=[norm_origin], destinations=[norm_destination], mode=api_mode, departure_time=now, region=self.default_region)
            if dm and dm.get('rows') and dm['rows'][0].get('elements'):
                el = dm['rows'][0]['elements'][0]
                if el.get('status') == 'OK' and el.get('duration'):
                    return int(el['duration']['value'] / 60)

            # Fallback to Directions API
            directions = self.client.directions(norm_origin, norm_destination, mode=api_mode, departure_time=now, region=self.default_region)
            if directions and directions[0].get('legs'):
                duration = directions[0]['legs'][0]['duration']['value']
                return int(duration / 60)

            return 15
        except Exception as e:
            # Reduce log noise but keep visibility
            logger.warning(f"Error calculating travel time: {str(e)}")
            return 15 

    def get_travel_time(self, origin: str, destination: str, mode: str = "driving", use_api: bool = True) -> int:
        """Cached travel time retrieval. When use_api is False or fast_scheduler is True, use heuristic."""
        try:
            api_mode = self._map_transport_mode(mode)
            fast = (not use_api) or self.fast_scheduler or (not self.client)
            key = (origin.strip().lower(), destination.strip().lower(), api_mode, 'fast' if fast else 'api')
            if key in self._cache:
                return self._cache[key]
            if fast:
                minutes = self._estimate_travel_time(origin, destination, api_mode)
            else:
                minutes = self.calculate_travel_time(origin, destination, api_mode)
            # Clamp to reasonable bounds
            minutes = max(1, min(minutes, 180))
            self._cache[key] = minutes
            return minutes
        except Exception as e:
            logger.error(f"Error in get_travel_time: {e}")
            return 15

    def check_connectivity(self) -> dict:
        """Ping Google Maps APIs to verify connectivity and credentials."""
        if not self.client:
            return {"available": False, "reason": "GOOGLE_MAPS_API_KEY not configured"}
        try:
            origin = self._normalize_address("London, SW1A 1AA")
            dest = self._normalize_address("London, SW1A 1AA")
            dm = self.client.distance_matrix(origins=[origin], destinations=[dest], mode="driving", region=self.default_region)
            status = dm.get('rows', [{}])[0].get('elements', [{}])[0].get('status')
            if status == 'OK':
                return {"available": True, "reason": "OK"}
            # Fallback to directions
            directions = self.client.directions(origin, dest, mode="driving", region=self.default_region)
            if directions and directions[0].get('legs'):
                return {"available": True, "reason": "Directions OK"}
            return {"available": False, "reason": status or "Unknown"}
        except Exception as e:
            return {"available": False, "reason": str(e)}