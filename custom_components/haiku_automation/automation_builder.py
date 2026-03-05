"""Automation Builder for HAIKU."""
import yaml
import json
import re
import random
import string
from datetime import datetime
import logging

_LOGGER = logging.getLogger(__name__)

class AutomationBuilder:
    """Build automations from natural language."""
    
    def __init__(self, hass):
        """Initialize the automation builder."""
        self.hass = hass
        self.automation_file = hass.config.path("automations.yaml")
        
    def get_entities(self):
        """Get all available entities from Home Assistant."""
        entities = {}
        for state in self.hass.states.async_all():
            entities[state.entity_id] = {
                'name': state.attributes.get('friendly_name', ''),
                'domain': state.entity_id.split('.')[0],
                'state': state.state,
                'attributes': dict(state.attributes)
            }
        return entities
    
    def parse_natural_language(self, text):
        """Parse natural language to automation components."""
        text = text.lower()
        entities = self.get_entities()
        
        triggers = []
        conditions = []
        actions = []
        
        # Zeit-Trigger
        if any(word in text for word in ['wenn', 'sobald', 'um', 'falls']):
            if time_match := re.search(r'(\d{1,2}):?(\d{0,2})\s*uhr', text):
                hour = time_match.group(1)
                minute = time_match.group(2) or '00'
                triggers.append({
                    'platform': 'time',
                    'at': f"{hour.zfill(2)}:{minute.zfill(2)}:00"
                })
            elif 'morgens' in text:
                triggers.append({'platform': 'time', 'at': '07:00:00'})
            elif 'abends' in text:
                triggers.append({'platform': 'time', 'at': '20:00:00'})
            elif 'nachts' in text:
                triggers.append({'platform': 'time', 'at': '22:00:00'})
            elif 'mittags' in text:
                triggers.append({'platform': 'time', 'at': '12:00:00'})
        
        # Sonnen-Trigger
        if 'sonnenaufgang' in text:
            triggers.append({'platform': 'sun', 'event': 'sunrise'})
        elif 'sonnenuntergang' in text:
            triggers.append({'platform': 'sun', 'event': 'sunset'})
        
        # Geräte-Trigger
        for entity_id, info in entities.items():
            entity_name = info['name'].lower() if info['name'] else entity_id.split('.')[-1].replace('_', ' ')
            
            # Check if entity is mentioned
            if entity_name in text or entity_id.split('.')[-1].replace('_', ' ') in text:
                # State change triggers
                if any(word in text for word in ['eingeschaltet wird', 'angeschaltet wird', 'an geht']):
                    triggers.append({
                        'platform': 'state',
                        'entity_id': entity_id,
                        'to': 'on'
                    })
                elif any(word in text for word in ['ausgeschaltet wird', 'aus geht', 'fertig ist']):
                    triggers.append({
                        'platform': 'state',
                        'entity_id': entity_id,
                        'to': 'off'
                    })
                
                # Actions
                if any(word in text for word in ['schalte ein', 'einschalten', 'anschalten', 'aktiviere']):
                    if info['domain'] in ['switch', 'light', 'fan', 'climate', 'input_boolean']:
                        actions.append({
                            'service': f"{info['domain']}.turn_on",
                            'target': {'entity_id': entity_id}
                        })
                elif any(word in text for word in ['schalte aus', 'ausschalten', 'deaktiviere']):
                    if info['domain'] in ['switch', 'light', 'fan', 'climate', 'input_boolean']:
                        actions.append({
                            'service': f"{info['domain']}.turn_off",
                            'target': {'entity_id': entity_id}
                        })
                elif 'toggle' in text or 'umschalten' in text:
                    if info['domain'] in ['switch', 'light', 'input_boolean']:
                        actions.append({
                            'service': f"{info['domain']}.toggle",
                            'target': {'entity_id': entity_id}
                        })
        
        # Bedingungen
        if any(word in text for word in ['nur wenn', 'falls', 'bei']):
            if 'tag' in text or 'hell' in text or 'tagsüber' in text:
                conditions.append({
                    'condition': 'sun',
                    'after': 'sunrise',
                    'before': 'sunset'
                })
            elif 'nacht' in text or 'dunkel' in text or 'nachts' in text:
                conditions.append({
                    'condition': 'sun',
                    'after': 'sunset',
                    'before': 'sunrise'
                })
        
        # Cover/Rollläden
        if 'rolllade' in text or 'rollladen' in text or 'jalousie' in text:
            for entity_id, info in entities.items():
                if info['domain'] == 'cover':
                    if 'öffne' in text or 'hochfahren' in text or 'auf' in text:
                        actions.append({
                            'service': 'cover.open_cover',
                            'target': {'entity_id': entity_id}
                        })
                    elif 'schließe' in text or 'runterfahren' in text or 'zu' in text:
                        actions.append({
                            'service': 'cover.close_cover',
                            'target': {'entity_id': entity_id}
                        })
        
        # Verzögerungen
        if delay_match := re.search(r'(\d+)\s*minute', text):
            minutes = int(delay_match.group(1))
            actions.append({'delay': {'minutes': minutes}})
        elif delay_match := re.search(r'(\d+)\s*stunde', text):
            hours = int(delay_match.group(1))
            actions.append({'delay': {'hours': hours}})
        elif delay_match := re.search(r'(\d+)\s*sekunde', text):
            seconds = int(delay_match.group(1))
            actions.append({'delay': {'seconds': seconds}})
        
        # Benachrichtigungen
        if any(word in text for word in ['benachrichtige', 'nachricht', 'melde', 'informiere']):
            message = "Automatisierung wurde ausgeführt"
            if 'dass' in text:
                message = text.split('dass')[-1].strip()
            elif '"' in text:
                quoted = re.findall(r'"([^"]*)"', text)
                if quoted:
                    message = quoted[0]
            
            actions.append({
                'service': 'notify.notify',
                'data': {'message': message}
            })
        
        # Dimmen
        if 'dimme' in text and (brightness_match := re.search(r'(\d+)\s*%', text)):
            brightness = int(brightness_match.group(1))
            for entity_id, info in entities.items():
                if info['domain'] == 'light' and (info['name'].lower() in text or entity_id.split('.')[-1] in text):
                    actions.append({
                        'service': 'light.turn_on',
                        'target': {'entity_id': entity_id},
                        'data': {'brightness_pct': brightness}
                    })
        
        return {
            'triggers': triggers,
            'conditions': conditions,
            'actions': actions
        }
    
    def create_automation(self, description, components=None):
        """Create a new automation."""
        if components is None:
            components = self.parse_natural_language(description)
        
        # Generate unique ID
        automation_id = ''.join(random.choices(string.digits, k=13))
        
        # Build automation
        automation = {
            'id': automation_id,
            'alias': description[:100],
            'description': f'Erstellt am {datetime.now().strftime("%d.%m.%Y %H:%M")}',
            'mode': 'single'
        }
        
        # Add components
        if components['triggers']:
            automation['trigger'] = components['triggers']
        else:
            automation['trigger'] = [{'platform': 'event', 'event_type': 'automation_manually_triggered'}]
        
        if components['conditions']:
            automation['condition'] = components['conditions']
        
        if components['actions']:
            automation['action'] = components['actions']
        else:
            automation['action'] = [{
                'service': 'persistent_notification.create',
                'data': {
                    'title': 'HAIKU Automation',
                    'message': f'Automation "{description}" wurde ausgeführt'
                }
            }]
        
        return automation
    
    def save_automation(self, automation):
        """Save automation to file."""
        try:
            with open(self.automation_file, 'r') as f:
                automations = yaml.safe_load(f) or []
            
            automations.append(automation)
            
            with open(self.automation_file, 'w') as f:
                yaml.dump(automations, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            _LOGGER.error(f"Error saving automation: {e}")
            return False
    
    def reload_automations(self):
        """Reload automations in Home Assistant."""
        try:
            self.hass.services.call('automation', 'reload')
            return True
        except Exception as e:
            _LOGGER.error(f"Error reloading automations: {e}")
            return False
    
    def process_request(self, request):
        """Process a natural language request."""
        _LOGGER.info(f"Processing request: {request}")
        
        # Parse and create automation
        components = self.parse_natural_language(request)
        automation = self.create_automation(request, components)
        
        # Save and reload
        if self.save_automation(automation):
            if self.reload_automations():
                _LOGGER.info(f"Created automation: {automation['id']}")
                return automation
            else:
                _LOGGER.warning("Could not reload automations")
        else:
            _LOGGER.error("Could not save automation")
        
        return None