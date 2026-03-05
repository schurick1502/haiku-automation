"""Analytics and Monitoring Module for HAIKU Automation Builder."""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

_LOGGER = logging.getLogger(__name__)

class AutomationAnalytics:
    """Analytics system for monitoring automation performance."""
    
    def __init__(self, hass):
        """Initialize analytics."""
        self.hass = hass
        self.metrics = defaultdict(lambda: {
            'triggers': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_execution_time': 0,
            'last_triggered': None,
            'created_by': 'unknown',
            'energy_saved': 0,
            'user_interactions': 0
        })
        self.global_stats = {
            'total_automations': 0,
            'active_automations': 0,
            'total_triggers_today': 0,
            'energy_saved_today': 0,
            'most_used_devices': Counter(),
            'peak_hours': Counter(),
            'error_rate': 0.0
        }
        
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics for all automations."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'automations': {},
            'global': self.global_stats,
            'insights': []
        }
        
        # Collect per-automation metrics
        automations = await self._get_all_automations()
        for automation in automations:
            auto_id = automation.get('id')
            metrics['automations'][auto_id] = await self._analyze_automation(automation)
        
        # Update global statistics
        metrics['global'] = await self._calculate_global_stats(metrics['automations'])
        
        # Generate insights
        metrics['insights'] = self._generate_insights(metrics)
        
        return metrics
    
    async def _analyze_automation(self, automation: Dict) -> Dict[str, Any]:
        """Analyze a single automation."""
        auto_id = automation.get('id')
        analysis = self.metrics[auto_id].copy()
        
        # Add automation metadata
        analysis['name'] = automation.get('alias', auto_id)
        analysis['enabled'] = automation.get('enabled', True)
        analysis['complexity'] = self._calculate_complexity(automation)
        
        # Analyze triggers
        analysis['trigger_types'] = self._analyze_trigger_types(automation.get('trigger', []))
        
        # Analyze actions
        analysis['action_types'] = self._analyze_action_types(automation.get('action', []))
        
        # Calculate efficiency score
        analysis['efficiency_score'] = self._calculate_efficiency(analysis)
        
        # Estimate energy impact
        analysis['energy_impact'] = await self._estimate_energy_impact(automation)
        
        return analysis
    
    def _calculate_complexity(self, automation: Dict) -> str:
        """Calculate automation complexity."""
        score = 0
        
        # Count triggers
        triggers = len(automation.get('trigger', []))
        score += triggers * 1
        
        # Count conditions
        conditions = len(automation.get('condition', []))
        score += conditions * 2
        
        # Count actions
        actions = len(automation.get('action', []))
        score += actions * 1
        
        # Check for complex actions
        for action in automation.get('action', []):
            if 'choose' in action or 'repeat' in action or 'wait_template' in action:
                score += 3
        
        if score <= 3:
            return 'simple'
        elif score <= 8:
            return 'moderate'
        else:
            return 'complex'
    
    def _analyze_trigger_types(self, triggers: List[Dict]) -> Dict[str, int]:
        """Analyze trigger types used."""
        types = Counter()
        for trigger in triggers:
            platform = trigger.get('platform', 'unknown')
            types[platform] += 1
        return dict(types)
    
    def _analyze_action_types(self, actions: List[Dict]) -> Dict[str, int]:
        """Analyze action types used."""
        types = Counter()
        for action in actions:
            if 'service' in action:
                service = action['service'].split('.')[0]
                types[service] += 1
            elif 'delay' in action:
                types['delay'] += 1
            elif 'wait_template' in action:
                types['wait'] += 1
        return dict(types)
    
    def _calculate_efficiency(self, analysis: Dict) -> float:
        """Calculate efficiency score (0-100)."""
        score = 100.0
        
        # Penalize for failures
        total_runs = analysis['successful_runs'] + analysis['failed_runs']
        if total_runs > 0:
            success_rate = analysis['successful_runs'] / total_runs
            score *= success_rate
        
        # Penalize for complexity without usage
        if analysis['complexity'] == 'complex' and analysis['triggers'] < 10:
            score *= 0.8
        
        # Bonus for energy saving
        if analysis.get('energy_saved', 0) > 0:
            score = min(100, score * 1.1)
        
        return round(score, 1)
    
    async def _estimate_energy_impact(self, automation: Dict) -> Dict[str, Any]:
        """Estimate energy impact of automation."""
        impact = {
            'rating': 'neutral',
            'estimated_savings_kwh': 0,
            'devices_controlled': []
        }
        
        # Check actions for energy-related devices
        for action in automation.get('action', []):
            if 'entity_id' in action:
                entity = action['entity_id']
                domain = entity.split('.')[0]
                
                # Energy-saving actions
                if action.get('service', '').endswith('turn_off'):
                    if domain in ['light', 'switch', 'climate']:
                        impact['estimated_savings_kwh'] += 0.1
                        impact['devices_controlled'].append(entity)
                
                # Climate optimizations
                if domain == 'climate' and 'temperature' in action.get('data', {}):
                    impact['estimated_savings_kwh'] += 0.5
        
        # Determine rating
        if impact['estimated_savings_kwh'] > 1:
            impact['rating'] = 'high_saver'
        elif impact['estimated_savings_kwh'] > 0:
            impact['rating'] = 'saver'
        elif impact['estimated_savings_kwh'] < -0.5:
            impact['rating'] = 'consumer'
        
        return impact
    
    async def _calculate_global_stats(self, automations: Dict) -> Dict[str, Any]:
        """Calculate global statistics."""
        stats = {
            'total_automations': len(automations),
            'active_automations': sum(1 for a in automations.values() if a.get('enabled', True)),
            'total_triggers_today': sum(a.get('triggers', 0) for a in automations.values()),
            'average_complexity': Counter(a['complexity'] for a in automations.values()),
            'total_energy_saved': sum(a.get('energy_impact', {}).get('estimated_savings_kwh', 0) 
                                     for a in automations.values()),
            'top_triggered': self._get_top_triggered(automations),
            'unused_automations': [name for name, a in automations.items() 
                                  if a.get('triggers', 0) == 0],
            'error_prone': [name for name, a in automations.items() 
                           if a.get('failed_runs', 0) > a.get('successful_runs', 0)]
        }
        
        return stats
    
    def _get_top_triggered(self, automations: Dict, limit: int = 5) -> List[Dict]:
        """Get top triggered automations."""
        sorted_autos = sorted(
            automations.items(),
            key=lambda x: x[1].get('triggers', 0),
            reverse=True
        )
        
        return [
            {
                'id': auto_id,
                'name': data.get('name', auto_id),
                'triggers': data.get('triggers', 0)
            }
            for auto_id, data in sorted_autos[:limit]
        ]
    
    def _generate_insights(self, metrics: Dict) -> List[Dict]:
        """Generate actionable insights from metrics."""
        insights = []
        
        # Check for unused automations
        unused = metrics['global'].get('unused_automations', [])
        if unused:
            insights.append({
                'type': 'unused',
                'severity': 'info',
                'title': 'Unused Automations Detected',
                'description': f"Found {len(unused)} automations that haven't triggered",
                'action': 'Review and remove or fix unused automations',
                'affected': unused[:5]  # Show first 5
            })
        
        # Check for error-prone automations
        error_prone = metrics['global'].get('error_prone', [])
        if error_prone:
            insights.append({
                'type': 'errors',
                'severity': 'warning',
                'title': 'Automations with High Error Rate',
                'description': f"{len(error_prone)} automations fail more than succeed",
                'action': 'Debug and fix these automations',
                'affected': error_prone[:5]
            })
        
        # Energy saving opportunities
        energy_saved = metrics['global'].get('total_energy_saved', 0)
        if energy_saved < 1:
            insights.append({
                'type': 'energy',
                'severity': 'suggestion',
                'title': 'Energy Saving Opportunity',
                'description': 'Your automations could save more energy',
                'action': 'Add schedules for lights and climate control',
                'potential_savings': '10-30 kWh/month'
            })
        
        # Complexity analysis
        complexity_dist = metrics['global'].get('average_complexity', {})
        if complexity_dist.get('complex', 0) > complexity_dist.get('simple', 0):
            insights.append({
                'type': 'complexity',
                'severity': 'info',
                'title': 'High Automation Complexity',
                'description': 'Most automations are complex',
                'action': 'Consider breaking complex automations into simpler ones',
                'benefit': 'Easier debugging and maintenance'
            })
        
        # Peak usage patterns
        if metrics['global'].get('total_triggers_today', 0) > 1000:
            insights.append({
                'type': 'performance',
                'severity': 'warning',
                'title': 'High Automation Activity',
                'description': 'Automations triggered over 1000 times today',
                'action': 'Review trigger frequencies to avoid system overload',
                'optimization': 'Add conditions to reduce unnecessary triggers'
            })
        
        return insights
    
    async def generate_report(self, period: str = 'week') -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        metrics = await self.collect_metrics()
        
        report = {
            'period': period,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_automations': metrics['global']['total_automations'],
                'active_automations': metrics['global']['active_automations'],
                'total_triggers': metrics['global']['total_triggers_today'],
                'energy_saved': f"{metrics['global']['total_energy_saved']:.1f} kWh",
                'health_score': self._calculate_health_score(metrics)
            },
            'top_performers': metrics['global'].get('top_triggered', []),
            'issues': {
                'unused': len(metrics['global'].get('unused_automations', [])),
                'errors': len(metrics['global'].get('error_prone', [])),
                'complex': sum(1 for a in metrics['automations'].values() 
                             if a.get('complexity') == 'complex')
            },
            'insights': metrics['insights'],
            'recommendations': self._generate_recommendations(metrics)
        }
        
        return report
    
    def _calculate_health_score(self, metrics: Dict) -> int:
        """Calculate overall system health score (0-100)."""
        score = 100
        
        # Penalize for unused automations
        unused_ratio = len(metrics['global'].get('unused_automations', [])) / max(1, metrics['global']['total_automations'])
        score -= int(unused_ratio * 20)
        
        # Penalize for error-prone automations
        error_ratio = len(metrics['global'].get('error_prone', [])) / max(1, metrics['global']['total_automations'])
        score -= int(error_ratio * 30)
        
        # Bonus for energy saving
        if metrics['global'].get('total_energy_saved', 0) > 10:
            score = min(100, score + 10)
        
        return max(0, score)
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        # Based on insights
        for insight in metrics['insights']:
            if insight['type'] == 'unused':
                recommendations.append("Review and remove unused automations to keep system clean")
            elif insight['type'] == 'errors':
                recommendations.append("Fix failing automations to improve reliability")
            elif insight['type'] == 'energy':
                recommendations.append("Add time-based automations for lights and climate")
        
        # General recommendations
        if metrics['global']['total_automations'] < 5:
            recommendations.append("Explore more automation possibilities with HAIKU")
        
        if not recommendations:
            recommendations.append("Your automation system is running smoothly!")
        
        return recommendations
    
    async def _get_all_automations(self) -> List[Dict]:
        """Get all automations from Home Assistant."""
        # This would fetch actual automations
        return []
    
    async def track_execution(self, automation_id: str, success: bool, execution_time: float):
        """Track automation execution."""
        self.metrics[automation_id]['triggers'] += 1
        
        if success:
            self.metrics[automation_id]['successful_runs'] += 1
        else:
            self.metrics[automation_id]['failed_runs'] += 1
        
        self.metrics[automation_id]['total_execution_time'] += execution_time
        self.metrics[automation_id]['last_triggered'] = datetime.now().isoformat()
        
        # Update global stats
        self.global_stats['total_triggers_today'] += 1
        
        # Track hour for peak analysis
        hour = datetime.now().hour
        self.global_stats['peak_hours'][hour] += 1