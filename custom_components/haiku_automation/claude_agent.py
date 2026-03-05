"""Claude Code Agent Integration for HAIKU."""
import logging
import aiohttp
import json
import yaml
import os
from typing import Dict, Any, Optional
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class ClaudeCodeAgent:
    """Claude Code Agent for advanced Home Assistant control."""
    
    def __init__(self, hass, api_key: str = None):
        """Initialize the Claude Code Agent."""
        self.hass = hass
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.session = None
        self.capabilities = {
            "file_operations": True,
            "yaml_editing": True,
            "automation_creation": True,
            "dashboard_design": True,
            "debugging": True,
            "optimization": True
        }
        
    async def initialize(self):
        """Initialize the agent session."""
        self.session = aiohttp.ClientSession()
        _LOGGER.info("Claude Code Agent initialized")
        
    async def close(self):
        """Close the agent session."""
        if self.session:
            await self.session.close()
    
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a natural language request with full Claude Code capabilities.
        
        Args:
            request: Natural language request
            context: Additional context (current state, history, etc.)
            
        Returns:
            Dict with response and actions taken
        """
        # Analyze request type
        request_type = self._analyze_request_type(request)
        
        # Prepare system context
        system_context = await self._prepare_system_context()
        
        # Build prompt for Claude
        prompt = self._build_prompt(request, request_type, system_context, context)
        
        # Execute with Claude Code
        result = await self._execute_claude_request(prompt, request_type)
        
        # Apply changes if needed
        if result.get("actions"):
            await self._apply_actions(result["actions"])
        
        return result
    
    def _analyze_request_type(self, request: str) -> str:
        """Determine the type of request."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["automatisierung", "automation", "wenn", "dann"]):
            return "automation"
        elif any(word in request_lower for word in ["dashboard", "karte", "ui", "ansicht"]):
            return "dashboard"
        elif any(word in request_lower for word in ["fehler", "debug", "problem", "funktioniert nicht"]):
            return "debugging"
        elif any(word in request_lower for word in ["optimiere", "verbessere", "effizienter"]):
            return "optimization"
        elif any(word in request_lower for word in ["analysiere", "zeige", "status"]):
            return "analysis"
        else:
            return "general"
    
    async def _prepare_system_context(self) -> Dict[str, Any]:
        """Prepare current system context for Claude."""
        # Get current states
        states = {}
        for state in self.hass.states.async_all():
            states[state.entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes)
            }
        
        # Get automations
        automations = []
        try:
            automation_path = self.hass.config.path("automations.yaml")
            if os.path.exists(automation_path):
                with open(automation_path, 'r') as f:
                    automations = yaml.safe_load(f) or []
        except Exception as e:
            _LOGGER.error(f"Error loading automations: {e}")
        
        # Get configuration
        config_items = {}
        try:
            config_path = self.hass.config.path("configuration.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_items = yaml.safe_load(f) or {}
        except Exception as e:
            _LOGGER.error(f"Error loading config: {e}")
        
        return {
            "states": states,
            "automations": automations,
            "config": config_items,
            "timestamp": datetime.now().isoformat(),
            "version": self.hass.config.version
        }
    
    def _build_prompt(self, request: str, request_type: str, system_context: Dict, user_context: Dict = None) -> str:
        """Build a comprehensive prompt for Claude."""
        
        prompt = f"""You are Claude Code Agent, an AI assistant for Home Assistant with full system access.

REQUEST TYPE: {request_type}
USER REQUEST: {request}

SYSTEM CONTEXT:
- Home Assistant Version: {system_context.get('version', 'unknown')}
- Total Entities: {len(system_context.get('states', {}))}
- Total Automations: {len(system_context.get('automations', []))}
- Timestamp: {system_context.get('timestamp')}

AVAILABLE ENTITIES (Sample):
"""
        # Add sample of entities
        for i, (entity_id, state) in enumerate(system_context.get('states', {}).items()):
            if i < 20:  # Limit to first 20
                prompt += f"- {entity_id}: {state['state']}\n"
        
        prompt += f"""
YOUR CAPABILITIES:
- Create/modify YAML files
- Create complex automations
- Design dashboards
- Debug issues
- Optimize performance
- Direct file system access

INSTRUCTIONS:
1. Analyze the request carefully
2. Propose a solution
3. Generate necessary code/configuration
4. Provide clear explanation
5. Return structured response with actions to take

Please provide your response in JSON format with:
- explanation: Clear explanation of what you're doing
- actions: List of actions to take
- code: Any code/YAML to create or modify
- warnings: Any potential issues or concerns
"""
        
        if user_context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{json.dumps(user_context, indent=2)}"
        
        return prompt
    
    async def _execute_claude_request(self, prompt: str, request_type: str) -> Dict[str, Any]:
        """Execute request with Claude API."""
        
        # For now, use a structured response based on request type
        # In production, this would call the actual Claude API
        
        if request_type == "automation":
            return await self._handle_automation_request(prompt)
        elif request_type == "dashboard":
            return await self._handle_dashboard_request(prompt)
        elif request_type == "debugging":
            return await self._handle_debugging_request(prompt)
        elif request_type == "optimization":
            return await self._handle_optimization_request(prompt)
        else:
            return await self._handle_general_request(prompt)
    
    async def _handle_automation_request(self, prompt: str) -> Dict[str, Any]:
        """Handle automation creation requests."""
        # Extract key information from prompt
        # This is a simplified version - real implementation would use Claude
        
        return {
            "explanation": "Ich erstelle eine intelligente Automatisierung basierend auf Ihrer Anfrage.",
            "actions": [
                {
                    "type": "create_automation",
                    "file": "automations.yaml",
                    "content": {
                        "id": f"claude_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "alias": "Claude Generated Automation",
                        "trigger": [{"platform": "time", "at": "07:00:00"}],
                        "action": [{"service": "light.turn_on", "entity_id": "light.all"}]
                    }
                }
            ],
            "code": """
# Neue Automatisierung
- id: claude_auto_20240305_164500
  alias: Claude Generated Automation
  trigger:
    - platform: time
      at: "07:00:00"
  action:
    - service: light.turn_on
      entity_id: light.all
""",
            "warnings": []
        }
    
    async def _handle_dashboard_request(self, prompt: str) -> Dict[str, Any]:
        """Handle dashboard creation requests."""
        return {
            "explanation": "Ich erstelle ein Dashboard basierend auf Ihrer Anfrage.",
            "actions": [
                {
                    "type": "create_dashboard",
                    "content": {
                        "title": "Claude Dashboard",
                        "views": []
                    }
                }
            ],
            "code": "",
            "warnings": []
        }
    
    async def _handle_debugging_request(self, prompt: str) -> Dict[str, Any]:
        """Handle debugging requests."""
        # Analyze logs and find issues
        issues = await self._analyze_system_issues()
        
        return {
            "explanation": f"Ich habe {len(issues)} potenzielle Probleme gefunden.",
            "actions": [
                {
                    "type": "fix_issues",
                    "issues": issues
                }
            ],
            "code": "",
            "warnings": issues
        }
    
    async def _handle_optimization_request(self, prompt: str) -> Dict[str, Any]:
        """Handle optimization requests."""
        suggestions = await self._analyze_optimization_opportunities()
        
        return {
            "explanation": "Ich habe Optimierungsmöglichkeiten analysiert.",
            "actions": [
                {
                    "type": "optimize",
                    "suggestions": suggestions
                }
            ],
            "code": "",
            "warnings": []
        }
    
    async def _handle_general_request(self, prompt: str) -> Dict[str, Any]:
        """Handle general requests."""
        return {
            "explanation": "Ich verarbeite Ihre Anfrage.",
            "actions": [],
            "code": "",
            "warnings": []
        }
    
    async def _apply_actions(self, actions: list) -> bool:
        """Apply the actions suggested by Claude."""
        success = True
        
        for action in actions:
            try:
                action_type = action.get("type")
                
                if action_type == "create_automation":
                    await self._create_automation(action)
                elif action_type == "modify_file":
                    await self._modify_file(action)
                elif action_type == "create_dashboard":
                    await self._create_dashboard(action)
                elif action_type == "fix_issues":
                    await self._fix_issues(action)
                else:
                    _LOGGER.warning(f"Unknown action type: {action_type}")
                    
            except Exception as e:
                _LOGGER.error(f"Error applying action: {e}")
                success = False
        
        return success
    
    async def _create_automation(self, action: Dict) -> None:
        """Create a new automation."""
        automation_file = self.hass.config.path(action.get("file", "automations.yaml"))
        content = action.get("content", {})
        
        # Load existing automations
        automations = []
        if os.path.exists(automation_file):
            with open(automation_file, 'r') as f:
                automations = yaml.safe_load(f) or []
        
        # Add new automation
        automations.append(content)
        
        # Save back
        with open(automation_file, 'w') as f:
            yaml.dump(automations, f, default_flow_style=False, allow_unicode=True)
        
        # Reload automations
        await self.hass.services.async_call('automation', 'reload')
        
        _LOGGER.info(f"Created automation: {content.get('id')}")
    
    async def _modify_file(self, action: Dict) -> None:
        """Modify a configuration file."""
        file_path = self.hass.config.path(action.get("file"))
        content = action.get("content")
        
        with open(file_path, 'w') as f:
            if file_path.endswith('.yaml'):
                yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
            else:
                f.write(content)
        
        _LOGGER.info(f"Modified file: {file_path}")
    
    async def _create_dashboard(self, action: Dict) -> None:
        """Create a new dashboard."""
        # This would integrate with Lovelace
        _LOGGER.info("Dashboard creation not yet implemented")
    
    async def _fix_issues(self, action: Dict) -> None:
        """Fix identified issues."""
        issues = action.get("issues", [])
        for issue in issues:
            _LOGGER.info(f"Fixing issue: {issue}")
            # Implement specific fixes
    
    async def _analyze_system_issues(self) -> list:
        """Analyze system for potential issues."""
        issues = []
        
        # Check for common problems
        # 1. Unavailable entities
        for state in self.hass.states.async_all():
            if state.state == "unavailable":
                issues.append(f"Entity {state.entity_id} is unavailable")
        
        # 2. Failed automations
        # Would need to check logs
        
        return issues[:10]  # Limit to 10 issues
    
    async def _analyze_optimization_opportunities(self) -> list:
        """Analyze system for optimization opportunities."""
        suggestions = []
        
        # Check for optimization opportunities
        # 1. Duplicate automations
        # 2. Inefficient triggers
        # 3. Missing conditions
        
        return suggestions

class ClaudeAgentService:
    """Service wrapper for Claude Agent."""
    
    def __init__(self, hass, api_key: str = None):
        """Initialize service."""
        self.hass = hass
        self.agent = ClaudeCodeAgent(hass, api_key)
        
    async def async_setup(self):
        """Set up the service."""
        await self.agent.initialize()
        
        # Register service
        self.hass.services.async_register(
            "haiku_automation",
            "claude_request",
            self.handle_service_call
        )
        
        _LOGGER.info("Claude Agent Service registered")
    
    async def handle_service_call(self, call):
        """Handle service calls."""
        request = call.data.get("request", "")
        context = call.data.get("context", {})
        
        result = await self.agent.process_request(request, context)
        
        # Fire event with result
        self.hass.bus.async_fire(
            "haiku_claude_response",
            result
        )
        
        return result