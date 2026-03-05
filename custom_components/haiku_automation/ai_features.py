"""Advanced AI Features for HAIKU Automation Builder."""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter
import pickle
import os

_LOGGER = logging.getLogger(__name__)

class AutomationDebugger:
    """AI-powered automation debugging."""
    
    def __init__(self, hass):
        """Initialize the debugger."""
        self.hass = hass
        self.execution_history = []
        self.error_patterns = {}
        
    async def debug_automation(self, automation_id: str, issue_description: str = None) -> Dict[str, Any]:
        """
        Debug why an automation didn't work as expected.
        
        Args:
            automation_id: The automation to debug
            issue_description: Optional description of the issue
            
        Returns:
            Detailed debugging report with solutions
        """
        report = {
            'automation_id': automation_id,
            'status': 'analyzing',
            'issues_found': [],
            'suggestions': [],
            'last_triggered': None,
            'execution_trace': []
        }
        
        # Get automation details
        automation = await self._get_automation_details(automation_id)
        if not automation:
            report['status'] = 'not_found'
            return report
        
        # Check last execution
        last_run = await self._check_last_execution(automation_id)
        report['last_triggered'] = last_run.get('timestamp')
        
        # Analyze triggers
        trigger_issues = self._analyze_triggers(automation.get('trigger', []))
        report['issues_found'].extend(trigger_issues)
        
        # Analyze conditions
        condition_issues = self._analyze_conditions(automation.get('condition', []))
        report['issues_found'].extend(condition_issues)
        
        # Analyze actions
        action_issues = self._analyze_actions(automation.get('action', []))
        report['issues_found'].extend(action_issues)
        
        # Check for conflicts
        conflicts = await self._check_conflicts(automation)
        report['issues_found'].extend(conflicts)
        
        # Generate suggestions
        report['suggestions'] = self._generate_solutions(report['issues_found'])
        
        # Set final status
        report['status'] = 'issues_found' if report['issues_found'] else 'no_issues'
        
        return report
    
    def _analyze_triggers(self, triggers: List[Dict]) -> List[Dict]:
        """Analyze trigger configuration for issues."""
        issues = []
        
        for i, trigger in enumerate(triggers):
            # Check for invalid entity IDs
            if 'entity_id' in trigger:
                entity_id = trigger['entity_id']
                if not self.hass.states.get(entity_id):
                    issues.append({
                        'type': 'invalid_entity',
                        'severity': 'critical',
                        'trigger_index': i,
                        'message': f"Entity {entity_id} does not exist",
                        'fix': f"Check if {entity_id} is correctly spelled or still exists"
                    })
            
            # Check time triggers
            if trigger.get('platform') == 'time':
                time_str = trigger.get('at')
                if not self._is_valid_time(time_str):
                    issues.append({
                        'type': 'invalid_time',
                        'severity': 'critical',
                        'trigger_index': i,
                        'message': f"Invalid time format: {time_str}",
                        'fix': "Use format HH:MM:SS (e.g., 07:30:00)"
                    })
            
            # Check state triggers
            if trigger.get('platform') == 'state':
                if 'to' not in trigger and 'from' not in trigger:
                    issues.append({
                        'type': 'missing_state',
                        'severity': 'warning',
                        'trigger_index': i,
                        'message': "State trigger without 'to' or 'from' will trigger on ANY state change",
                        'fix': "Add 'to' or 'from' to specify exact state changes"
                    })
        
        return issues
    
    def _analyze_conditions(self, conditions: List[Dict]) -> List[Dict]:
        """Analyze condition configuration for issues."""
        issues = []
        
        for i, condition in enumerate(conditions):
            # Check entity existence
            if 'entity_id' in condition:
                entity_id = condition['entity_id']
                if not self.hass.states.get(entity_id):
                    issues.append({
                        'type': 'invalid_entity',
                        'severity': 'critical',
                        'condition_index': i,
                        'message': f"Condition entity {entity_id} does not exist",
                        'fix': f"Remove or update condition with valid entity"
                    })
            
            # Check for impossible conditions
            if condition.get('condition') == 'time':
                after = condition.get('after')
                before = condition.get('before')
                if after and before and after > before:
                    issues.append({
                        'type': 'impossible_condition',
                        'severity': 'critical',
                        'condition_index': i,
                        'message': f"Time condition can never be true (after {after} is later than before {before})",
                        'fix': "Swap after and before times or adjust the condition"
                    })
        
        return issues
    
    def _analyze_actions(self, actions: List[Dict]) -> List[Dict]:
        """Analyze action configuration for issues."""
        issues = []
        
        for i, action in enumerate(actions):
            # Check service calls
            if 'service' in action:
                service = action['service']
                # Check if service exists
                domain, service_name = service.split('.') if '.' in service else (None, None)
                if domain and not self._service_exists(domain, service_name):
                    issues.append({
                        'type': 'invalid_service',
                        'severity': 'critical',
                        'action_index': i,
                        'message': f"Service {service} does not exist",
                        'fix': "Check service name or ensure integration is loaded"
                    })
            
            # Check entity targets
            if 'entity_id' in action or 'target' in action:
                entities = action.get('entity_id', [])
                if isinstance(entities, str):
                    entities = [entities]
                elif 'target' in action:
                    entities = action['target'].get('entity_id', [])
                    if isinstance(entities, str):
                        entities = [entities]
                
                for entity_id in entities:
                    if not self.hass.states.get(entity_id):
                        issues.append({
                            'type': 'invalid_entity',
                            'severity': 'critical',
                            'action_index': i,
                            'message': f"Action target {entity_id} does not exist",
                            'fix': f"Update action with valid entity ID"
                        })
        
        return issues
    
    async def _check_conflicts(self, automation: Dict) -> List[Dict]:
        """Check for conflicts with other automations."""
        conflicts = []
        
        # Get all other automations
        all_automations = await self._get_all_automations()
        
        for other in all_automations:
            if other['id'] == automation['id']:
                continue
            
            # Check for same triggers
            if self._triggers_overlap(automation.get('trigger', []), other.get('trigger', [])):
                # Check if actions conflict
                if self._actions_conflict(automation.get('action', []), other.get('action', [])):
                    conflicts.append({
                        'type': 'automation_conflict',
                        'severity': 'warning',
                        'conflicting_automation': other['id'],
                        'message': f"Conflicts with automation '{other.get('alias', other['id'])}'",
                        'fix': "Add conditions to differentiate or combine automations"
                    })
        
        return conflicts
    
    def _generate_solutions(self, issues: List[Dict]) -> List[str]:
        """Generate solution suggestions based on found issues."""
        solutions = []
        
        # Group issues by type
        issue_types = defaultdict(list)
        for issue in issues:
            issue_types[issue['type']].append(issue)
        
        # Generate targeted solutions
        if 'invalid_entity' in issue_types:
            solutions.append("Run entity discovery to find correct entity IDs")
            solutions.append("Check if devices are still connected and powered on")
        
        if 'automation_conflict' in issue_types:
            solutions.append("Consider merging conflicting automations")
            solutions.append("Add time or state conditions to prevent conflicts")
        
        if 'impossible_condition' in issue_types:
            solutions.append("Review and fix logical errors in conditions")
        
        return solutions
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Check if time string is valid."""
        if not time_str:
            return False
        try:
            datetime.strptime(time_str, "%H:%M:%S")
            return True
        except ValueError:
            return False
    
    def _service_exists(self, domain: str, service: str) -> bool:
        """Check if a service exists."""
        # This is a simplified check
        return domain in ['homeassistant', 'light', 'switch', 'climate', 'cover', 'scene', 'script', 'automation']
    
    def _triggers_overlap(self, triggers1: List, triggers2: List) -> bool:
        """Check if two trigger sets overlap."""
        for t1 in triggers1:
            for t2 in triggers2:
                if t1.get('platform') == t2.get('platform'):
                    if t1.get('entity_id') == t2.get('entity_id'):
                        return True
        return False
    
    def _actions_conflict(self, actions1: List, actions2: List) -> bool:
        """Check if two action sets conflict."""
        entities1 = set()
        entities2 = set()
        
        for action in actions1:
            if 'entity_id' in action:
                entities1.add(action['entity_id'])
        
        for action in actions2:
            if 'entity_id' in action:
                entities2.add(action['entity_id'])
        
        # Check if same entities are being controlled
        return bool(entities1 & entities2)
    
    async def _get_automation_details(self, automation_id: str) -> Optional[Dict]:
        """Get automation details."""
        # This would fetch from automations.yaml
        return {}
    
    async def _check_last_execution(self, automation_id: str) -> Dict:
        """Check last execution of automation."""
        return {'timestamp': datetime.now() - timedelta(hours=2)}
    
    async def _get_all_automations(self) -> List[Dict]:
        """Get all automations."""
        return []


class SmartLearning:
    """Machine learning system that improves over time."""
    
    def __init__(self, hass):
        """Initialize smart learning."""
        self.hass = hass
        self.learning_data_file = hass.config.path("haiku_learning.pkl")
        self.patterns = defaultdict(list)
        self.user_preferences = {}
        self.correction_history = []
        self.load_learning_data()
    
    def learn_from_correction(self, original: Dict, corrected: Dict, feedback: str = None):
        """Learn from user corrections to improve future suggestions."""
        correction = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'corrected': corrected,
            'feedback': feedback
        }
        
        self.correction_history.append(correction)
        
        # Extract patterns
        pattern = self._extract_pattern(original, corrected)
        if pattern:
            self.patterns[pattern['type']].append(pattern)
        
        # Update preferences
        self._update_preferences(corrected)
        
        # Save learning data
        self.save_learning_data()
    
    def _extract_pattern(self, original: Dict, corrected: Dict) -> Optional[Dict]:
        """Extract learning pattern from correction."""
        pattern = {'type': 'general'}
        
        # Check what was changed
        if original.get('trigger') != corrected.get('trigger'):
            pattern['type'] = 'trigger_correction'
            pattern['change'] = 'trigger'
        elif original.get('action') != corrected.get('action'):
            pattern['type'] = 'action_correction'
            pattern['change'] = 'action'
        
        return pattern
    
    def _update_preferences(self, automation: Dict):
        """Update user preferences based on automation."""
        # Track preferred trigger times
        for trigger in automation.get('trigger', []):
            if trigger.get('platform') == 'time':
                time = trigger.get('at')
                self.user_preferences.setdefault('preferred_times', []).append(time)
        
        # Track preferred devices
        for action in automation.get('action', []):
            if 'entity_id' in action:
                self.user_preferences.setdefault('preferred_devices', []).append(action['entity_id'])
    
    def predict_improvement(self, automation: Dict) -> Dict[str, Any]:
        """Predict improvements based on learned patterns."""
        suggestions = {
            'confidence': 0.0,
            'improvements': []
        }
        
        # Check against learned patterns
        for pattern_type, patterns in self.patterns.items():
            if len(patterns) > 3:  # Need enough data
                # Apply pattern matching
                improvement = self._apply_pattern(automation, patterns)
                if improvement:
                    suggestions['improvements'].append(improvement)
                    suggestions['confidence'] += 0.2
        
        # Apply user preferences
        pref_improvements = self._apply_preferences(automation)
        suggestions['improvements'].extend(pref_improvements)
        
        suggestions['confidence'] = min(suggestions['confidence'], 1.0)
        
        return suggestions
    
    def _apply_pattern(self, automation: Dict, patterns: List) -> Optional[Dict]:
        """Apply learned pattern to suggest improvement."""
        # This is simplified - real implementation would use ML
        return {
            'type': 'learned_pattern',
            'suggestion': 'Based on your previous corrections, consider adjusting the trigger time'
        }
    
    def _apply_preferences(self, automation: Dict) -> List[Dict]:
        """Apply user preferences to suggest improvements."""
        improvements = []
        
        # Suggest preferred times
        if 'preferred_times' in self.user_preferences:
            times = Counter(self.user_preferences['preferred_times'])
            most_common = times.most_common(1)[0][0] if times else None
            if most_common:
                improvements.append({
                    'type': 'preferred_time',
                    'suggestion': f"You often use {most_common} as trigger time"
                })
        
        return improvements
    
    def save_learning_data(self):
        """Save learning data to disk."""
        try:
            data = {
                'patterns': dict(self.patterns),
                'preferences': self.user_preferences,
                'corrections': self.correction_history[-100:]  # Keep last 100
            }
            with open(self.learning_data_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            _LOGGER.error(f"Failed to save learning data: {e}")
    
    def load_learning_data(self):
        """Load learning data from disk."""
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.patterns = defaultdict(list, data.get('patterns', {}))
                    self.user_preferences = data.get('preferences', {})
                    self.correction_history = data.get('corrections', [])
        except Exception as e:
            _LOGGER.error(f"Failed to load learning data: {e}")


class AutomationSuggester:
    """Intelligently suggest automations based on usage patterns."""
    
    def __init__(self, hass):
        """Initialize the suggester."""
        self.hass = hass
        self.usage_patterns = {}
        self.device_interactions = defaultdict(list)
        
    async def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze Home Assistant usage patterns."""
        patterns = {
            'daily_routines': [],
            'device_correlations': [],
            'unused_devices': [],
            'optimization_opportunities': []
        }
        
        # Analyze state history
        history = await self._get_state_history()
        
        # Find daily routines
        patterns['daily_routines'] = self._find_daily_routines(history)
        
        # Find device correlations
        patterns['device_correlations'] = self._find_correlations(history)
        
        # Find unused devices
        patterns['unused_devices'] = self._find_unused_devices(history)
        
        # Find optimization opportunities
        patterns['optimization_opportunities'] = self._find_optimizations(patterns)
        
        return patterns
    
    async def suggest_automations(self) -> List[Dict[str, Any]]:
        """Suggest automations based on patterns."""
        suggestions = []
        patterns = await self.analyze_usage_patterns()
        
        # Suggest routine automations
        for routine in patterns['daily_routines']:
            suggestions.append({
                'type': 'daily_routine',
                'confidence': routine['confidence'],
                'title': f"Automate {routine['action']} at {routine['time']}",
                'description': f"You regularly {routine['action']} around {routine['time']}",
                'automation': self._build_routine_automation(routine)
            })
        
        # Suggest correlation automations
        for correlation in patterns['device_correlations']:
            suggestions.append({
                'type': 'device_correlation',
                'confidence': correlation['confidence'],
                'title': f"Link {correlation['device1']} with {correlation['device2']}",
                'description': f"These devices are often used together",
                'automation': self._build_correlation_automation(correlation)
            })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:10]  # Return top 10 suggestions
    
    def _find_daily_routines(self, history: Dict) -> List[Dict]:
        """Find daily routines in usage history."""
        routines = []
        
        # Group events by time of day
        time_events = defaultdict(list)
        
        # This is simplified - real implementation would analyze actual history
        # Example routine
        routines.append({
            'time': '07:00',
            'action': 'turn on kitchen lights',
            'confidence': 0.85,
            'frequency': 'daily'
        })
        
        return routines
    
    def _find_correlations(self, history: Dict) -> List[Dict]:
        """Find device correlations."""
        correlations = []
        
        # This would analyze which devices are used together
        # Example correlation
        correlations.append({
            'device1': 'light.living_room',
            'device2': 'switch.tv',
            'confidence': 0.75,
            'delay': 30  # seconds
        })
        
        return correlations
    
    def _find_unused_devices(self, history: Dict) -> List[str]:
        """Find devices that haven't been used recently."""
        unused = []
        
        # Check all entities
        for state in self.hass.states.async_all():
            # This is simplified - would check actual usage
            pass
        
        return unused
    
    def _find_optimizations(self, patterns: Dict) -> List[Dict]:
        """Find optimization opportunities."""
        optimizations = []
        
        if patterns['unused_devices']:
            optimizations.append({
                'type': 'unused_devices',
                'description': f"Found {len(patterns['unused_devices'])} unused devices",
                'action': 'Consider removing or automating these devices'
            })
        
        return optimizations
    
    def _build_routine_automation(self, routine: Dict) -> Dict:
        """Build automation for routine."""
        return {
            'alias': f"Daily: {routine['action']}",
            'trigger': [
                {
                    'platform': 'time',
                    'at': f"{routine['time']}:00"
                }
            ],
            'action': [
                {
                    'service': 'light.turn_on',
                    'entity_id': 'light.kitchen'
                }
            ]
        }
    
    def _build_correlation_automation(self, correlation: Dict) -> Dict:
        """Build automation for device correlation."""
        return {
            'alias': f"Link {correlation['device1']} and {correlation['device2']}",
            'trigger': [
                {
                    'platform': 'state',
                    'entity_id': correlation['device1'],
                    'to': 'on'
                }
            ],
            'action': [
                {
                    'delay': {
                        'seconds': correlation['delay']
                    }
                },
                {
                    'service': 'homeassistant.turn_on',
                    'entity_id': correlation['device2']
                }
            ]
        }
    
    async def _get_state_history(self) -> Dict:
        """Get state history from Home Assistant."""
        # This would fetch actual history
        return {}


