"""HAIKU Automation Builder for Home Assistant."""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from typing import Any

_LOGGER = logging.getLogger(__name__)

DOMAIN = "haiku_automation"
PLATFORMS = []

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_NAME, default="HAIKU"): cv.string,
        })
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the HAIKU Automation Builder component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HAIKU Automation from a config entry."""
    _LOGGER.info("Setting up HAIKU Automation Builder v1.3.0 with Advanced Features")
    
    # Store instance
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = HAIKUAutomation(hass, entry)
    
    # Initialize new advanced features
    from .knx_integration import KNXIntegration
    from .ai_features import AutomationDebugger, SmartLearning, AutomationSuggester, PerformanceOptimizer
    from .analytics import AutomationAnalytics
    from .integration_hub import IntegrationHub
    
    # Setup KNX Integration
    knx = KNXIntegration(hass)
    hass.data[DOMAIN][f"{entry.entry_id}_knx"] = knx
    await knx.discover_knx_devices()
    _LOGGER.info("KNX Integration initialized")
    
    # Setup AI Features
    debugger = AutomationDebugger(hass)
    learning = SmartLearning(hass)
    suggester = AutomationSuggester(hass)
    optimizer = PerformanceOptimizer(hass)
    
    hass.data[DOMAIN][f"{entry.entry_id}_debugger"] = debugger
    hass.data[DOMAIN][f"{entry.entry_id}_learning"] = learning
    hass.data[DOMAIN][f"{entry.entry_id}_suggester"] = suggester
    hass.data[DOMAIN][f"{entry.entry_id}_optimizer"] = optimizer
    _LOGGER.info("AI Features initialized")
    
    # Setup Analytics
    analytics = AutomationAnalytics(hass)
    hass.data[DOMAIN][f"{entry.entry_id}_analytics"] = analytics
    _LOGGER.info("Analytics Dashboard initialized")
    
    # Setup Integration Hub
    hub = IntegrationHub(hass)
    hass.data[DOMAIN][f"{entry.entry_id}_hub"] = hub
    discovered = await hub.discover_integrations()
    _LOGGER.info(f"Integration Hub initialized - Found {len(discovered['integrations'])} integrations")
    
    # Register services
    await _register_services(hass)
    
    # Initialize Claude Agent if API key is configured
    if entry.data.get("claude_api_key") or entry.options.get("claude_api_key"):
        from .claude_agent import ClaudeAgentService
        api_key = entry.data.get("claude_api_key") or entry.options.get("claude_api_key")
        claude_service = ClaudeAgentService(hass, api_key)
        await claude_service.async_setup()
        hass.data[DOMAIN][f"{entry.entry_id}_claude"] = claude_service
        _LOGGER.info("Claude Code Agent initialized")
    
    # Initialize OpenAI Agent if API key is configured
    if entry.data.get("openai_api_key") or entry.options.get("openai_api_key"):
        from .openai_agent import OpenAIService
        openai_config = {
            "openai_api_key": entry.data.get("openai_api_key") or entry.options.get("openai_api_key"),
            "openai_model": entry.data.get("openai_model") or entry.options.get("openai_model", "gpt-3.5-turbo"),
            "openai_subscription": entry.data.get("openai_subscription") or entry.options.get("openai_subscription", "free")
        }
        openai_service = OpenAIService(hass, openai_config)
        await openai_service.async_setup()
        hass.data[DOMAIN][f"{entry.entry_id}_openai"] = openai_service
        _LOGGER.info(f"OpenAI Agent initialized with model: {openai_config['openai_model']}")
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    
    # Remove services if no instances left
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, "create_automation")
        hass.services.async_remove(DOMAIN, "process_telegram")
    
    return True

async def _register_services(hass: HomeAssistant) -> None:
    """Register HAIKU services."""
    
    async def debug_automation(call: ServiceCall) -> None:
        """Debug an automation."""
        automation_id = call.data.get("automation_id", "")
        issue = call.data.get("issue", "")
        
        for key, instance in hass.data[DOMAIN].items():
            if key.endswith("_debugger"):
                result = await instance.debug_automation(automation_id, issue)
                hass.bus.async_fire(
                    f"{DOMAIN}_debug_result",
                    {"result": result}
                )
                break
    
    async def suggest_automations(call: ServiceCall) -> None:
        """Suggest automations based on patterns."""
        for key, instance in hass.data[DOMAIN].items():
            if key.endswith("_suggester"):
                suggestions = await instance.suggest_automations()
                hass.bus.async_fire(
                    f"{DOMAIN}_suggestions",
                    {"suggestions": suggestions}
                )
                break
    
    async def analytics_report(call: ServiceCall) -> None:
        """Generate analytics report."""
        period = call.data.get("period", "week")
        
        for key, instance in hass.data[DOMAIN].items():
            if key.endswith("_analytics"):
                report = await instance.generate_report(period)
                hass.bus.async_fire(
                    f"{DOMAIN}_analytics_report",
                    {"report": report}
                )
                break
    
    async def discover_integrations(call: ServiceCall) -> None:
        """Discover available integrations."""
        for key, instance in hass.data[DOMAIN].items():
            if key.endswith("_hub"):
                discovered = await instance.discover_integrations()
                hass.bus.async_fire(
                    f"{DOMAIN}_integrations_discovered",
                    {"integrations": discovered}
                )
                break
    
    async def create_automation(call: ServiceCall) -> None:
        """Create automation from natural language."""
        request = call.data.get("request", "")
        
        for instance in hass.data[DOMAIN].values():
            if isinstance(instance, HAIKUAutomation):
                result = await instance.create_automation(request)
                hass.bus.async_fire(
                    f"{DOMAIN}_automation_created",
                    {"automation": result}
                )
                break
    
    async def process_telegram(call: ServiceCall) -> None:
        """Process Telegram message."""
        message = call.data.get("message", "")
        chat_id = call.data.get("chat_id", "")
        
        for instance in hass.data[DOMAIN].values():
            if isinstance(instance, HAIKUAutomation):
                result = await instance.process_telegram_message(message, chat_id)
                break
    
    # Register new advanced services
    if not hass.services.has_service(DOMAIN, "debug_automation"):
        hass.services.async_register(
            DOMAIN,
            "debug_automation",
            debug_automation,
            schema=vol.Schema({
                vol.Required("automation_id"): cv.string,
                vol.Optional("issue"): cv.string,
            })
        )
    
    if not hass.services.has_service(DOMAIN, "suggest_automations"):
        hass.services.async_register(
            DOMAIN,
            "suggest_automations",
            suggest_automations,
            schema=vol.Schema({})
        )
    
    if not hass.services.has_service(DOMAIN, "analytics_report"):
        hass.services.async_register(
            DOMAIN,
            "analytics_report",
            analytics_report,
            schema=vol.Schema({
                vol.Optional("period", default="week"): vol.In(["day", "week", "month"])
            })
        )
    
    if not hass.services.has_service(DOMAIN, "discover_integrations"):
        hass.services.async_register(
            DOMAIN,
            "discover_integrations",
            discover_integrations,
            schema=vol.Schema({})
        )
    
    # Register existing services
    if not hass.services.has_service(DOMAIN, "create_automation"):
        hass.services.async_register(
            DOMAIN,
            "create_automation",
            create_automation,
            schema=vol.Schema({
                vol.Required("request"): cv.string,
            })
        )
    
    if not hass.services.has_service(DOMAIN, "process_telegram"):
        hass.services.async_register(
            DOMAIN,
            "process_telegram",
            process_telegram,
            schema=vol.Schema({
                vol.Required("message"): cv.string,
                vol.Required("chat_id"): cv.string,
            })
        )

class HAIKUAutomation:
    """HAIKU Automation Builder."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize HAIKU Automation."""
        self.hass = hass
        self.entry = entry
        self._automation_builder = None
    
    async def create_automation(self, request: str) -> dict:
        """Create automation from natural language."""
        from .automation_builder import AutomationBuilder
        
        if not self._automation_builder:
            self._automation_builder = AutomationBuilder(self.hass)
        
        return await self.hass.async_add_executor_job(
            self._automation_builder.process_request, request
        )
    
    async def process_telegram_message(self, message: str, chat_id: str) -> str:
        """Process Telegram message and return response."""
        from .telegram_processor import TelegramProcessor
        
        processor = TelegramProcessor(self.hass)
        return await processor.process_message(message, chat_id)