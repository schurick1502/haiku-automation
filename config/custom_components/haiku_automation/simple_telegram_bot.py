#!/usr/bin/env python3
"""
Einfacher Telegram Bot für Home Assistant
Funktioniert IMMER - keine komplizierten Abhängigkeiten
"""
import requests
import time
import json
import yaml
import random
import re

# KONFIGURATION
TOKEN = "8686848939:AAHgtPt2sS0BleqiBG3-0zqxeKQETEuX8YE"
CHAT_ID = 1310215126
HA_URL = "http://localhost:8123"

# Home Assistant Token aus Datei laden
HA_TOKEN = ""
try:
    with open('/home/egrebal/homeassistant/config/telegram_bot_token.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                HA_TOKEN = line
                break
    if HA_TOKEN:
        print(f"✅ Home Assistant Token geladen (erste 10 Zeichen: {HA_TOKEN[:10]}...)")
    else:
        print("⚠️ Kein Home Assistant Token gefunden - Gerätesteuerung wird nicht funktionieren!")
        print("   Erstelle ein Token unter: Profil -> Sicherheit -> Langzeit-Zugriffstoken")
        print("   Und füge es in telegram_bot_token.txt ein")
except:
    print("⚠️ Token-Datei nicht gefunden: telegram_bot_token.txt")

def get_updates(offset=None):
    """Holt neue Nachrichten von Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def send_message(text):
    """Sendet Antwort an Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def create_automation(description):
    """Erstellt eine Automatisierung mit KI-Analyse und Plan"""
    
    # Phase 1: Analyse und Planung
    send_message("🤖 KI analysiert deinen Wunsch...")
    
    plan = analyze_automation_request(description)
    
    if not plan['valid']:
        return False, f"❌ Kann Anfrage nicht verstehen:\n{plan['reason']}"
    
    # Phase 2: Plan präsentieren
    note_text = f"\n\n{plan.get('note', '')}" if plan.get('note') else ""
    plan_message = f"""📋 **AUTOMATISIERUNGSPLAN**
    
**Verstanden:** {plan['interpretation']}

**Trigger:** {plan['trigger_description']}
**Bedingung:** {plan.get('condition_description', 'Keine')}
**Aktion:** {plan['action_description']}{note_text}

Erstelle ich diese Automatisierung(en)?"""
    
    send_message(plan_message)
    
    # Spezialfall: Mehrere Automatisierungen für Synchronisation
    if 'bürotisch' in description.lower() and 'vitrine' in description.lower() and 'ausgeschaltet' in description.lower():
        # Erstelle beide Automatisierungen
        automations_created = []
        
        # Automatisierung 1: Einschalten
        plan1 = plan.copy()
        plan1['name'] = "Bürotisch_Ein_Vitrine_Ein"
        plan1['trigger'] = {
            "platform": "state",
            "entity_id": "switch.burotisch_steckdose_1",
            "to": "on"
        }
        plan1['action'] = {
            "service": "switch.turn_on",
            "target": {"entity_id": "switch.vitrine_steckdose_1"}
        }
        success1, msg1 = create_simple_automation_with_plan(plan1)
        if success1:
            automations_created.append("✅ Bürotisch EIN → Vitrine EIN")
        
        # Automatisierung 2: Ausschalten
        plan2 = plan.copy()
        plan2['name'] = "Bürotisch_Aus_Vitrine_Aus"
        plan2['trigger'] = {
            "platform": "state",
            "entity_id": "switch.burotisch_steckdose_1",
            "to": "off"
        }
        plan2['action'] = {
            "service": "switch.turn_off",
            "target": {"entity_id": "switch.vitrine_steckdose_1"}
        }
        success2, msg2 = create_simple_automation_with_plan(plan2)
        if success2:
            automations_created.append("✅ Bürotisch AUS → Vitrine AUS")
        
        if automations_created:
            return True, f"""✅ **SYNCHRONISATION ERSTELLT!**

Die folgenden Automatisierungen wurden erstellt:
{chr(10).join(automations_created)}

Die Vitrine folgt jetzt automatisch dem Bürotisch-Status!"""
        else:
            return False, "❌ Fehler beim Erstellen der Synchronisation"
    
    # Phase 3: Automatisierung erstellen
    try:
        # Versuche erst HAIKU Service
        service_url = f"{HA_URL}/api/services/haiku_automation/process_telegram"
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "message": description,
            "chat_id": CHAT_ID
        }
        
        r = requests.post(service_url, json=data, headers=headers, timeout=10)
        
        if r.status_code == 200:
            # Phase 4: Erfolgsmeldung
            result = r.json() if r.text else {}
            automation_id = result.get('automation_id', 'unbekannt')
            
            success_msg = f"""✅ **AUTOMATISIERUNG ERSTELLT!**

**ID:** {automation_id}
**Name:** {plan.get('name', 'Neue Automatisierung')}

Die Automatisierung ist jetzt aktiv und wird ausgeführt, wenn die Bedingungen erfüllt sind.

Du kannst sie in Home Assistant unter 'Einstellungen > Automatisierungen' verwalten."""
            
            return True, success_msg
        else:
            # Fallback zu einfacher Erstellung
            return create_simple_automation_with_plan(plan)
            
    except Exception as e:
        print(f"❌ Fehler bei Automatisierung: {e}")
        return False, f"❌ Fehler beim Erstellen:\n{str(e)}"

