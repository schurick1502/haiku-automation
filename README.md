# HAIKU Automation Builder für Home Assistant

🤖 **HAIKU** erstellt automatisch Home Assistant Automatisierungen aus natürlicher Sprache!

## ✨ Features

- 🗣️ **Natürliche Sprache** → Home Assistant Automatisierung
- 🚀 **Sofortige Aktivierung** der erstellten Automatisierungen  
- 💬 **Telegram Bot Integration** für Steuerung von unterwegs
- 🏠 **Vollständige HA Integration** mit Config Flow
- 🌍 **Mehrsprachig** (Deutsch & Englisch)

## 📦 Installation

### Methode 1: HACS (empfohlen)

1. HACS in Home Assistant öffnen
2. Auf "Integrationen" → "+" klicken
3. Nach "HAIKU Automation" suchen
4. Installieren und Home Assistant neu starten

### Methode 2: Manuell

1. Den `custom_components/haiku_automation` Ordner in dein `config/custom_components/` kopieren
2. Home Assistant neu starten
3. Zu Einstellungen → Integrationen gehen
4. "+" klicken und nach "HAIKU" suchen
5. Den Anweisungen folgen

## 🚀 Einrichtung

### Basis-Konfiguration

1. **Integration hinzufügen:**
   - Einstellungen → Integrationen → Integration hinzufügen
   - "HAIKU Automation Builder" suchen
   - Name eingeben (Standard: "HAIKU")

### Telegram Bot (optional)

1. **Bot erstellen:**
   - Mit @BotFather in Telegram chatten
   - `/newbot` eingeben
   - Bot-Namen und Username wählen
   - Token kopieren

2. **Chat ID herausfinden:**
   - Nachricht an deinen Bot senden
   - `https://api.telegram.org/bot<TOKEN>/getUpdates` aufrufen
   - Chat ID aus der Antwort kopieren

3. **In HAIKU konfigurieren:**
   - HAIKU Integration → Optionen
   - "Telegram Integration aktivieren" anhaken
   - Token und Chat ID eingeben

## 💬 Verwendung

### Service Calls

```yaml
# Automatisierung aus Text erstellen
service: haiku_automation.create_automation
data:
  request: "Wenn die Waschmaschine fertig ist, sende mir eine Nachricht"
```

### Beispiele natürlicher Sprache

- ⏰ **Zeit-basiert:** "Jeden Morgen um 7 Uhr alle Lichter einschalten"
- 🌅 **Sonnen-Events:** "Bei Sonnenuntergang alle Rollläden schließen"  
- 🔌 **Geräte-Trigger:** "Wenn die Waschmaschine aus geht, Steckdose ausschalten"
- 💡 **Mit Bedingungen:** "Wenn Bewegung erkannt wird nachts, Flur Licht für 5 Minuten an"
- 📱 **Benachrichtigungen:** "Wenn Haustür geöffnet wird, sende Nachricht"

### Telegram Befehle

- `/start` - Bot starten
- `/help` - Hilfe anzeigen
- `/status` - System Status
- `/devices` - Geräte auflisten
- Oder direkt: "Schalte Wohnzimmer Licht ein"

## 🔧 Unterstützte Komponenten

### Trigger
- **Zeit:** Uhrzeiten, morgens, abends, nachts
- **Sonne:** Sonnenaufgang, Sonnenuntergang
- **Geräte:** Ein/Aus-Zustände aller Entitäten

### Bedingungen
- **Tageszeit:** Tag, Nacht, Hell, Dunkel
- **Wochentage:** Montag bis Sonntag
- **Gerätezustände:** An/Aus Prüfungen

### Aktionen
- **Schalten:** Lichter, Steckdosen, Schalter
- **Rollläden:** Öffnen, Schließen
- **Dimmen:** Prozentuale Helligkeit
- **Verzögerungen:** Minuten, Stunden, Sekunden
- **Benachrichtigungen:** Nachrichten senden

## 📝 Erweiterte Konfiguration

### YAML Konfiguration (optional)

```yaml
haiku_automation:
  name: "Mein HAIKU"
```

### Automatisierung für Telegram Bot

```yaml
automation:
  - alias: HAIKU Telegram Handler
    trigger:
      - platform: event
        event_type: telegram_text
    action:
      - service: haiku_automation.process_telegram
        data:
          message: "{{ trigger.event.data.text }}"
          chat_id: "{{ trigger.event.data.chat_id }}"
```

## 🐛 Fehlerbehebung

**Automatisierung wird nicht erstellt:**
- Prüfe ob `/config/automations.yaml` existiert
- Stelle sicher dass Home Assistant Schreibrechte hat

**Telegram funktioniert nicht:**
- Token und Chat ID überprüfen
- Firewall/Netzwerk Einstellungen prüfen

**Geräte werden nicht erkannt:**
- Friendly Names in Home Assistant setzen
- Entity IDs in der Anfrage verwenden

## 📊 Beispiel-Automatisierung

Input: "Wenn Bewegung im Flur erkannt wird nachts, schalte Flur Licht für 2 Minuten ein"

Generierte Automatisierung:
```yaml
id: '1234567890123'
alias: 'Wenn Bewegung im Flur erkannt wird nachts, schalte Flur Licht für 2 Minuten ein'
trigger:
  - platform: state
    entity_id: binary_sensor.flur_bewegung
    to: 'on'
condition:
  - condition: sun
    after: sunset
    before: sunrise
action:
  - service: light.turn_on
    target:
      entity_id: light.flur
  - delay:
      minutes: 2
  - service: light.turn_off
    target:
      entity_id: light.flur
```

## 🤝 Beitragen

Contributions sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## 📄 Lizenz

MIT License - siehe LICENSE Datei

## 🙏 Credits

Entwickelt mit ❤️ für die Home Assistant Community