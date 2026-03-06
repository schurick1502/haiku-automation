"""Security and Privacy Layer for HAIKU Automation Builder."""
import hashlib
import re
import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import secrets
import base64
from cryptography.fernet import Fernet

_LOGGER = logging.getLogger(__name__)


class DataSanitizer:
    """Sanitize and pseudonymize sensitive data before sending to LLMs."""
    
    def __init__(self, hass):
        """Initialize the sanitizer."""
        self.hass = hass
        self.entity_map = {}
        self.reverse_map = {}
        self.sensitive_patterns = [
            # IP Addresses
            (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'IP_ADDRESS'),
            # MAC Addresses
            (r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', 'MAC_ADDRESS'),
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
            # Phone numbers (improved pattern for international formats)
            (r'\+?[0-9\s\-\(\)\.]{7,20}', 'PHONE'),
            # Credit card numbers
            (r'\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b', 'CREDIT_CARD'),
            # Social Security Numbers
            (r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b', 'SSN'),
            # API Keys (generic pattern)
            (r'\b[A-Za-z0-9]{32,}\b', 'API_KEY'),
            # Passwords in config (simplified to avoid JSON corruption)
            (r'password\s*:\s*["\'][^"\']+["\']', 'PASSWORD'),
            # Tokens (simplified to avoid JSON corruption)
            (r'token\s*:\s*["\'][^"\']+["\']', 'TOKEN'),
            # GPS Coordinates
            (r'[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)', 'GPS_COORD'),
        ]
        self.session_key = self._generate_session_key()
        
    def _generate_session_key(self):
        """Generate a unique session key for pseudonymization."""
        return secrets.token_hex(16)
    
    def pseudonymize_entities(self, data: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace real entity IDs with pseudonyms.
        
        Returns:
            Tuple of (sanitized_data, mapping_dict)
        """
        sanitized = data
        mapping = {}
        
        # Get all entities from Home Assistant
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            friendly_name = state.attributes.get('friendly_name', '')
            
            # Create pseudonym
            pseudo_id = f"entity_{hashlib.md5(f'{entity_id}{self.session_key}'.encode()).hexdigest()[:8]}"
            
            # Store mapping
            mapping[pseudo_id] = entity_id
            self.entity_map[entity_id] = pseudo_id
            self.reverse_map[pseudo_id] = entity_id
            
            # Replace in data
            sanitized = sanitized.replace(entity_id, pseudo_id)
            if friendly_name:
                # Create safe friendly name
                safe_name = f"Device_{pseudo_id[-4:]}"
                sanitized = sanitized.replace(friendly_name, safe_name)
        
        return sanitized, mapping
    
    def remove_sensitive_data(self, data: str) -> Tuple[str, List[Dict]]:
        """
        Remove or mask sensitive information.
        
        Returns:
            Tuple of (sanitized_data, removed_items)
        """
        sanitized = data
        removed = []
        
        for pattern, data_type in self.sensitive_patterns:
            matches = re.finditer(pattern, sanitized)
            for match in matches:
                original = match.group(0)
                replacement = f"[REDACTED_{data_type}_{len(removed)}]"
                
                removed.append({
                    'type': data_type,
                    'original': original,
                    'replacement': replacement,
                    'position': match.span()
                })
                
                sanitized = sanitized.replace(original, replacement)
        
        return sanitized, removed
    
    def sanitize_for_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main sanitization function for LLM requests.
        
        Args:
            data: The data to be sent to LLM
            
        Returns:
            Sanitized data safe for external transmission
        """
        # Convert to string for processing
        data_str = json.dumps(data, ensure_ascii=False)
        
        # Step 1: Pseudonymize entities first (before other replacements)
        data_str, entity_mapping = self.pseudonymize_entities(data_str)
        
        # Step 2: Remove sensitive patterns
        data_str, sensitive_removed = self.remove_sensitive_data(data_str)
        
        # Step 3: Remove location data
        data_str = self._remove_location_data(data_str)
        
        # Step 4: Sanitize personal information
        data_str = self._sanitize_personal_info(data_str)
        
        # Try to convert back to dict, if it fails return as string
        try:
            sanitized_data = json.loads(data_str)
        except json.JSONDecodeError:
            # If JSON is corrupted, return a safe structure
            sanitized_data = {
                "sanitized_content": data_str,
                "parse_error": True
            }
        
        # Store sanitization info for reversal
        sanitized_data['_sanitization_info'] = {
            'session_key': self.session_key,
            'timestamp': datetime.now().isoformat(),
            'items_removed': len(sensitive_removed),
            'entities_mapped': len(entity_mapping)
        }
        
        _LOGGER.info(f"Sanitized data: Removed {len(sensitive_removed)} sensitive items, "
                    f"mapped {len(entity_mapping)} entities")
        
        return sanitized_data
    
    def _remove_location_data(self, data: str) -> str:
        """Remove location-specific information."""
        # Remove latitude/longitude
        data = re.sub(r'"latitude"\s*:\s*[^,}]+', '"latitude": "REDACTED"', data)
        data = re.sub(r'"longitude"\s*:\s*[^,}]+', '"longitude": "REDACTED"', data)
        
        # Remove address information
        data = re.sub(r'"address"\s*:\s*"[^"]*"', '"address": "REDACTED"', data)
        data = re.sub(r'"location"\s*:\s*"[^"]*"', '"location": "REDACTED"', data)
        
        return data
    
    def _sanitize_personal_info(self, data: str) -> str:
        """Remove personal identifying information."""
        # Remove common name patterns
        data = re.sub(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 'PERSON_NAME', data)
        
        # Remove URLs with personal domains
        data = re.sub(r'https?://[^\s/]+\.(duckdns|no-ip|dynv6|dynu)\.[^\s]*', 'PERSONAL_URL', data)
        
        return data
    
    def restore_from_llm(self, llm_response: str) -> str:
        """
        Restore original entity IDs and data from LLM response.
        
        Args:
            llm_response: The response from LLM with pseudonymized data
            
        Returns:
            Response with original entity IDs restored
        """
        restored = llm_response
        
        # Restore entity IDs
        for pseudo_id, real_id in self.reverse_map.items():
            restored = restored.replace(pseudo_id, real_id)
        
        # Note: Sensitive data that was removed cannot be restored (by design)
        
        return restored


class APIKeyVault:
    """Secure storage for API keys."""
    
    def __init__(self, hass):
        """Initialize the vault."""
        self.hass = hass
        self.vault_file = hass.config.path(".haiku_vault")
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
        
    def _get_or_create_master_key(self) -> bytes:
        """Get or create a master encryption key."""
        key_file = self.hass.config.path(".haiku_key")
        
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            import os
            os.chmod(key_file, 0o600)
            return key
    
    def store_api_key(self, service: str, api_key: str) -> None:
        """
        Securely store an API key.
        
        Args:
            service: The service name (openai, claude, etc.)
            api_key: The API key to store
        """
        # Encrypt the API key
        encrypted = self.cipher.encrypt(api_key.encode())
        
        # Load existing vault
        vault = self._load_vault()
        
        # Add encrypted key
        vault[service] = {
            'encrypted_key': base64.b64encode(encrypted).decode(),
            'stored_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        # Save vault
        self._save_vault(vault)
        
        _LOGGER.info(f"API key for {service} stored securely")
    
    def retrieve_api_key(self, service: str) -> str:
        """
        Retrieve a decrypted API key.
        
        Args:
            service: The service name
            
        Returns:
            Decrypted API key or None if not found
        """
        vault = self._load_vault()
        
        if service not in vault:
            return None
        
        try:
            # Decrypt the key
            encrypted = base64.b64decode(vault[service]['encrypted_key'])
            decrypted = self.cipher.decrypt(encrypted)
            
            # Update last used
            vault[service]['last_used'] = datetime.now().isoformat()
            self._save_vault(vault)
            
            return decrypted.decode()
        except Exception as e:
            _LOGGER.error(f"Failed to decrypt API key for {service}: {e}")
            return None
    
    def _load_vault(self) -> Dict:
        """Load the vault file."""
        try:
            with open(self.vault_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_vault(self, vault: Dict) -> None:
        """Save the vault file."""
        with open(self.vault_file, 'w') as f:
            json.dump(vault, f, indent=2)
        # Set restrictive permissions
        import os
        os.chmod(self.vault_file, 0o600)


class RateLimiter:
    """Rate limiting for API calls."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.call_history = {}
        self.limits = {
            'openai': {'per_minute': 20, 'per_hour': 100, 'per_day': 1000},
            'claude': {'per_minute': 30, 'per_hour': 150, 'per_day': 2000},
            'default': {'per_minute': 10, 'per_hour': 50, 'per_day': 500}
        }
    
    def check_rate_limit(self, service: str, user_id: str = 'default') -> bool:
        """
        Check if a call is within rate limits.
        
        Args:
            service: The service being called
            user_id: Identifier for the user/integration
            
        Returns:
            True if within limits, False otherwise
        """
        key = f"{service}:{user_id}"
        now = datetime.now()
        
        if key not in self.call_history:
            self.call_history[key] = []
        
        # Clean old entries
        self.call_history[key] = [
            t for t in self.call_history[key] 
            if (now - t).total_seconds() < 86400  # Keep last 24 hours
        ]
        
        # Get limits
        limits = self.limits.get(service, self.limits['default'])
        
        # Check per minute
        recent_minute = [
            t for t in self.call_history[key]
            if (now - t).total_seconds() < 60
        ]
        if len(recent_minute) >= limits['per_minute']:
            _LOGGER.warning(f"Rate limit exceeded for {service}: per_minute")
            return False
        
        # Check per hour
        recent_hour = [
            t for t in self.call_history[key]
            if (now - t).total_seconds() < 3600
        ]
        if len(recent_hour) >= limits['per_hour']:
            _LOGGER.warning(f"Rate limit exceeded for {service}: per_hour")
            return False
        
        # Check per day
        if len(self.call_history[key]) >= limits['per_day']:
            _LOGGER.warning(f"Rate limit exceeded for {service}: per_day")
            return False
        
        # Add this call
        self.call_history[key].append(now)
        
        return True


class SecurityAuditor:
    """Audit and log security-relevant events."""
    
    def __init__(self, hass):
        """Initialize the auditor."""
        self.hass = hass
        self.audit_file = hass.config.path("haiku_audit.log")
        
    def log_llm_request(self, service: str, request_data: Dict, sanitized: bool = False):
        """Log an LLM request for auditing."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'type': 'llm_request',
            'sanitized': sanitized,
            'request_size': len(json.dumps(request_data)),
            'entities_count': len([k for k in request_data.keys() if 'entity' in k.lower()])
        }
        
        self._write_audit_log(entry)
    
    def log_automation_created(self, automation_id: str, source: str):
        """Log when an automation is created."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'automation_created',
            'automation_id': automation_id,
            'source': source
        }
        
        self._write_audit_log(entry)
    
    def log_security_event(self, event_type: str, details: Dict):
        """Log a security event."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'security_event',
            'event_type': event_type,
            'details': details
        }
        
        self._write_audit_log(entry)
        
        # Also log to Home Assistant
        _LOGGER.warning(f"Security event: {event_type} - {details}")
    
    def _write_audit_log(self, entry: Dict):
        """Write an entry to the audit log."""
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')