# 🚀 OpenAI in 5 Minuten einrichten

## Schritt 1: Bei OpenAI einloggen

### Option A: Mit Google Account (Empfohlen)
1. Öffne [platform.openai.com](https://platform.openai.com)
2. Klicke auf **"Continue with Google"**
3. Wähle dein Google-Konto
4. Fertig! ✅

### Option B: Mit Microsoft Account
1. Öffne [platform.openai.com](https://platform.openai.com)
2. Klicke auf **"Continue with Microsoft"**
3. Melde dich mit deinem Microsoft-Konto an
4. Fertig! ✅

### Option C: Mit E-Mail
1. Öffne [platform.openai.com](https://platform.openai.com)
2. Klicke auf **"Sign up"**
3. Gib deine E-Mail ein
4. Bestätige die E-Mail
5. Fertig! ✅

> **💡 Tipp:** Neue Accounts erhalten automatisch $18 Guthaben geschenkt!

## Schritt 2: API-Key erstellen

1. Nach dem Login, klicke oben rechts auf dein **Profil-Icon**
2. Wähle **"View API keys"**
3. Klicke auf **"+ Create new secret key"**
4. Gib einen Namen ein (z.B. "HAIKU")
5. **WICHTIG:** Kopiere den Key sofort! (beginnt mit `sk-`)
6. Speichere ihn sicher - du siehst ihn nie wieder!

```
Beispiel Key: sk-proj-abc123xyz789...
```

## Schritt 3: In Home Assistant einrichten

1. Öffne **Home Assistant**
2. Gehe zu **Einstellungen** → **Geräte & Dienste**
3. Finde **HAIKU Automation**
4. Klicke auf **Konfigurieren** (oder **Optionen**)
5. Aktiviere **"Enable OpenAI GPT"** ✅
6. Füge deinen **API Key** ein
7. Wähle deinen **Account-Typ**:
   - `Free Trial` → Du nutzt das $18 Guthaben
   - `Pay-as-you-go` → Du hast eine Zahlungsmethode hinterlegt
8. **Speichern** 💾

## Schritt 4: Testen

Erstelle deine erste AI-Automation:

```yaml
service: haiku_automation.create_automation
data:
  request: "Schalte das Licht um 22 Uhr aus"
```

## 📊 Was kostet das?

### Mit dem $18 Gratis-Guthaben:

| Was du machst | Wie oft | Wie lange es reicht |
|--------------|---------|-------------------|
| 5 Automations pro Tag | GPT-3.5 | ~8 Monate |
| 10 Automations pro Tag | GPT-3.5 | ~4 Monate |
| 5 Automations pro Tag | GPT-4 | ~2 Wochen |

### Nach dem Guthaben (optional):

| Modell | Pro Automation | 100 Automations |
|--------|---------------|-----------------|
| GPT-3.5 Turbo | ~$0.003 | $0.30 |
| GPT-4 Turbo | ~$0.02 | $2.00 |

## ❓ Häufige Fragen

**Muss ich meine Kreditkarte angeben?**
> Nein! Erst wenn dein $18 Guthaben aufgebraucht ist.

**Kann ich mehrere Accounts nutzen?**
> Ja, z.B. einen für Testen, einen für Produktion.

**Was passiert wenn mein Guthaben leer ist?**
> HAIKU funktioniert weiter, nur ohne AI-Features. Oder du fügst eine Zahlungsmethode bei OpenAI hinzu.

**Ist mein API-Key sicher?**
> Ja! HAIKU verschlüsselt alle API-Keys lokal.

**Kann ich den Key später ändern?**
> Ja, jederzeit in den HAIKU-Einstellungen.

## 🔒 Sicherheit

- ✅ Deine Daten werden **pseudonymisiert** bevor sie an OpenAI gehen
- ✅ Keine persönlichen Informationen werden gesendet
- ✅ API-Keys sind **verschlüsselt** gespeichert
- ✅ Du hast volle Kontrolle über alle Anfragen

## 🎉 Fertig!

Du kannst jetzt intelligente Automationen mit natürlicher Sprache erstellen!

**Beispiele:**
- "Wenn ich nach Hause komme, mach das Licht an"
- "Morgens um 7 Uhr Rollläden hoch"
- "Wenn es regnet, schließe die Fenster"
- "Abends Fernsehmodus aktivieren"

---
**Support:** [GitHub Issues](https://github.com/schurick1502/haiku-automation/issues) | **Version:** 1.3.1