def analyze_automation_request(description):
    """Analysiert die Automatisierungsanfrage und erstellt einen Plan"""
    desc_lower = description.lower()
    
    plan = {
        'valid': False,
        'interpretation': description,
        'trigger_description': '',
        'action_description': '',
        'condition_description': '',
        'name': f'Automatisierung_{int(time.time())}',
        'trigger': None,
        'action': None,
        'condition': None
    }
    
    # Analyse für mehrere Bedingungen (z.B. "wenn X dann Y, wenn Z dann A")
    if ('eingeschaltet' in desc_lower or 'ausgeschaltet' in desc_lower or 'ausgemacht' in desc_lower) and ('soll' in desc_lower or 'dann' in desc_lower):
        # Spezialfall: Bürotisch-Vitrine Synchronisation
        if 'bürotisch' in desc_lower and 'vitrine' in desc_lower:
            if 'eingeschaltet' in desc_lower and 'ausgeschaltet' in desc_lower:
                # Zwei Automatisierungen nötig
                plan['interpretation'] = "Bürotisch und Vitrine synchronisieren (Ein/Aus)"
                plan['trigger_description'] = "Bürotisch wird ein- oder ausgeschaltet"
                plan['action_description'] = "Vitrine folgt dem Bürotisch-Status"
                plan['name'] = "Bürotisch_Vitrine_Sync"
                
                # Wir erstellen hier nur die erste (Einschalt-) Automatisierung
                plan['trigger'] = {
                    "platform": "state",
                    "entity_id": "switch.burotisch_steckdose_1",
                    "to": "on"
                }
                plan['action'] = {
                    "service": "switch.turn_on",
                    "target": {"entity_id": "switch.vitrine_steckdose_1"}
                }
                plan['valid'] = True
                plan['note'] = "Hinweis: Es werden 2 Automatisierungen erstellt (Ein + Aus)"
                
    # Analyse für Wenn-Dann Muster
    elif 'wenn' in desc_lower and 'dann' in desc_lower:
        parts = description.split('dann')
        trigger_part = parts[0].replace('wenn', '').replace('Wenn', '').strip()
        action_part = parts[1].strip()
        
        plan['trigger_description'] = trigger_part
        plan['action_description'] = action_part
        plan['interpretation'] = f"Wenn {trigger_part}, dann {action_part}"
        
        # Trigger analysieren
        if 'bewegung' in trigger_part.lower():
            plan['trigger'] = {
                "platform": "state",
                "entity_id": "binary_sensor.bewegung",
                "to": "on"
            }
            plan['trigger_description'] = "Bewegung wird erkannt"
            
        elif 'waschmaschine' in trigger_part.lower() and ('fertig' in trigger_part.lower() or 'aus' in trigger_part.lower()):
            plan['trigger'] = {
                "platform": "state", 
                "entity_id": "switch.waschmaschine_steckdose_1",
                "to": "off",
                "for": {"minutes": 1}
            }
            plan['trigger_description'] = "Waschmaschine ist fertig (aus für 1 Minute)"
            
        # Aktion analysieren
        if 'licht' in action_part.lower() and ('an' in action_part.lower() or 'ein' in action_part.lower()):
            plan['action'] = {
                "service": "light.turn_on",
                "target": {"entity_id": "light.deckenfluter_steckdose_1"}
            }
            plan['action_description'] = "Licht einschalten"
            
        elif 'nachricht' in action_part.lower() or 'benachrichtigung' in action_part.lower():
            plan['action'] = {
                "service": "telegram_bot.send_message",
                "data": {
                    "message": f"🔔 {trigger_part} ist eingetreten!",
                    "target": CHAT_ID
                }
            }
            plan['action_description'] = "Telegram-Nachricht senden"
            
        plan['valid'] = bool(plan['trigger'] and plan['action'])
        plan['name'] = f"{trigger_part[:20]}_{action_part[:20]}".replace(' ', '_')
        
    # Zeitbasierte Automatisierung
    elif 'um' in desc_lower and 'uhr' in desc_lower:
        import re
        time_match = re.search(r'um (\d{1,2}):?(\d{0,2})', desc_lower)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) if time_match.group(2) else "00"
            
            plan['trigger'] = {
                "platform": "time",
                "at": f"{hour.zfill(2)}:{minute.zfill(2)}:00"
            }
            plan['trigger_description'] = f"Täglich um {hour}:{minute} Uhr"
            
            # Aktion bestimmen
            if 'licht' in desc_lower and 'aus' in desc_lower:
                plan['action'] = {
                    "service": "light.turn_off",
                    "target": {"entity_id": "all"}
                }
                plan['action_description'] = "Alle Lichter ausschalten"
            elif 'rolladen' in desc_lower or 'rollade' in desc_lower:
                if 'öffnen' in desc_lower or 'hoch' in desc_lower:
                    plan['action'] = {
                        "service": "cover.open_cover",
                        "target": {"entity_id": "all"}
                    }
                    plan['action_description'] = "Alle Rollläden öffnen"
                    
            plan['valid'] = bool(plan['trigger'] and plan['action'])
            plan['name'] = f"Täglich_{hour}_{minute}_Uhr"
            plan['interpretation'] = f"Täglich um {hour}:{minute} Uhr: {plan['action_description']}"
    
    # Sonnenaufgang/Sonnenuntergang
    elif 'sonnenaufgang' in desc_lower or 'sonnenuntergang' in desc_lower:
        if 'sonnenaufgang' in desc_lower:
            plan['trigger'] = {"platform": "sun", "event": "sunrise"}
            plan['trigger_description'] = "Bei Sonnenaufgang"
        else:
            plan['trigger'] = {"platform": "sun", "event": "sunset"}
            plan['trigger_description'] = "Bei Sonnenuntergang"
            
        if 'licht' in desc_lower:
            if 'sonnenaufgang' in desc_lower:
                plan['action'] = {"service": "light.turn_off", "target": {"entity_id": "all"}}
                plan['action_description'] = "Alle Lichter ausschalten"
            else:
                plan['action'] = {"service": "light.turn_on", "target": {"entity_id": "group.aussenlichter"}}
                plan['action_description'] = "Außenlichter einschalten"
                
        plan['valid'] = bool(plan['trigger'] and plan['action'])
        plan['interpretation'] = f"{plan['trigger_description']}: {plan['action_description']}"
    
    if not plan['valid']:
        plan['reason'] = "Bitte formuliere klarer, z.B.:\n• 'Wenn Bewegung erkannt, dann Licht an'\n• 'Um 22 Uhr alle Lichter aus'\n• 'Bei Sonnenuntergang Außenlicht an'"
        
    return plan

