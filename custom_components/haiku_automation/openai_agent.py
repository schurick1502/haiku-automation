"""OpenAI LLM Integration for HAIKU Automation Builder."""
import logging
import aiohttp
import json
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# Import security components
from .security import DataSanitizer, APIKeyVault, RateLimiter, SecurityAuditor

_LOGGER = logging.getLogger(__name__)

class OpenAIAgent:
    """OpenAI GPT Integration for advanced automation creation."""
    
    MODELS = {
        "gpt-4": {
            "name": "GPT-4 (Most capable)",
            "max_tokens": 8192,
            "description": "Best for complex automations and understanding",
            "cost_per_1k": 0.03
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "max_tokens": 128000,
            "description": "Faster GPT-4 with larger context",
            "cost_per_1k": 0.01
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "max_tokens": 4096,
            "description": "Fast and cost-effective",
            "cost_per_1k": 0.0015
        }
    }
    
    def __init__(self, hass, api_key: str, model: str = "gpt-3.5-turbo", subscription_tier: str = "free"):
        """
        Initialize OpenAI Agent.
        
        Args:
            hass: Home Assistant instance
            api_key: OpenAI API key
            model: GPT model to use
            subscription_tier: free, basic, pro, enterprise
        """
        self.hass = hass
        self.model = model
        self.subscription_tier = subscription_tier
        self.session = None
        
        # Initialize security components
        self.sanitizer = DataSanitizer(hass)
        self.vault = APIKeyVault(hass)
        self.rate_limiter = RateLimiter()
        self.auditor = SecurityAuditor(hass)
        
        # Store API key securely
        self.vault.store_api_key("openai", api_key)
        
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_today": 0,
            "last_reset": datetime.now().date()
        }
        self.rate_limits = {
            "free": {"daily_requests": 10, "max_tokens": 2000},
            "basic": {"daily_requests": 100, "max_tokens": 4000},
            "pro": {"daily_requests": 1000, "max_tokens": 8000},
            "enterprise": {"daily_requests": -1, "max_tokens": 128000}  # -1 = unlimited
        }
        
    async def initialize(self):
        """Initialize the OpenAI session."""
        self.session = aiohttp.ClientSession()
        _LOGGER.info(f"OpenAI Agent initialized with model: {self.model}")
        
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
    
    def check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        # Reset daily counter
        today = datetime.now().date()
        if self.usage_stats["last_reset"] != today:
            self.usage_stats["requests_today"] = 0
            self.usage_stats["last_reset"] = today
        
        limits = self.rate_limits.get(self.subscription_tier, self.rate_limits["free"])
        
        if limits["daily_requests"] == -1:  # Unlimited
            return True
            
        return self.usage_stats["requests_today"] < limits["daily_requests"]
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a natural language request using OpenAI GPT.
        
        Args:
            request: Natural language request
            context: Additional context
            
        Returns:
            Dict with automation and explanation
        """
        # Check rate limits (both internal and service-level)
        if not self.check_rate_limit():
            return {
                "error": "Rate limit exceeded",
                "message": f"Daily limit reached for {self.subscription_tier} tier",
                "upgrade_url": "https://openai.com/pricing"
            }
        
        if not self.rate_limiter.check_rate_limit("openai", self.subscription_tier):
            return {
                "error": "Service rate limit exceeded",
                "message": "Please wait before making another request"
            }
        
        # Sanitize request and context for privacy
        sanitized_data = {
            "request": request,
            "context": context or {}
        }
        sanitized_data = self.sanitizer.sanitize_for_llm(sanitized_data)
        
        # Log the sanitized request
        self.auditor.log_llm_request("openai", sanitized_data, sanitized=True)
        
        # Prepare the prompt with sanitized data
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            sanitized_data["request"], 
            sanitized_data.get("context")
        )
        
        try:
            # Call OpenAI API
            response = await self._call_openai_api(system_prompt, user_prompt)
            
            # Update usage stats
            self.usage_stats["requests_today"] += 1
            
            # Parse response
            result = self._parse_gpt_response(response)
            
            # Restore original entity IDs from pseudonyms
            if result.get("automation"):
                automation_str = json.dumps(result["automation"])
                restored_str = self.sanitizer.restore_from_llm(automation_str)
                result["automation"] = json.loads(restored_str)
                
                # Create automation with restored data
                automation = await self._create_automation(result["automation"], request)
                result["automation"] = automation
            
            # Restore any entity references in explanation
            if result.get("explanation"):
                result["explanation"] = self.sanitizer.restore_from_llm(result["explanation"])
            
            return result
            
        except Exception as e:
            _LOGGER.error(f"OpenAI API error: {e}")
            return {
                "error": "API Error",
                "message": str(e)
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for GPT."""
        return """You are an expert Home Assistant automation creator. Your task is to convert natural language requests into valid Home Assistant automations.

IMPORTANT RULES:
1. Always output valid YAML that Home Assistant can understand
2. Use entity_id format: domain.entity_name (e.g., light.living_room, switch.coffee_maker)
3. Include all necessary fields: id, alias, trigger, condition (optional), action
4. Support German and English inputs
5. Be smart about inferring intent

OUTPUT FORMAT:
Return a JSON object with:
{
    "automation": {
        "id": "unique_id",
        "alias": "descriptive name",
        "trigger": [...],
        "condition": [...],  // optional
        "action": [...]
    },
    "explanation": "What this automation does",
    "entities_used": ["entity.id1", "entity.id2"],
    "suggestions": ["optional improvement suggestions"]
}

COMMON PATTERNS:
- Time triggers: {"platform": "time", "at": "HH:MM:SS"}
- State triggers: {"platform": "state", "entity_id": "...", "to": "on/off"}
- Sun triggers: {"platform": "sun", "event": "sunrise/sunset", "offset": "00:30:00"}
- Numeric triggers: {"platform": "numeric_state", "entity_id": "...", "below": 10}

ACTIONS:
- Turn on/off: {"service": "homeassistant.turn_on", "entity_id": "..."}
- Notify: {"service": "notify.notify", "data": {"message": "..."}}
- Delay: {"delay": {"seconds": 30}}
- Conditions: {"condition": "state", "entity_id": "...", "state": "on"}"""
    
    def _build_user_prompt(self, request: str, context: Dict[str, Any] = None) -> str:
        """Build the user prompt with context."""
        prompt = f"Create a Home Assistant automation for: {request}\n\n"
        
        if context and context.get("entities"):
            prompt += "Available entities:\n"
            for entity_id, info in list(context["entities"].items())[:20]:
                prompt += f"- {entity_id} ({info.get('name', 'Unknown')})\n"
        
        prompt += "\nImportant: Return ONLY valid JSON, no additional text."
        
        return prompt
    
    async def _call_openai_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call the OpenAI API."""
        if not self.session:
            await self.initialize()
        
        # Retrieve API key from secure vault
        api_key = self.vault.retrieve_api_key("openai")
        if not api_key:
            raise Exception("OpenAI API key not found in vault")
        
        limits = self.rate_limits.get(self.subscription_tier, self.rate_limits["free"])
        max_tokens = min(limits["max_tokens"], self.MODELS[self.model]["max_tokens"])
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}  # Force JSON response
        }
        
        async with self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                
                # Track usage
                if "usage" in result:
                    tokens_used = result["usage"]["total_tokens"]
                    self.usage_stats["total_tokens"] += tokens_used
                    cost = (tokens_used / 1000) * self.MODELS[self.model]["cost_per_1k"]
                    self.usage_stats["total_cost"] += cost
                    
                    _LOGGER.info(f"OpenAI usage: {tokens_used} tokens, cost: ${cost:.4f}")
                
                return result
            else:
                error = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error}")
    
    def _parse_gpt_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the GPT response."""
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            if isinstance(content, str):
                result = json.loads(content)
            else:
                result = content
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            _LOGGER.error(f"Failed to parse GPT response: {e}")
            return {
                "error": "Parse error",
                "message": "Could not parse GPT response",
                "raw_response": response
            }
    
    async def _create_automation(self, automation_dict: Dict, original_request: str) -> Dict:
        """Create the automation in Home Assistant."""
        # Ensure required fields
        if "id" not in automation_dict:
            automation_dict["id"] = f"gpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if "alias" not in automation_dict:
            automation_dict["alias"] = original_request[:100]
        
        if "mode" not in automation_dict:
            automation_dict["mode"] = "single"
        
        # Add metadata
        automation_dict["description"] = f"Created by OpenAI GPT: {original_request}"
        
        return automation_dict
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        limits = self.rate_limits.get(self.subscription_tier, self.rate_limits["free"])
        
        return {
            "subscription_tier": self.subscription_tier,
            "model": self.model,
            "requests_today": self.usage_stats["requests_today"],
            "daily_limit": limits["daily_requests"],
            "total_tokens_used": self.usage_stats["total_tokens"],
            "total_cost": f"${self.usage_stats['total_cost']:.2f}",
            "remaining_requests": limits["daily_requests"] - self.usage_stats["requests_today"] 
                                 if limits["daily_requests"] != -1 else "unlimited"
        }
    
    async def test_connection(self) -> bool:
        """Test the OpenAI API connection."""
        try:
            response = await self._call_openai_api(
                "You are a test assistant.",
                "Respond with 'OK' if you receive this message."
            )
            return "choices" in response
        except Exception as e:
            _LOGGER.error(f"OpenAI connection test failed: {e}")
            return False


