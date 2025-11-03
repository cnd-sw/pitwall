import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OpenF1Client:
    BASE_URL = "https://api.openf1.org/v1"
    
    # Team colors mapping
    TEAM_COLORS = {
        'red bull racing': '#3671C6',
        'ferrari': '#E8002D',
        'mercedes': '#27F4D2',
        'mclaren': '#FF8000',
        'aston martin': '#229971',
        'alpine': '#FF87BC',
        'williams': '#64C4FF',
        'alphatauri': '#5E8FAA',
        'alfa romeo': '#C92D4B',
        'haas f1 team': '#B6BABD',
        'kick sauber': '#52E252',
        'rb': '#6692FF',
        'racing bulls': '#6692FF'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.drivers_cache = {}
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Make GET request to OpenF1 API"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return []
    
    def get_current_session(self) -> Optional[Dict]:
        """Get the current or most recent session"""
        sessions = self._get("sessions", params={
            "date_start>=" : (datetime.utcnow() - timedelta(days=1)).isoformat()
        })
        if sessions:
            # Sort by date and get most recent
            sessions.sort(key=lambda x: x.get('date_start', ''), reverse=True)
            return sessions[0]
        return None
    
    def get_session_info(self, session_key: int) -> Dict:
        """Get detailed session information"""
        sessions = self._get("sessions", params={"session_key": session_key})
        return sessions[0] if sessions else {}
    
    def get_drivers(self, session_key: int) -> List[Dict]:
        """Get all drivers in a session with enhanced info"""
        if session_key in self.drivers_cache:
            return self.drivers_cache[session_key]
        
        drivers = self._get("drivers", params={"session_key": session_key})
        
        # Add team colors
        for driver in drivers:
            team_name = driver.get('team_name', '').lower()
            driver['team_color'] = self.TEAM_COLORS.get(team_name, '#FFFFFF')
        
        self.drivers_cache[session_key] = drivers
        return drivers
    
    def get_driver_info(self, session_key: int, driver_number: int) -> Optional[Dict]:
        """Get specific driver information"""
        drivers = self.get_drivers(session_key)
        for driver in drivers:
            if driver.get('driver_number') == driver_number:
                return driver
        return None
    
    def get_position_data(self, session_key: int) -> List[Dict]:
        """Get position data for all drivers"""
        return self._get("position", params={"session_key": session_key})
    
    def get_latest_positions(self, session_key: int) -> List[Dict]:
        """Get the most recent position for each driver with driver info"""
        positions = self.get_position_data(session_key)
        if not positions:
            return []
        
        # Group by driver and get latest
        driver_positions = {}
        for pos in positions:
            driver_num = pos.get('driver_number')
            if driver_num:
                if driver_num not in driver_positions:
                    driver_positions[driver_num] = pos
                elif pos.get('date', '') > driver_positions[driver_num].get('date', ''):
                    driver_positions[driver_num] = pos
        
        # Add driver info to positions
        drivers = self.get_drivers(session_key)
        for pos in driver_positions.values():
            driver_num = pos.get('driver_number')
            driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
            if driver_info:
                pos['driver_info'] = driver_info
        
        # Sort by position
        result = list(driver_positions.values())
        result.sort(key=lambda x: x.get('position', 999))
        return result
    
    def get_lap_data(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """Get lap times data"""
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        laps = self._get("laps", params=params)
        
        # Add driver info
        if laps:
            drivers = self.get_drivers(session_key)
            for lap in laps:
                driver_num = lap.get('driver_number')
                driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
                if driver_info:
                    lap['driver_info'] = driver_info
        
        return laps
    
    def get_fastest_laps(self, session_key: int, limit: int = 10) -> List[Dict]:
        """Get fastest laps in the session"""
        laps = self.get_lap_data(session_key)
        if not laps:
            return []
        
        # Filter valid laps and sort by lap time
        valid_laps = [lap for lap in laps if lap.get('lap_duration') and lap.get('lap_duration') > 0]
        valid_laps.sort(key=lambda x: x.get('lap_duration', float('inf')))
        
        return valid_laps[:limit]
    
    def get_pit_stops(self, session_key: int) -> List[Dict]:
        """Get all pit stops in the session with driver info"""
        pit_stops = self._get("pit", params={"session_key": session_key})
        
        if pit_stops:
            drivers = self.get_drivers(session_key)
            for stop in pit_stops:
                driver_num = stop.get('driver_number')
                driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
                if driver_info:
                    stop['driver_info'] = driver_info
        
        return pit_stops
    
    def get_race_control_messages(self, session_key: int) -> List[Dict]:
        """Get race control messages (flags, penalties, etc.)"""
        return self._get("race_control", params={"session_key": session_key})
    
    def get_team_radio(self, session_key: int) -> List[Dict]:
        """Get team radio messages with driver info"""
        radio = self._get("team_radio", params={"session_key": session_key})
        
        if radio:
            drivers = self.get_drivers(session_key)
            for msg in radio:
                driver_num = msg.get('driver_number')
                driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
                if driver_info:
                    msg['driver_info'] = driver_info
        
        return radio
    
    def get_weather(self, session_key: int) -> List[Dict]:
        """Get weather data"""
        return self._get("weather", params={"session_key": session_key})
    
    def get_car_data(self, session_key: int, driver_number: int) -> List[Dict]:
        """Get car telemetry data for a specific driver"""
        return self._get("car_data", params={
            "session_key": session_key,
            "driver_number": driver_number
        })
    
    def get_intervals(self, session_key: int) -> List[Dict]:
        """Get time intervals between drivers"""
        return self._get("intervals", params={"session_key": session_key})
    
    def get_stints(self, session_key: int) -> List[Dict]:
        """Get tire stint information with driver info"""
        stints = self._get("stints", params={"session_key": session_key})
        
        if stints:
            drivers = self.get_drivers(session_key)
            for stint in stints:
                driver_num = stint.get('driver_number')
                driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
                if driver_info:
                    stint['driver_info'] = driver_info
        
        return stints
    
    def get_meetings(self, year: Optional[int] = None) -> List[Dict]:
        """Get race weekend meetings (Grand Prix events)"""
        params = {}
        if year:
            params["year"] = year
        else:
            params["year"] = datetime.utcnow().year
        return self._get("meetings", params=params)
    
    def get_sessions_for_meeting(self, meeting_key: int) -> List[Dict]:
        """Get all sessions for a specific meeting (FP1, FP2, Quali, Race, etc.)"""
        return self._get("sessions", params={"meeting_key": meeting_key})
    
    def get_lap_by_lap_data(self, session_key: int) -> Dict:
        """Get comprehensive lap-by-lap data for replay"""
        laps = self.get_lap_data(session_key)
        positions = self.get_position_data(session_key)
        
        # Organize by lap number
        lap_data = {}
        for lap in laps:
            lap_num = lap.get('lap_number')
            if lap_num not in lap_data:
                lap_data[lap_num] = {'laps': [], 'positions': []}
            lap_data[lap_num]['laps'].append(lap)
        
        for pos in positions:
            # Estimate lap number from position data if available
            lap_num = 1  # Default, would need more logic for accurate mapping
            if lap_num in lap_data:
                lap_data[lap_num]['positions'].append(pos)
        
        return lap_data
    
    def calculate_championship_standings(self, year: int) -> Dict:
        """Calculate championship standings from race results"""
        meetings = self.get_meetings(year)
        
        driver_points = {}
        constructor_points = {}
        driver_podiums = {}
        driver_wins = {}
        
        # F1 points system
        points_system = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
            6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
        
        for meeting in meetings:
            sessions = self.get_sessions_for_meeting(meeting['meeting_key'])
            race_session = next((s for s in sessions if s.get('session_name') == 'Race'), None)
            
            if not race_session:
                continue
            
            session_key = race_session['session_key']
            positions = self.get_latest_positions(session_key)
            drivers = self.get_drivers(session_key)
            
            for pos in positions:
                position = pos.get('position')
                driver_num = pos.get('driver_number')
                
                if not position or not driver_num:
                    continue
                
                driver_info = next((d for d in drivers if d.get('driver_number') == driver_num), None)
                if not driver_info:
                    continue
                
                driver_name = driver_info.get('full_name') or driver_info.get('name_acronym')
                team_name = driver_info.get('team_name')
                
                if not driver_name:
                    continue
                
                # Initialize driver
                if driver_name not in driver_points:
                    driver_points[driver_name] = {
                        'points': 0,
                        'team': team_name,
                        'team_color': driver_info.get('team_color'),
                        'driver_number': driver_num
                    }
                    driver_podiums[driver_name] = 0
                    driver_wins[driver_name] = 0
                
                # Add points
                if position in points_system:
                    driver_points[driver_name]['points'] += points_system[position]
                
                # Track podiums
                if position <= 3:
                    driver_podiums[driver_name] += 1
                
                # Track wins
                if position == 1:
                    driver_wins[driver_name] += 1
                
                # Constructor points
                if team_name:
                    if team_name not in constructor_points:
                        constructor_points[team_name] = {
                            'points': 0,
                            'team_color': driver_info.get('team_color')
                        }
                    if position in points_system:
                        constructor_points[team_name]['points'] += points_system[position]
        
        # Sort drivers by points
        drivers_sorted = sorted(
            [{'name': k, **v, 'podiums': driver_podiums.get(k, 0), 'wins': driver_wins.get(k, 0)} 
             for k, v in driver_points.items()],
            key=lambda x: x['points'],
            reverse=True
        )
        
        # Sort constructors by points
        constructors_sorted = sorted(
            [{'name': k, **v} for k, v in constructor_points.items()],
            key=lambda x: x['points'],
            reverse=True
        )
        
        # Get all podium finishers
        podium_finishers = sorted(
            [d for d in drivers_sorted if d['podiums'] > 0],
            key=lambda x: x['podiums'],
            reverse=True
        )
        
        return {
            'drivers': drivers_sorted[:10],
            'constructors': constructors_sorted[:5],
            'podium_finishers': podium_finishers,
            'all_drivers': drivers_sorted
        }
    
    def get_comprehensive_race_data(self, session_key: int) -> Dict:
        """Get all data for a race session in one call"""
        return {
            "session_info": self.get_session_info(session_key),
            "drivers": self.get_drivers(session_key),
            "positions": self.get_latest_positions(session_key),
            "pit_stops": self.get_pit_stops(session_key),
            "race_control": self.get_race_control_messages(session_key),
            "team_radio": self.get_team_radio(session_key),
            "weather": self.get_weather(session_key),
            "intervals": self.get_intervals(session_key),
            "stints": self.get_stints(session_key),
            "fastest_laps": self.get_fastest_laps(session_key),
            "all_laps": self.get_lap_data(session_key)
        }