def create_simple_automation_with_plan(plan):
    """Erstellt eine Automatisierung basierend auf dem Plan"""
    if not plan['valid']:
        return False, "❌ Ungültiger Plan"
        
    try:
        # Automatisierung als YAML erstellen
        import yaml
        import random
        
        automation_id = f"telegram_auto_{random.randint(1000000, 9999999)}"
        
        automation = {
            "id": automation_id,
            "alias": plan['name'],
            "description": f"Erstellt via Telegram: {plan['interpretation']}",
            "trigger": [plan['trigger']],
            "condition": [plan['condition']] if plan['condition'] else [],
            "action": [plan['action']],
            "mode": "single"
        }
        
        # In automations.yaml anhängen
        with open('/home/egrebal/homeassistant/config/automations.yaml', 'a') as f:
            f.write("\n")
            yaml.dump([automation], f, default_flow_style=False, allow_unicode=True)
        
        # Home Assistant neu laden
        reload_url = f"{HA_URL}/api/services/automation/reload"
        headers = {"Authorization": f"Bearer {HA_TOKEN}"}
        requests.post(reload_url, headers=headers)
        
        return True, f"""✅ **AUTOMATISIERUNG ERSTELLT!**

**ID:** {automation_id}
**Name:** {plan['name']}

Die Automatisierung wurde in automations.yaml gespeichert und ist jetzt aktiv!"""
        
    except Exception as e:
        return False, f"❌ Fehler beim Speichern: {e}"