class PerformanceOptimizer:
    """Optimize automation performance."""
    
    def __init__(self, hass):
        """Initialize optimizer."""
        self.hass = hass
    
    async def analyze_automation_performance(self, automation_id: str) -> Dict[str, Any]:
        """Analyze performance of an automation."""
        metrics = {
            'automation_id': automation_id,
            'execution_time': [],
            'trigger_frequency': 0,
            'resource_usage': 'low',
            'optimization_suggestions': []
        }
        
        # Analyze trigger frequency
        metrics['trigger_frequency'] = await self._get_trigger_frequency(automation_id)
        
        if metrics['trigger_frequency'] > 100:  # per day
            metrics['optimization_suggestions'].append({
                'issue': 'High trigger frequency',
                'suggestion': 'Consider adding conditions to reduce unnecessary executions'
            })
        
        return metrics
    
    async def optimize_all_automations(self) -> Dict[str, Any]:
        """Optimize all automations."""
        report = {
            'total_automations': 0,
            'optimized': 0,
            'issues_found': [],
            'improvements': []
        }
        
        # Get all automations
        automations = []  # Would fetch actual automations
        
        report['total_automations'] = len(automations)
        
        for automation in automations:
            optimization = await self.analyze_automation_performance(automation['id'])
            if optimization['optimization_suggestions']:
                report['issues_found'].append(optimization)
        
        return report
    
    async def _get_trigger_frequency(self, automation_id: str) -> int:
        """Get trigger frequency for automation."""
        # This would check actual logs
        return 10  # Example value