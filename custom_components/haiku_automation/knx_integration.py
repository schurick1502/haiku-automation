"""KNX Integration Module for HAIKU Automation Builder."""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

_LOGGER = logging.getLogger(__name__)

class KNXIntegration:
    """KNX-specific integration for HAIKU."""
    
    def __init__(self, hass):
        """Initialize KNX Integration."""
        self.hass = hass
        self.knx_devices = {}
        self.group_addresses = {}
        self.scenes = {}
        self.building_structure = {}
        
    async def discover_knx_devices(self) -> Dict[str, Any]:
        """
        Discover all KNX devices and their capabilities.
        
        Returns:
            Dictionary of KNX devices with their group addresses and functions
        """
        knx_devices = {}
        
        # Find all KNX entities in Home Assistant
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            
            # Check if this is a KNX device
            if self._is_knx_entity(entity_id, state.attributes):
                device_info = self._extract_knx_info(entity_id, state)
                knx_devices[entity_id] = device_info
                
                # Map group addresses
                if 'knx_group_address' in state.attributes:
                    ga = state.attributes['knx_group_address']
                    self.group_addresses[ga] = entity_id
        
        self.knx_devices = knx_devices
        _LOGGER.info(f"Discovered {len(knx_devices)} KNX devices")
        
        return knx_devices
    
    def _is_knx_entity(self, entity_id: str, attributes: dict) -> bool:
        """Check if entity is a KNX device."""
        # Check for KNX-specific attributes
        knx_indicators = [
            'knx_group_address',
            'knx_source',
            'knx_destination',
            'knx_dpt'
        ]
        
        # Check if any KNX indicator is present
        for indicator in knx_indicators:
            if indicator in attributes:
                return True
        
        # Check if entity_id contains KNX hints
        if 'knx' in entity_id.lower():
            return True
            
        return False
    
    def _extract_knx_info(self, entity_id: str, state) -> Dict[str, Any]:
        """Extract KNX-specific information from entity."""
        info = {
            'entity_id': entity_id,
            'friendly_name': state.attributes.get('friendly_name', entity_id),
            'state': state.state,
            'device_class': state.attributes.get('device_class'),
            'knx_info': {}
        }
        
        # Extract KNX-specific attributes
        knx_attrs = ['knx_group_address', 'knx_source', 'knx_destination', 'knx_dpt']
        for attr in knx_attrs:
            if attr in state.attributes:
                info['knx_info'][attr] = state.attributes[attr]
        
        # Determine device type and capabilities
        info['capabilities'] = self._determine_capabilities(entity_id, state.attributes)
        
        # Extract location/room information
        info['location'] = self._extract_location(entity_id, state.attributes.get('friendly_name', ''))
        
        return info
    
    def _determine_capabilities(self, entity_id: str, attributes: dict) -> List[str]:
        """Determine what a KNX device can do."""
        capabilities = []
        
        # Check domain
        domain = entity_id.split('.')[0]
        
        if domain == 'light':
            capabilities.extend(['on_off', 'brightness'])
            if attributes.get('supported_color_modes'):
                capabilities.append('color')
        elif domain == 'switch':
            capabilities.append('on_off')
        elif domain == 'cover':
            capabilities.extend(['open_close', 'position'])
            if attributes.get('tilt_position'):
                capabilities.append('tilt')
        elif domain == 'climate':
            capabilities.extend(['temperature', 'hvac_mode'])
        elif domain == 'sensor':
            capabilities.append('read_only')
        elif domain == 'binary_sensor':
            capabilities.extend(['read_only', 'motion' if 'motion' in entity_id else 'binary'])
        
        return capabilities
    
    def _extract_location(self, entity_id: str, friendly_name: str) -> str:
        """Extract room/location from entity name."""
        # Common room patterns in German and English
        rooms = [
            'wohnzimmer', 'schlafzimmer', 'küche', 'bad', 'flur', 'büro',
            'keller', 'dachboden', 'garage', 'garten', 'terrasse', 'balkon',
            'living', 'bedroom', 'kitchen', 'bathroom', 'hallway', 'office',
            'basement', 'attic', 'garage', 'garden', 'terrace', 'balcony'
        ]
        
        text = f"{entity_id} {friendly_name}".lower()
        
        for room in rooms:
            if room in text:
                return room
        
        return 'unknown'
    
    async def create_knx_automation(self, request: str) -> Dict[str, Any]:
        """
        Create KNX-specific automation from natural language.
        
        Enhanced to understand KNX-specific terminology and patterns.
        """
        # Analyze request for KNX-specific patterns
        knx_patterns = self._analyze_knx_patterns(request)
        
        # Build automation with KNX optimizations
        automation = {
            'id': f'knx_auto_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'alias': f'KNX: {request[:100]}',
            'description': 'Created by HAIKU KNX Integration',
            'mode': 'single'
        }
        
        # Handle KNX scene commands
        if knx_patterns.get('scene'):
            automation = self._build_scene_automation(knx_patterns['scene'], request)
        
        # Handle group operations
        elif knx_patterns.get('group_operation'):
            automation = self._build_group_automation(knx_patterns['group_operation'], request)
        
        # Handle standard automation with KNX devices
        else:
            automation = await self._build_standard_knx_automation(request, knx_patterns)
        
        return automation
    
    def _analyze_knx_patterns(self, request: str) -> Dict[str, Any]:
        """Analyze request for KNX-specific patterns."""
        patterns = {}
        request_lower = request.lower()
        
        # Scene patterns
        scene_keywords = ['szene', 'scene', 'stimmung', 'mood']
        for keyword in scene_keywords:
            if keyword in request_lower:
                patterns['scene'] = self._extract_scene_name(request)
                break
        
        # Group operations
        if any(word in request_lower for word in ['alle', 'all', 'gesamt', 'entire']):
            patterns['group_operation'] = True
        
        # Central functions
        if any(word in request_lower for word in ['zentral', 'central', 'master']):
            patterns['central_function'] = True
        
        # Time programs
        if any(word in request_lower for word in ['zeitprogramm', 'schedule', 'timer']):
            patterns['time_program'] = True
        
        return patterns
    
    def _extract_scene_name(self, request: str) -> str:
        """Extract scene name from request."""
        # Common scene names
        scenes = {
            'morgen': 'morning',
            'abend': 'evening',
            'nacht': 'night',
            'arbeit': 'work',
            'film': 'movie',
            'dinner': 'dinner',
            'party': 'party',
            'weg': 'away',
            'urlaub': 'vacation'
        }
        
        request_lower = request.lower()
        for german, english in scenes.items():
            if german in request_lower or english in request_lower:
                return english
        
        return 'custom'
    
    def _build_scene_automation(self, scene: str, request: str) -> Dict[str, Any]:
        """Build KNX scene automation."""
        return {
            'id': f'knx_scene_{scene}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'alias': f'KNX Scene: {scene.title()}',
            'trigger': self._extract_trigger_from_request(request),
            'action': [
                {
                    'service': 'scene.turn_on',
                    'target': {
                        'entity_id': f'scene.knx_{scene}'
                    }
                }
            ]
        }
    
    def _build_group_automation(self, group_op: bool, request: str) -> Dict[str, Any]:
        """Build KNX group operation automation."""
        # Find all devices in the requested location
        location = self._extract_location_from_request(request)
        devices = self._get_devices_by_location(location)
        
        return {
            'id': f'knx_group_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'alias': f'KNX Group: {request[:80]}',
            'trigger': self._extract_trigger_from_request(request),
            'action': [
                {
                    'service': 'homeassistant.turn_on' if 'ein' in request.lower() or 'on' in request.lower() else 'homeassistant.turn_off',
                    'target': {
                        'entity_id': devices
                    }
                }
            ]
        }
    
    async def _build_standard_knx_automation(self, request: str, patterns: Dict) -> Dict[str, Any]:
        """Build standard automation with KNX devices."""
        # This would integrate with the main automation builder
        # but with KNX-specific enhancements
        automation = {
            'id': f'knx_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'alias': request[:100],
            'trigger': self._extract_trigger_from_request(request),
            'action': self._extract_actions_from_request(request)
        }
        
        return automation
    
    def _extract_trigger_from_request(self, request: str) -> List[Dict]:
        """Extract trigger from natural language request."""
        triggers = []
        request_lower = request.lower()
        
        # Time-based triggers
        time_pattern = r'(\d{1,2}):(\d{2})'
        time_match = re.search(time_pattern, request)
        if time_match:
            triggers.append({
                'platform': 'time',
                'at': f"{time_match.group(1).zfill(2)}:{time_match.group(2)}:00"
            })
        
        # Motion triggers
        if any(word in request_lower for word in ['bewegung', 'motion']):
            # Find motion sensors
            for entity_id, info in self.knx_devices.items():
                if 'motion' in info.get('capabilities', []):
                    triggers.append({
                        'platform': 'state',
                        'entity_id': entity_id,
                        'to': 'on'
                    })
                    break
        
        # Sun triggers
        if 'sonnenaufgang' in request_lower or 'sunrise' in request_lower:
            triggers.append({'platform': 'sun', 'event': 'sunrise'})
        elif 'sonnenuntergang' in request_lower or 'sunset' in request_lower:
            triggers.append({'platform': 'sun', 'event': 'sunset'})
        
        return triggers if triggers else [{'platform': 'time', 'at': '12:00:00'}]
    
    def _extract_actions_from_request(self, request: str) -> List[Dict]:
        """Extract actions from natural language request."""
        actions = []
        request_lower = request.lower()
        
        # Find target devices
        target_devices = []
        for entity_id, info in self.knx_devices.items():
            device_name = info['friendly_name'].lower()
            if device_name in request_lower or entity_id.split('.')[-1] in request_lower:
                target_devices.append(entity_id)
        
        # Determine action type
        if any(word in request_lower for word in ['ein', 'an', 'on', 'activate']):
            service = 'homeassistant.turn_on'
        elif any(word in request_lower for word in ['aus', 'off', 'deactivate']):
            service = 'homeassistant.turn_off'
        else:
            service = 'homeassistant.toggle'
        
        if target_devices:
            actions.append({
                'service': service,
                'target': {
                    'entity_id': target_devices
                }
            })
        
        return actions
    
    def _extract_location_from_request(self, request: str) -> str:
        """Extract location from request."""
        request_lower = request.lower()
        
        # Check all known locations
        for entity_id, info in self.knx_devices.items():
            location = info.get('location', '')
            if location and location in request_lower:
                return location
        
        return 'all'
    
    def _get_devices_by_location(self, location: str) -> List[str]:
        """Get all devices in a specific location."""
        if location == 'all':
            return list(self.knx_devices.keys())
        
        devices = []
        for entity_id, info in self.knx_devices.items():
            if info.get('location') == location:
                devices.append(entity_id)
        
        return devices
    
    async def analyze_knx_usage(self) -> Dict[str, Any]:
        """Analyze KNX system usage and provide insights."""
        analysis = {
            'total_devices': len(self.knx_devices),
            'devices_by_type': {},
            'devices_by_location': {},
            'unused_devices': [],
            'most_used_devices': [],
            'optimization_suggestions': []
        }
        
        # Count devices by type
        for entity_id, info in self.knx_devices.items():
            domain = entity_id.split('.')[0]
            analysis['devices_by_type'][domain] = analysis['devices_by_type'].get(domain, 0) + 1
            
            location = info.get('location', 'unknown')
            analysis['devices_by_location'][location] = analysis['devices_by_location'].get(location, 0) + 1
        
        # Generate optimization suggestions
        if analysis['total_devices'] > 50:
            analysis['optimization_suggestions'].append(
                "Consider creating scenes for frequently used device combinations"
            )
        
        return analysis
    
    async def suggest_knx_automations(self) -> List[Dict[str, Any]]:
        """Suggest useful KNX automations based on available devices."""
        suggestions = []
        
        # Check available device types
        has_motion = any('motion' in d.get('capabilities', []) for d in self.knx_devices.values())
        has_lights = any(e.startswith('light.') for e in self.knx_devices.keys())
        has_covers = any(e.startswith('cover.') for e in self.knx_devices.keys())
        has_climate = any(e.startswith('climate.') for e in self.knx_devices.keys())
        
        # Suggest motion-based lighting
        if has_motion and has_lights:
            suggestions.append({
                'name': 'Motion-Activated Lighting',
                'description': 'Turn on lights when motion is detected',
                'request': 'Wenn Bewegung erkannt wird, schalte das Licht ein'
            })
        
        # Suggest cover automation
        if has_covers:
            suggestions.append({
                'name': 'Automatic Blinds',
                'description': 'Close blinds at sunset',
                'request': 'Schließe alle Rollläden bei Sonnenuntergang'
            })
        
        # Suggest climate optimization
        if has_climate:
            suggestions.append({
                'name': 'Climate Schedule',
                'description': 'Reduce heating at night',
                'request': 'Reduziere die Heizung um 22 Uhr auf 18 Grad'
            })
        
        # Suggest central off
        if has_lights or has_covers:
            suggestions.append({
                'name': 'Central Off',
                'description': 'Turn everything off when leaving',
                'request': 'Schalte alles aus wenn ich das Haus verlasse'
            })
        
        return suggestions