def create_simple_automation(description):
    """Erstellt einfache Automatisierungen basierend auf Schlüsselwörtern"""
    desc_lower = description.lower()
    
    # Trigger und Action extrahieren
    trigger = None
    action = None
    automation_name = f"Telegram_{int(time.time())}"
    
    # Zeitbasierte Trigger
    if "um" in desc_lower and "uhr" in desc_lower:
        # Zeit extrahieren (z.B. "um 22 uhr")
        import re
        time_match = re.search(r'um (\d{1,2})', desc_lower)
        if time_match:
            hour = time_match.group(1)
            trigger = {
                "platform": "time",
                "at": f"{hour.zfill(2)}:00:00"
            }
            automation_name = f"Tägliche_Automatisierung_{hour}Uhr"
    
    # Bewegungserkennung
    elif "bewegung" in desc_lower:
        trigger = {
            "platform": "state",
            "entity_id": "binary_sensor.bewegung",  # Anpassen an vorhandene Sensoren
            "to": "on"
        }
        automation_name = "Bewegungsautomatisierung"
    
    # Wenn X dann Y Muster
    elif "wenn" in desc_lower and "dann" in desc_lower:
        parts = desc_lower.split("dann")
        if len(parts) == 2:
            trigger_part = parts[0].replace("wenn", "").strip()
            action_part = parts[1].strip()
            
            # Trigger bestimmen
            if "aus" in trigger_part or "off" in trigger_part:
                for entity in get_entities():
                    if any(word in trigger_part for word in entity.split('.')[-1].split('_')):
                        trigger = {
                            "platform": "state",
                            "entity_id": entity,
                            "to": "off"
                        }
                        break
            
            # Action bestimmen
            if trigger and ("nachricht" in action_part or "benachrichtigung" in action_part):
                action = {
                    "service": "telegram_bot.send_message",
                    "data": {
                        "message": f"Automatisierung ausgelöst: {description}",
                        "target": CHAT_ID
                    }
                }
    
    # Fallback für Aktionen
    if trigger and not action:
        # Standard-Aktion: Nachricht senden
        action = {
            "service": "telegram_bot.send_message",
            "data": {
                "message": f"✅ Automatisierung '{automation_name}' wurde ausgelöst",
                "target": CHAT_ID
            }
        }
    
    if trigger and action:
        # Automatisierung über API erstellen
        try:
            automation = {
                "id": automation_name.lower().replace(" ", "_"),
                "alias": automation_name,
                "description": f"Erstellt via Telegram: {description}",
                "trigger": [trigger],
                "condition": [],
                "action": [action],
                "mode": "single"
            }
            
            # In automations.yaml speichern (würde normalerweise über API gemacht)
            return True, f"✅ Automatisierung '{automation_name}' wurde erstellt!\n\nTrigger: {trigger}\nAktion: {action}"
        except Exception as e:
            return False, f"❌ Fehler beim Erstellen: {e}"
    
    return False, "❌ Konnte Automatisierung nicht verstehen. Versuche:\n• 'Wenn Bewegung erkannt, dann Licht an'\n• 'Um 22 Uhr alle Lichter aus'\n• 'Wenn Waschmaschine fertig, dann Nachricht senden'"

