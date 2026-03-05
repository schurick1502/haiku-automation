"""Config flow for HAIKU Automation Builder."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME

from .const import DOMAIN, DEFAULT_NAME

class HAIKUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAIKU Automation."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id("haiku_automation_instance")
            self._abort_if_unique_id_configured()
            
            # Create entry
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input
            )

        # Show form
        data_schema = vol.Schema({
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Optional("telegram_token", default=""): str,
            vol.Optional("telegram_chat_id", default=""): str,
            vol.Optional("enable_telegram", default=False): bool,
            vol.Optional("claude_api_key", default=""): str,
            vol.Optional("enable_claude", default=False): bool,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return HAIKUOptionsFlow(config_entry)


class HAIKUOptionsFlow(config_entries.OptionsFlow):
    """Handle options for HAIKU Automation."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "enable_telegram",
                    default=self.config_entry.options.get("enable_telegram", False)
                ): bool,
                vol.Optional(
                    "telegram_token",
                    default=self.config_entry.options.get("telegram_token", "")
                ): str,
                vol.Optional(
                    "telegram_chat_id", 
                    default=self.config_entry.options.get("telegram_chat_id", "")
                ): str,
                vol.Optional(
                    "natural_language_model",
                    default=self.config_entry.options.get("natural_language_model", "simple")
                ): vol.In(["simple", "advanced"]),
            })
        )