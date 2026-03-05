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
    _LOGGER.info("Setting up HAIKU Automation Builder")
    
    # Store instance
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = HAIKUAutomation(hass, entry)
    
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
    
    # Register services
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