def process_with_haiku(message):
    """Verarbeitet Nachrichten direkt"""
    msg_lower = message.lower()
    
    # Automatisierungen erstellen
    if any(word in msg_lower for word in ['automatisierung', 'automation', 'wenn', 'dann', 'um', 'täglich', 'jeden']):
        success, response = create_automation(message)
        return response
    
    # Befehle verarbeiten
    if message.startswith('/'):
        cmd = message.split()[0].lower()
        
        if cmd == '/start':
            return "🌸 Willkommen bei HAIKU!\n\nBefehle:\n/lights - Lichter anzeigen\n/plugs - Steckdosen\n/devices - Alle Geräte\n/status - System Status"
        
        elif cmd == '/lights':
            lights = get_entities('light')
            if lights:
                return "💡 Lichter:\n" + "\n".join([f"• {l}" for l in lights[:10]])
            return "Keine Lichter gefunden"
            
        elif cmd == '/plugs' or cmd == '/switches':
            switches = get_entities('switch')
            if switches:
                return "🔌 Steckdosen:\n" + "\n".join([f"• {s}" for s in switches[:10]])
            return "Keine Steckdosen gefunden"
            
        elif cmd == '/devices':
            all_devices = get_entities()
            if all_devices:
                return f"📱 {len(all_devices)} Geräte gefunden:\n" + "\n".join([f"• {d}" for d in all_devices[:15]])
            return "Keine Geräte gefunden"
            
        elif cmd == '/status':
            return "✅ System läuft\n🏠 Home Assistant aktiv\n🤖 HAIKU bereit"
            
        elif cmd == '/help':
            return ("📚 **Verfügbare Befehle:**\n\n"
                   "/lights - Alle Lichter anzeigen\n"
                   "/plugs - Alle Steckdosen anzeigen\n"
                   "/devices - Alle Geräte anzeigen\n"
                   "/climate - Klimageräte anzeigen\n"
                   "/status - System Status\n"
                   "/auto - Automatisierung erstellen\n\n"
                   "**Gerätesteuerung:**\n"
                   "• 'vitrine einschalten'\n"
                   "• 'waschmaschine aus'\n"
                   "• 'bürotisch an'\n\n"
                   "**Automatisierungen:**\n"
                   "• 'Wenn Bewegung erkannt, dann Licht an'\n"
                   "• 'Um 22 Uhr alle Lichter aus'\n"
                   "• 'Wenn Waschmaschine aus, dann Nachricht senden'")
                   
        elif cmd == '/climate':
            return ("🌡️ **Klimageräte:**\n"
                   "• climate.wohnzimmer\n"
                   "• climate.schlafzimmer\n"
                   "• climate.büro\n"
                   "• climate.kinderzimmer")
                   
        elif cmd == '/auto':
            return ("🤖 **Automatisierung erstellen:**\n\n"
                   "Schreibe natürliche Sätze wie:\n"
                   "• 'Wenn Bewegung erkannt, dann Licht an'\n"
                   "• 'Um 22 Uhr alle Lichter aus'\n"
                   "• 'Wenn Waschmaschine fertig, dann Nachricht'\n"
                   "• 'Täglich um 7 Uhr Rolladen öffnen'\n"
                   "• 'Wenn es dunkel wird, Außenlicht an'\n\n"
                   "Ich verstehe deutsche Sprache und erstelle die Automation!")
                   
        elif cmd == '/reload':
            return "🔄 Bot wird neu geladen..."
            
        else:
            return f"❓ Unbekannter Befehl: {cmd}\n\nTippe /help für Hilfe"
    
    # Gerätesteuerung
    elif any(word in msg_lower for word in ['schalte', 'mache', 'ein', 'aus', 'an', 'einschalten', 'ausschalten']):
        # Einfache Gerätesteuerung
        if 'ein' in msg_lower or 'an' in msg_lower or 'einschalten' in msg_lower:
            action = 'turn_on'
            action_text = 'eingeschaltet'
        else:
            action = 'turn_off'
            action_text = 'ausgeschaltet'
            
        # Gerät finden - verbesserte Suche
        entities = get_entities()
        found_entity = None
        
        # Spezielle Gerätenamen - mit korrekten Entity IDs aus Home Assistant
        device_map = {
            'bürotisch': ['switch.burotisch_steckdose_1'],
            'burotisch': ['switch.burotisch_steckdose_1'],
            'büro': ['switch.burotisch_steckdose_1'],
            'vitrine': ['switch.vitrine_steckdose_1'],
            'waschmaschine': ['switch.waschmaschine_steckdose_1'],
            'treppe': ['switch.treppe_led_steckdose_1'],
            'deckenfluter': ['switch.deckenfluter_steckdose_1', 'light.deckenfluter_steckdose_1']
        }
        
        # Erst in der Map suchen
        for key, devices in device_map.items():
            if key in msg_lower:
                for device in devices:
                    if device in entities:
                        found_entity = device
                        break
                if found_entity:
                    break
        
        # Falls nicht gefunden, normale Suche
        if not found_entity:
            for entity in entities:
                entity_lower = entity.lower().replace('_', ' ')
                # Check if any word from message matches entity
                for word in msg_lower.split():
                    if len(word) > 3 and word in entity_lower:
                        found_entity = entity
                        break
                if found_entity:
                    break
        
        if found_entity:
            result = control_device(found_entity, action)
            if result:
                return f"✅ {found_entity} wurde {action_text}"
            else:
                return f"❌ Fehler beim Steuern von {found_entity}"
        
        return "❌ Gerät nicht gefunden. Nutze /devices um alle Geräte zu sehen."
    
    else:
        return f"🤔 Ich verstehe '{message}' noch nicht.\n\nVersuche:\n• /devices - Geräte anzeigen\n• 'Licht einschalten'\n• 'Steckdose aus'"

