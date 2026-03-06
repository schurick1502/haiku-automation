# HomeAssistant Sicherheits-Update

## ✅ Erfolgreich angepasst!

### Was wurde geändert:

**Vorher:**
- `network_mode: host` - HomeAssistant hatte Zugriff auf ALLE Host-Ports
- Port 8123 war von überall erreichbar

**Jetzt:**
- Explizite Port-Bindungen nur auf:
  - `127.0.0.1:8123` (localhost)
  - `192.168.178.184:8123` (interne IP)
- Kein externer Zugriff mehr möglich!

### Backup erstellt:
- `/home/egrebal/homeassistant/docker-compose.yml.backup.[timestamp]`

### Zugriff auf HomeAssistant:

**Aus dem lokalen Netzwerk:**
- http://192.168.178.184:8123

**Vom Server selbst:**
- http://localhost:8123

**Von außen (Internet):**
- ❌ BLOCKIERT (das ist gut!)

## ⚠️ Wichtige Hinweise:

### Falls Probleme mit Smart Home Geräten:

Einige HomeAssistant-Integrationen benötigen `network_mode: host` für:
- Automatische Geräte-Erkennung (mDNS/Bonjour)
- Bluetooth-Geräte
- Bestimmte Zigbee/Z-Wave Adapter

**Falls du diese Features brauchst:**

1. Editiere `/home/egrebal/homeassistant/docker-compose.yml`
2. Entferne die `ports:` Sektion
3. Aktiviere wieder `network_mode: host`
4. Restart: `docker compose restart homeassistant`

### Aktueller Status:
- Container läuft ✅
- Nur auf localhost und interne IP erreichbar ✅
- Von außen nicht mehr zugänglich ✅

## Befehle zur Überwachung:

```bash
# Status prüfen
docker ps | grep homeassistant

# Logs anzeigen
docker logs homeassistant -f

# Neustart bei Bedarf
cd /home/egrebal/homeassistant
docker compose restart homeassistant

# Zurück zur alten Config
cp docker-compose.yml.backup.* docker-compose.yml
docker compose up -d
```