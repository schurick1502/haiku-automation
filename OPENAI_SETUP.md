# OpenAI Setup für HAIKU - 100% KOSTENLOS

## HAIKU ist und bleibt KOSTENLOS!
HAIKU ist vollständig Open Source und kostenlos. Du zahlst nur für deine OpenAI API-Nutzung direkt an OpenAI.

## So funktioniert's:

### 1. OpenAI Account erstellen oder einloggen
1. Gehe zu [platform.openai.com](https://platform.openai.com)
2. Wähle deine bevorzugte Methode:
   - **E-Mail & Passwort**: Klassische Registrierung
   - **Google Account**: Mit Google einloggen
   - **Microsoft Account**: Mit Microsoft einloggen
   - **Apple ID**: Mit Apple einloggen
3. Neue Accounts erhalten $18 Gratis-Guthaben!

### 2. API-Key generieren
1. Klicke auf dein Profil → "View API keys"
2. "Create new secret key"
3. Kopiere den Key (beginnt mit `sk-`)
4. **WICHTIG:** Speichere den Key sicher!

### 3. In HAIKU konfigurieren
1. Home Assistant → Einstellungen → Integrationen → HAIKU
2. "Enable OpenAI GPT" aktivieren
3. API-Key einfügen
4. OpenAI Account-Typ wählen:
   - **Free Trial**: Erste $18 gratis
   - **Pay-as-you-go**: Standard (Kreditkarte hinterlegt)
   - **Tier 1**: Nach $50 Ausgaben bei OpenAI
   - **Tier 2**: Nach $500 Ausgaben bei OpenAI
   - **Custom**: Keine Limits von HAIKU

### 4. Kosten bei OpenAI

| Modell | Kosten | Beispiel (100 Anfragen) |
|--------|--------|------------------------|
| GPT-3.5 Turbo | $0.0015/1K tokens | ~$0.30 |
| GPT-4 Turbo | $0.01/1K tokens | ~$2.00 |
| GPT-4 | $0.03/1K tokens | ~$6.00 |

**Mit dem $18 Gratis-Guthaben kannst du:**
- ~12.000 Anfragen mit GPT-3.5 Turbo
- ~900 Anfragen mit GPT-4 Turbo
- ~300 Anfragen mit GPT-4

## Warum Account-Typ in HAIKU?

Der Account-Typ hilft HAIKU, deine Limits zu respektieren:
- Verhindert versehentlich hohe Kosten
- Passt Rate-Limits an
- Zeigt verfügbare Modelle

## Datenschutz

✅ HAIKU sendet KEINE Daten ohne deine Erlaubnis
✅ Alle Daten werden pseudonymisiert vor dem Senden
✅ API-Keys werden verschlüsselt gespeichert
✅ Du behältst volle Kontrolle

## FAQ

**Muss ich zahlen?**
Nein! HAIKU ist kostenlos. Du zahlst nur OpenAI für API-Nutzung (nach den ersten $18).

**Wie lange reicht das Gratis-Guthaben?**
Bei normaler Nutzung (5-10 Automations/Tag) etwa 3-6 Monate.

**Was passiert wenn das Guthaben aufgebraucht ist?**
Du kannst eine Kreditkarte bei OpenAI hinterlegen oder HAIKU ohne AI nutzen.

**Kann ich die Limits ändern?**
Ja! Wähle "Custom" und setze eigene Limits oder keine Limits.

## Support

- HAIKU ist Open Source: [github.com/schurick1502/haiku-automation](https://github.com/schurick1502/haiku-automation)
- Issues: [GitHub Issues](https://github.com/schurick1502/haiku-automation/issues)
- OpenAI Hilfe: [platform.openai.com/docs](https://platform.openai.com/docs)

---
**HAIKU v1.3.1** - Kostenlose, intelligente Automatisierung für alle!