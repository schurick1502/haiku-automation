# HACS Default Repository Submission Guide

## ✅ Voraussetzungen erfüllt:

- [x] Public GitHub Repository
- [x] `hacs.json` im Root
- [x] `manifest.json` mit korrekten Informationen
- [x] README.md mit Dokumentation
- [x] Versioniertes Release (v1.0.0)
- [x] Custom component Struktur korrekt

## 📝 Submission Steps:

### 1. Fork HACS Default Repository
```bash
# Fork this repo:
https://github.com/hacs/default

# Clone your fork:
git clone https://github.com/schurick1502/default
cd default
```

### 2. Add Integration to HACS
```bash
# Create new branch
git checkout -b add-haiku-automation

# Edit file: integration/haiku_automation
echo "https://github.com/schurick1502/haiku-automation" > integration/haiku_automation

# Commit
git add integration/haiku_automation
git commit -m "Add HAIKU Automation Builder integration"

# Push
git push origin add-haiku-automation
```

### 3. Create Pull Request

Go to: https://github.com/hacs/default/pulls
Create PR with template:

```markdown
## Integration: HAIKU Automation Builder

**Repository:** https://github.com/schurick1502/haiku-automation

**Description:** 
AI-powered Home Assistant automation builder using natural language. Create automations by simply describing what you want in plain text.

**Features:**
- Natural language processing for automation creation
- Telegram bot integration
- Claude AI agent support
- Multi-language (DE/EN)
- Real-time activation

**Category:** Integration

**Checklist:**
- [x] Repository is public
- [x] Repository has a README
- [x] Repository has a hacs.json
- [x] Integration has manifest.json
- [x] Integration loads in Home Assistant
- [x] All requirements are pinned
```

## 🌐 Community Promotion:

### Home Assistant Community Forum Post

**Title:** [New Integration] HAIKU - Create automations using natural language

**Category:** Share your Projects

**Content:**
```markdown
Hi everyone! 👋

I'm excited to share HAIKU Automation Builder - a new integration that lets you create Home Assistant automations using natural language!

## What is HAIKU?

HAIKU understands commands like:
- "Turn on living room lights at sunset"
- "When washing machine finishes, send notification"
- "Create morning routine at 7 AM"

And automatically creates the YAML automation for you!

## Features
🗣️ Natural language processing
💬 Telegram bot control
🤖 Claude AI integration (optional)
🌍 German & English support
📦 HACS compatible
⚡ Instant activation

## Installation

### Via HACS (Custom Repo for now):
1. HACS → Integrations → ⋮ → Custom repositories
2. Add: https://github.com/schurick1502/haiku-automation
3. Category: Integration
4. Install & restart

## Links
- GitHub: https://github.com/schurick1502/haiku-automation
- Issues: https://github.com/schurick1502/haiku-automation/issues

Would love your feedback and contributions!
```

### Reddit r/homeassistant Post

**Title:** I built HAIKU - Create HA automations with natural language (like "turn lights on at sunset")

**Content:**
```markdown
Hey r/homeassistant!

Just released HAIKU Automation Builder - an integration that converts natural language to Home Assistant automations.

Instead of writing YAML, just say what you want:
- "When motion detected at night, turn on hallway light for 5 minutes"
- "Every morning at 7 AM turn on all lights"
- "If washing machine power drops below 10W, send notification"

HAIKU understands and creates the automation instantly!

Features:
- Works in German & English
- Telegram bot for remote control
- Optional Claude AI for advanced requests
- HACS compatible

GitHub: https://github.com/schurick1502/haiku-automation

Install via HACS custom repository or manually. Would love feedback!
```

## 📊 Marketing Channels:

1. **Home Assistant Discord**
   - Share in #custom-components channel
   
2. **Twitter/X**
   ```
   🚀 Just released HAIKU for @home_assistant!
   
   Create automations with natural language:
   "Turn lights on at sunset" → Full YAML automation ✨
   
   🤖 AI-powered
   💬 Telegram control
   🌍 Multi-language
   
   GitHub: github.com/schurick1502/haiku-automation
   #HomeAssistant #SmartHome #OpenSource
   ```

3. **YouTube Demo Video**
   - Record 2-3 min demo
   - Show natural language → automation
   - Upload with tags: home assistant, automation, ai, smart home

## 🔍 SEO & Discovery:

### GitHub Topics to add:
```bash
gh repo edit --add-topic home-assistant
gh repo edit --add-topic hacs
gh repo edit --add-topic automation
gh repo edit --add-topic natural-language-processing
gh repo edit --add-topic ai
gh repo edit --add-topic smart-home
gh repo edit --add-topic telegram-bot
```

### Keywords for better discovery:
- home assistant automation
- natural language home automation
- ai smart home
- telegram home assistant
- claude ai home assistant
- hacs integration
- yaml automation generator