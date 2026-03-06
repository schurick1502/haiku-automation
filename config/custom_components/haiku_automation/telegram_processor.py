"""Telegram message processor for HAIKU."""
import logging
import re
from .automation_builder import AutomationBuilder

_LOGGER = logging.getLogger(__name__)

class TelegramProcessor:
    """Process Telegram messages for HAIKU."""
    
    def __init__(self, hass):
        """Initialize processor."""
        self.hass = hass
        self.builder = AutomationBuilder(hass)
    
    async def process_message(self, message, chat_id):
        """Process a Telegram message."""
        message_lower = message.lower()
        
        # Commands
        if message.startswith('/'):
            return await self._handle_command(message, chat_id)
        
        # Device control
        if any(word in message_lower for word in ['schalte', 'mache', 'aktiviere', 'öffne', 'schließe']):
            return await self._handle_device_control(message)
        
        # Automation creation
        if any(word in message_lower for word in ['wenn', 'sobald', 'falls', 'automatisierung']):
            return await self._handle_automation_creation(message)
        
        # Status queries
        if any(word in message_lower for word in ['status', 'zustand', 'wie ist', 'zeige']):
            return await self._handle_status_query(message)
        
        # Default response
        return "🤔 Ich verstehe: " + message + "\nVersuche: 'Schalte Licht ein' oder 'Wenn Bewegung erkannt, dann Licht an'"
    
    async def _handle_command(self, command, chat_id):
        """Handle Telegram commands."""
        cmd = command.split()[0].lower()
        
        if cmd == '/start':
            return ("🌸 Willkommen bei HAIKU!\n\n"
                   "Ich kann:\n"
                   "• Geräte steuern\n"
                   "• Automatisierungen erstellen\n"
                   "• Status anzeigen\n\n"
                   "Beispiel: 'Schalte Wohnzimmer Licht ein'")
        
        elif cmd == '/help':
            return ("📚 HAIKU Hilfe\n\n"
                   "Geräte steuern:\n"
                   "• Schalte [Gerät] ein/aus\n"
                   "• Öffne/Schließe [Rolllade]\n\n"
                   "Automatisierung:\n"
                   "• Wenn [Trigger], dann [Aktion]\n\n"
                   "Status:\n"
                   "• Zeige alle Lichter\n"
                   "• Status [Gerät]")
        
        elif cmd == '/status':
            # Count entities
            lights = len([s for s in self.hass.states.async_all() if s.entity_id.startswith('light.')])
            switches = len([s for s in self.hass.states.async_all() if s.entity_id.startswith('switch.')])
            automations = len([s for s in self.hass.states.async_all() if s.entity_id.startswith('automation.')])
            
            return (f"📊 System Status\n\n"
                   f"💡 Lichter: {lights}\n"
                   f"🔌 Schalter: {switches}\n"
                   f"🤖 Automatisierungen: {automations}")
        
        elif cmd == '/devices':
            return await self._list_devices()
        
        return "❓ Unbekannter Befehl. Nutze /help für Hilfe."
    
    async def _handle_device_control(self, message):
        """Handle device control requests."""
        message_lower = message.lower()
        response = []
        
        # Find matching devices
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            friendly_name = state.attributes.get('friendly_name', '').lower()
            entity_name = entity_id.split('.')[-1].replace('_', ' ')
            
            # Check if device is mentioned
            if friendly_name in message_lower or entity_name in message_lower:
                domain = entity_id.split('.')[0]
                
                # Determine action
                if any(word in message_lower for word in ['ein', 'an', 'aktiviere']):
                    if domain in ['light', 'switch', 'fan', 'climate']:
                        await self.hass.services.async_call(
                            domain, 'turn_on',
                            {'entity_id': entity_id}
                        )
                        response.append(f"✅ {friendly_name or entity_name} eingeschaltet")
                
                elif any(word in message_lower for word in ['aus', 'deaktiviere']):
                    if domain in ['light', 'switch', 'fan', 'climate']:
                        await self.hass.services.async_call(
                            domain, 'turn_off',
                            {'entity_id': entity_id}
                        )
                        response.append(f"✅ {friendly_name or entity_name} ausgeschaltet")
                
                elif 'öffne' in message_lower and domain == 'cover':
                    await self.hass.services.async_call(
                        'cover', 'open_cover',
                        {'entity_id': entity_id}
                    )
                    response.append(f"✅ {friendly_name or entity_name} geöffnet")
                
                elif 'schließe' in message_lower and domain == 'cover':
                    await self.hass.services.async_call(
                        'cover', 'close_cover',
                        {'entity_id': entity_id}
                    )
                    response.append(f"✅ {friendly_name or entity_name} geschlossen")
        
        if response:
            return "\n".join(response)
        else:
            return "❌ Kein passendes Gerät gefunden"
    
    async def _handle_automation_creation(self, message):
        """Handle automation creation requests."""
        result = await self.hass.async_add_executor_job(
            self.builder.process_request, message
        )
        
        if result:
            return (f"✅ Automatisierung erstellt!\n\n"
                   f"Name: {result.get('alias', 'Unbenannt')}\n"
                   f"ID: {result.get('id', 'N/A')}\n\n"
                   f"Die Automatisierung ist jetzt aktiv.")
        else:
            return "❌ Konnte Automatisierung nicht erstellen. Bitte Anfrage überprüfen."
    
    async def _handle_status_query(self, message):
        """Handle status queries."""
        message_lower = message.lower()
        response = []
        
        # List specific domain
        if 'licht' in message_lower or 'lampe' in message_lower:
            states = [s for s in self.hass.states.async_all() if s.entity_id.startswith('light.')]
            response.append(f"💡 Lichter ({len(states)}):")
            for state in states[:10]:
                name = state.attributes.get('friendly_name', state.entity_id)
                status = "🟢 An" if state.state == 'on' else "⚫ Aus"
                response.append(f"  {name}: {status}")
        
        elif 'steckdose' in message_lower or 'schalter' in message_lower:
            states = [s for s in self.hass.states.async_all() if s.entity_id.startswith('switch.')]
            response.append(f"🔌 Schalter ({len(states)}):")
            for state in states[:10]:
                name = state.attributes.get('friendly_name', state.entity_id)
                status = "🟢 An" if state.state == 'on' else "⚫ Aus"
                response.append(f"  {name}: {status}")
        
        elif 'rolllade' in message_lower or 'jalousie' in message_lower:
            states = [s for s in self.hass.states.async_all() if s.entity_id.startswith('cover.')]
            response.append(f"🚪 Rollläden ({len(states)}):")
            for state in states[:10]:
                name = state.attributes.get('friendly_name', state.entity_id)
                if state.state == 'open':
                    status = "📂 Offen"
                elif state.state == 'closed':
                    status = "📁 Geschlossen"
                else:
                    status = f"📊 {state.state}"
                response.append(f"  {name}: {status}")
        
        if response:
            return "\n".join(response)
        else:
            return "❓ Keine spezifische Abfrage erkannt"
    
    async def _list_devices(self):
        """List all available devices."""
        devices = {
            'lights': [],
            'switches': [],
            'covers': [],
            'climate': [],
            'sensors': []
        }
        
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            name = state.attributes.get('friendly_name', entity_id)
            
            if entity_id.startswith('light.'):
                devices['lights'].append(name)
            elif entity_id.startswith('switch.'):
                devices['switches'].append(name)
            elif entity_id.startswith('cover.'):
                devices['covers'].append(name)
            elif entity_id.startswith('climate.'):
                devices['climate'].append(name)
            elif entity_id.startswith('sensor.') and len(devices['sensors']) < 5:
                devices['sensors'].append(name)
        
        response = ["📱 Verfügbare Geräte:\n"]
        
        if devices['lights']:
            response.append(f"💡 Lichter ({len(devices['lights'])}):")
            for device in devices['lights'][:5]:
                response.append(f"  • {device}")
        
        if devices['switches']:
            response.append(f"\n🔌 Schalter ({len(devices['switches'])}):")
            for device in devices['switches'][:5]:
                response.append(f"  • {device}")
        
        if devices['covers']:
            response.append(f"\n🚪 Rollläden ({len(devices['covers'])}):")
            for device in devices['covers'][:5]:
                response.append(f"  • {device}")
        
        return "\n".join(response)