class OpenAIService:
    """Service wrapper for OpenAI integration."""
    
    def __init__(self, hass, config):
        """Initialize the service."""
        self.hass = hass
        self.config = config
        self.agents = {}  # Store multiple agents for different users/configs
        
    async def async_setup(self):
        """Set up the OpenAI service."""
        # Register services
        import voluptuous as vol
        import homeassistant.helpers.config_validation as cv
        
        self.hass.services.async_register(
            "haiku_automation",
            "openai_create_automation",
            self.handle_create_automation,
            schema=vol.Schema({
                vol.Required("request"): cv.string,
                vol.Optional("model", default="gpt-3.5-turbo"): cv.string,
                vol.Optional("api_key"): cv.string,
            })
        )
        
        self.hass.services.async_register(
            "haiku_automation",
            "openai_usage_stats",
            self.handle_usage_stats
        )
        
        _LOGGER.info("OpenAI Service registered for HAIKU")
    
    async def handle_create_automation(self, call):
        """Handle automation creation requests."""
        request = call.data.get("request")
        model = call.data.get("model", "gpt-3.5-turbo")
        api_key = call.data.get("api_key") or self.config.get("openai_api_key")
        
        if not api_key:
            _LOGGER.error("No OpenAI API key provided")
            return {"error": "No API key"}
        
        # Get or create agent
        agent_key = f"{api_key[:8]}_{model}"
        if agent_key not in self.agents:
            subscription = self.config.get("openai_subscription", "free")
            self.agents[agent_key] = OpenAIAgent(
                self.hass, 
                api_key, 
                model,
                subscription
            )
            await self.agents[agent_key].initialize()
        
        agent = self.agents[agent_key]
        
        # Get entity context
        context = {
            "entities": {
                state.entity_id: {
                    "name": state.attributes.get("friendly_name"),
                    "state": state.state
                }
                for state in self.hass.states.async_all()[:50]  # Limit to 50 entities
            }
        }
        
        # Process request
        result = await agent.process_request(request, context)
        
        # Save automation if successful
        if result.get("automation") and not result.get("error"):
            await self._save_automation(result["automation"])
        
        return result
    
    async def handle_usage_stats(self, call):
        """Handle usage statistics requests."""
        stats = {}
        for key, agent in self.agents.items():
            stats[key] = await agent.get_usage_stats()
        return stats
    
    async def _save_automation(self, automation):
        """Save the automation to automations.yaml."""
        import yaml
        
        automation_file = self.hass.config.path("automations.yaml")
        
        try:
            # Load existing
            with open(automation_file, 'r') as f:
                automations = yaml.safe_load(f) or []
            
            # Add new
            automations.append(automation)
            
            # Save
            with open(automation_file, 'w') as f:
                yaml.dump(automations, f, default_flow_style=False, allow_unicode=True)
            
            # Reload
            await self.hass.services.async_call('automation', 'reload')
            
            _LOGGER.info(f"Created OpenAI automation: {automation.get('id')}")
            
        except Exception as e:
            _LOGGER.error(f"Failed to save automation: {e}")