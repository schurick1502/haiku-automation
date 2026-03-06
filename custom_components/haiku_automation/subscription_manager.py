"""Subscription Manager for HAIKU OpenAI Integration."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

_LOGGER = logging.getLogger(__name__)

class SubscriptionManager:
    """Manage OpenAI subscription tiers and usage limits."""
    
    TIERS = {
        "free": {
            "name": "Free Tier",
            "daily_limit": 10,
            "max_tokens": 2000,
            "models": ["gpt-3.5-turbo"],
            "features": ["basic_automation"],
            "price": 0,
            "description": "Perfect for trying out HAIKU"
        },
        "basic": {
            "name": "Basic",
            "daily_limit": 100,
            "max_tokens": 4000,
            "models": ["gpt-3.5-turbo", "gpt-4-turbo"],
            "features": ["basic_automation", "debugging", "suggestions"],
            "price": 9.99,
            "description": "For regular home automation users"
        },
        "pro": {
            "name": "Professional",
            "daily_limit": 1000,
            "max_tokens": 8000,
            "models": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"],
            "features": ["basic_automation", "debugging", "suggestions", "analytics", "learning"],
            "price": 29.99,
            "description": "For power users and enthusiasts"
        },
        "enterprise": {
            "name": "Enterprise",
            "daily_limit": -1,  # Unlimited
            "max_tokens": 128000,
            "models": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"],
            "features": ["all"],
            "price": 99.99,
            "description": "Unlimited access for professionals"
        }
    }
    
    def __init__(self, hass, subscription_tier: str = "free"):
        """Initialize the subscription manager."""
        self.hass = hass
        self.tier = subscription_tier.lower()
        self.usage_file = hass.config.path("haiku_usage.json")
        self.usage = self._load_usage()
        
    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from file."""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Reset if new day
                    last_reset = datetime.fromisoformat(data.get('last_reset', '2000-01-01'))
                    if last_reset.date() != datetime.now().date():
                        data['daily_count'] = 0
                        data['last_reset'] = datetime.now().isoformat()
                    return data
        except Exception as e:
            _LOGGER.error(f"Failed to load usage data: {e}")
        
        return {
            'daily_count': 0,
            'total_count': 0,
            'last_reset': datetime.now().isoformat(),
            'tier': self.tier
        }
    
    def _save_usage(self) -> None:
        """Save usage data to file."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            _LOGGER.error(f"Failed to save usage data: {e}")
    
    def check_limit(self) -> tuple[bool, str]:
        """
        Check if user is within their subscription limits.
        
        Returns:
            Tuple of (allowed, message)
        """
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        
        # Check daily limit
        if tier_info['daily_limit'] != -1:  # -1 means unlimited
            if self.usage['daily_count'] >= tier_info['daily_limit']:
                remaining_hours = 24 - datetime.now().hour
                return False, f"Daily limit reached ({tier_info['daily_limit']} requests). Resets in {remaining_hours} hours. Consider upgrading to {self._suggest_upgrade()}"
        
        return True, f"Request allowed. {self.get_remaining_requests()} requests remaining today."
    
    def record_usage(self, tokens_used: int = 0) -> None:
        """Record a usage event."""
        self.usage['daily_count'] += 1
        self.usage['total_count'] += 1
        self.usage['last_used'] = datetime.now().isoformat()
        
        if 'tokens_used' not in self.usage:
            self.usage['tokens_used'] = 0
        self.usage['tokens_used'] += tokens_used
        
        self._save_usage()
        
        # Log usage
        _LOGGER.info(f"OpenAI usage recorded: {self.usage['daily_count']}/{self.TIERS[self.tier]['daily_limit']} daily requests")
    
    def get_remaining_requests(self) -> int:
        """Get remaining requests for today."""
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        
        if tier_info['daily_limit'] == -1:
            return -1  # Unlimited
        
        return max(0, tier_info['daily_limit'] - self.usage['daily_count'])
    
    def can_use_model(self, model: str) -> bool:
        """Check if the current tier can use a specific model."""
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        return model in tier_info['models']
    
    def can_use_feature(self, feature: str) -> bool:
        """Check if the current tier can use a specific feature."""
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        return feature in tier_info['features'] or 'all' in tier_info['features']
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for current tier."""
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        return tier_info['max_tokens']
    
    def _suggest_upgrade(self) -> str:
        """Suggest the next tier upgrade."""
        tier_order = ['free', 'basic', 'pro', 'enterprise']
        current_index = tier_order.index(self.tier)
        
        if current_index < len(tier_order) - 1:
            next_tier = tier_order[current_index + 1]
            return f"{self.TIERS[next_tier]['name']} (${self.TIERS[next_tier]['price']}/month)"
        
        return "Enterprise (contact sales)"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        tier_info = self.TIERS.get(self.tier, self.TIERS['free'])
        
        return {
            'subscription': {
                'tier': self.tier,
                'name': tier_info['name'],
                'price': f"${tier_info['price']}/month",
                'features': tier_info['features']
            },
            'usage': {
                'daily_requests': self.usage['daily_count'],
                'daily_limit': tier_info['daily_limit'],
                'remaining_today': self.get_remaining_requests(),
                'total_requests': self.usage.get('total_count', 0),
                'tokens_used': self.usage.get('tokens_used', 0),
                'last_used': self.usage.get('last_used', 'Never')
            },
            'limits': {
                'max_tokens': tier_info['max_tokens'],
                'available_models': tier_info['models']
            },
            'upgrade': {
                'available': self.tier != 'enterprise',
                'next_tier': self._suggest_upgrade() if self.tier != 'enterprise' else None,
                'benefits': self._get_upgrade_benefits()
            }
        }
    
    def _get_upgrade_benefits(self) -> list[str]:
        """Get benefits of upgrading."""
        tier_order = ['free', 'basic', 'pro', 'enterprise']
        current_index = tier_order.index(self.tier)
        
        if current_index >= len(tier_order) - 1:
            return []
        
        next_tier = tier_order[current_index + 1]
        next_info = self.TIERS[next_tier]
        current_info = self.TIERS[self.tier]
        
        benefits = []
        
        # More requests
        if next_info['daily_limit'] == -1:
            benefits.append("Unlimited daily requests")
        else:
            increase = next_info['daily_limit'] - current_info['daily_limit']
            benefits.append(f"{increase} more requests per day")
        
        # More tokens
        if next_info['max_tokens'] > current_info['max_tokens']:
            benefits.append(f"Up to {next_info['max_tokens']} tokens per request")
        
        # More models
        new_models = set(next_info['models']) - set(current_info['models'])
        if new_models:
            benefits.append(f"Access to {', '.join(new_models)}")
        
        # More features
        new_features = set(next_info['features']) - set(current_info['features'])
        if new_features:
            benefits.append(f"New features: {', '.join(new_features)}")
        
        return benefits
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate OpenAI API key format.
        
        Note: This only validates format, not actual validity with OpenAI.
        """
        if not api_key:
            return False
        
        # OpenAI keys start with 'sk-' and are typically 48+ characters
        if not api_key.startswith('sk-'):
            return False
        
        if len(api_key) < 40:
            return False
        
        # Check for valid characters (alphanumeric and hyphens)
        import re
        if not re.match(r'^sk-[a-zA-Z0-9-]+$', api_key):
            return False
        
        return True
    
    async def test_connection(self, api_key: str) -> tuple[bool, str]:
        """
        Test OpenAI API connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.validate_api_key(api_key):
            return False, "Invalid API key format. Should start with 'sk-'"
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Simple test request
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        return True, "API key is valid and working"
                    elif response.status == 401:
                        return False, "Invalid API key. Please check your key"
                    elif response.status == 429:
                        return False, "Rate limit exceeded. Please wait and try again"
                    else:
                        return False, f"API error: {response.status}"
                        
        except Exception as e:
            _LOGGER.error(f"Failed to test OpenAI connection: {e}")
            return False, f"Connection error: {str(e)}"