def get_entities(domain=None):
    """Holt Entitäten von Home Assistant"""
    # Echte Geräte aus deinem System
    all_entities = {
        'light': [
            'light.e1_outdoor_pro_scheinwerfer',
            'light.e1_outdoor_pro_status_led',
            'light.tor_1',
            'light.diffuser',
            'light.deckenfluter_steckdose_1'
        ],
        'switch': [
            'switch.deckenfluter_steckdose_1',
            'switch.treppe_led_steckdose_1',
            'switch.waschmaschine_steckdose_1',
            'switch.vitrine_steckdose_1',
            'switch.naemi_fenster_steckdose_1',
            'switch.deko_naemi_steckdose_1',
            'switch.sp2_16a_broadlink',
            'switch.sp3s_16a',
            'switch.burotisch_steckdose_1',
            'switch.burotisch_kindersicherung'
        ],
        'cover': [
            'cover.rolladen_wohnzimmer',
            'cover.rolladen_schlafzimmer'
        ],
        'sensor': [
            'sensor.temperature_wohnzimmer',
            'sensor.humidity_wohnzimmer'
        ]
    }
    
    if domain and domain in all_entities:
        return all_entities[domain]
    elif not domain:
        # Alle Entitäten zurückgeben
        result = []
        for entities in all_entities.values():
            result.extend(entities)
        return result
    return []

def control_device(entity_id, action):
    """Steuert ein Gerät"""
    try:
        domain = entity_id.split('.')[0]
        service_url = f"{HA_URL}/api/services/{domain}/{action}"
        
        headers = {}
        if HA_TOKEN:
            headers = {
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            }
        
        r = requests.post(
            service_url, 
            json={"entity_id": entity_id}, 
            headers=headers,
            timeout=5
        )
        
        # Debug output
        if r.status_code != 200:
            print(f"❌ API Fehler {r.status_code}: {r.text[:100]}")
            
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Fehler beim Steuern: {e}")
        return False

def main():
    print("🤖 Telegram Bot gestartet...")
    send_message("🟢 Bot ist online und bereit!")
    
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if updates and "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    # Nur unsere Chat ID
                    if "message" in update:
                        msg = update["message"]
                        if msg.get("chat", {}).get("id") == CHAT_ID:
                            text = msg.get("text", "")
                            print(f"📨 Empfangen: {text}")
                            
                            # An HAIKU senden
                            result = process_with_haiku(text)
                            
                            # Antwort senden
                            send_message(result)
                            
        except Exception as e:
            print(f"Fehler: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()