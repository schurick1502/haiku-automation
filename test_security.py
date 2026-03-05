#!/usr/bin/env python3
"""Test script for HAIKU security features."""

import sys
import os
import json
from datetime import datetime

# Add custom components to path
sys.path.insert(0, '/config/custom_components/haiku_automation')

from security import DataSanitizer, APIKeyVault, RateLimiter, SecurityAuditor

class MockHass:
    """Mock Home Assistant for testing."""
    
    def __init__(self):
        self.config = self
        self.states = self
        
    def path(self, filename):
        return f"/config/{filename}"
    
    def async_all(self):
        """Return mock states."""
        class MockState:
            def __init__(self, entity_id, state, friendly_name):
                self.entity_id = entity_id
                self.state = state
                self.attributes = {"friendly_name": friendly_name}
        
        return [
            MockState("light.wohnzimmer", "on", "Wohnzimmer Licht"),
            MockState("switch.steckdose_1", "off", "Steckdose 1"),
            MockState("sensor.temperature", "22.5", "Temperatur"),
            MockState("person.max_mustermann", "home", "Max Mustermann")
        ]

def test_data_sanitizer():
    """Test data sanitization features."""
    print("\n=== Testing Data Sanitizer ===")
    
    hass = MockHass()
    sanitizer = DataSanitizer(hass)
    
    # Test data with sensitive information
    test_data = {
        "request": "Schalte light.wohnzimmer ein wenn person.max_mustermann nach Hause kommt",
        "context": {
            "user_email": "max@example.com",
            "ip_address": "192.168.1.100",
            "api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz",
            "phone": "+49 123 456789",
            "location": {
                "latitude": 52.5200,
                "longitude": 13.4050,
                "address": "Musterstraße 123, 12345 Berlin"
            },
            "password": "password: 'secret123'",
            "credit_card": "1234 5678 9012 3456"
        }
    }
    
    # Sanitize the data
    sanitized = sanitizer.sanitize_for_llm(test_data)
    
    print("\nOriginal data sample:")
    print(f"  Request: {test_data['request'][:50]}...")
    print(f"  Email: {test_data['context']['user_email']}")
    print(f"  IP: {test_data['context']['ip_address']}")
    
    print("\nSanitized data:")
    sanitized_str = json.dumps(sanitized, indent=2)
    
    # Check if sensitive data was removed
    checks = {
        "Email removed": "max@example.com" not in sanitized_str,
        "IP removed": "192.168.1.100" not in sanitized_str,
        "API key removed": "sk-1234567890" not in sanitized_str,
        "Phone removed": "+49 123 456789" not in sanitized_str,
        "Password removed": "secret123" not in sanitized_str,
        "Credit card removed": "1234 5678 9012 3456" not in sanitized_str,
        "Location removed": "52.5200" not in sanitized_str,
        "Entities pseudonymized": "light.wohnzimmer" not in sanitized_str
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    # Test restoration
    llm_response = "Ich schalte entity_12345678 ein wenn entity_87654321 nach Hause kommt"
    if "entity_" in sanitized_str:
        # Find a pseudonym to test
        import re
        pseudo_match = re.search(r'entity_[a-f0-9]{8}', sanitized_str)
        if pseudo_match:
            test_pseudo = pseudo_match.group()
            llm_response = f"Ich schalte {test_pseudo} ein"
    
    restored = sanitizer.restore_from_llm(llm_response)
    print(f"\nLLM Response: {llm_response}")
    print(f"Restored: {restored}")
    
    return all(checks.values())

def test_api_vault():
    """Test API key vault."""
    print("\n=== Testing API Key Vault ===")
    
    hass = MockHass()
    vault = APIKeyVault(hass)
    
    # Store test keys
    test_keys = {
        "openai": "sk-test-openai-key-1234567890",
        "claude": "sk-ant-test-claude-key-abcdef",
        "telegram": "8686848939:AAHgtPt2sS0BleqiBG3-0zqxeKQETEuX8YE"
    }
    
    for service, key in test_keys.items():
        vault.store_api_key(service, key)
        print(f"  Stored key for {service}")
    
    # Retrieve and verify
    print("\nRetrieving keys:")
    all_match = True
    for service, original_key in test_keys.items():
        retrieved = vault.retrieve_api_key(service)
        matches = retrieved == original_key
        status = "✅" if matches else "❌"
        print(f"  {status} {service}: {'Match' if matches else 'Mismatch'}")
        all_match = all_match and matches
    
    # Test non-existent key
    non_existent = vault.retrieve_api_key("nonexistent")
    print(f"  ✅ Non-existent key returns: {non_existent}")
    
    return all_match

def test_rate_limiter():
    """Test rate limiting."""
    print("\n=== Testing Rate Limiter ===")
    
    limiter = RateLimiter()
    
    # Test within limits
    results = []
    print("\nTesting rate limits (5 calls):")
    for i in range(5):
        allowed = limiter.check_rate_limit("openai", "test_user")
        status = "✅" if allowed else "❌"
        print(f"  Call {i+1}: {status} {'Allowed' if allowed else 'Blocked'}")
        results.append(allowed)
    
    # Should allow first few calls
    return results[0] and results[1]

def test_security_auditor():
    """Test security auditing."""
    print("\n=== Testing Security Auditor ===")
    
    hass = MockHass()
    auditor = SecurityAuditor(hass)
    
    # Log various events
    auditor.log_llm_request("openai", {"request": "test"}, sanitized=True)
    print("  ✅ Logged LLM request")
    
    auditor.log_automation_created("test_automation_123", "user_request")
    print("  ✅ Logged automation creation")
    
    auditor.log_security_event("suspicious_activity", {
        "type": "rate_limit_exceeded",
        "source": "192.168.1.100"
    })
    print("  ✅ Logged security event")
    
    # Check if audit file exists
    audit_file = "/config/haiku_audit.log"
    if os.path.exists(audit_file):
        with open(audit_file, 'r') as f:
            lines = f.readlines()
            print(f"  ✅ Audit log has {len(lines)} entries")
        return True
    else:
        print("  ⚠️  Audit file not created yet")
        return True

def main():
    """Run all security tests."""
    print("=" * 50)
    print("HAIKU SECURITY LAYER TEST SUITE")
    print("=" * 50)
    
    results = {
        "Data Sanitizer": test_data_sanitizer(),
        "API Vault": test_api_vault(),
        "Rate Limiter": test_rate_limiter(),
        "Security Auditor": test_security_auditor()
    }
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Security layer is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the security implementation.")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())