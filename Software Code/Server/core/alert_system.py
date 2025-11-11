"""
Alert System - Real-time notifications and warnings
Monitors for crowd detection, security threats, and unusual behavior
Location: Software Code/Server/core/alert_system.py
"""

import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import json

from core.config import CROWD_THRESHOLD, ALERT_TYPES
from core.tracker import Track


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    CROWD_DETECTED = "crowd_detected"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    LOITERING = "loitering"
    SECURITY_OBJECT = "security_object"
    ZONE_VIOLATION = "zone_violation"
    HIGH_ACTIVITY = "high_activity"
    NO_ACTIVITY = "no_activity"


@dataclass
class Alert:
    """Alert object with all relevant information"""
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    timestamp: float
    message: str
    details: Dict = field(default_factory=dict)
    location: Optional[Dict] = None
    resolved: bool = False
    resolved_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "type": self.alert_type.value,
            "level": self.level.value,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "message": self.message,
            "details": self.details,
            "location": self.location,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at
        }
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = time.time()


class AlertSystem:
    """
    Real-time alert monitoring system
    Detects unusual patterns and generates alerts
    """
    
    def __init__(
        self,
        crowd_threshold: int = None,
        loitering_time: float = 300.0,  # 5 minutes
        enable_logging: bool = True
    ):
        """
        Initialize alert system
        
        Args:
            crowd_threshold: Number of people for crowd alert
            loitering_time: Time in seconds to trigger loitering alert
            enable_logging: Whether to log alerts to file
        """
        self.crowd_threshold = crowd_threshold or CROWD_THRESHOLD
        self.loitering_time = loitering_time
        self.enable_logging = enable_logging
        
        # Alert storage
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Alert callbacks (for real-time notifications)
        self.callbacks: List[Callable] = []
        
        # Statistics
        self.total_alerts = 0
        self.alerts_by_type = {alert_type: 0 for alert_type in AlertType}
        
        print("🚨 Alert System Initialized")
        print(f"👥 Crowd threshold: {self.crowd_threshold} people")
        print(f"⏱️  Loitering threshold: {loitering_time}s")
    
    def check_alerts(
        self,
        active_tracks: List[Track],
        timestamp: float,
        frame_number: int
    ) -> List[Alert]:
        """
        Check current state and generate alerts
        
        Args:
            active_tracks: Currently active tracks
            timestamp: Current timestamp
            frame_number: Current frame number
            
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        # Check crowd detection
        crowd_alert = self._check_crowd(active_tracks, timestamp)
        if crowd_alert:
            new_alerts.append(crowd_alert)
        
        # Check for loitering
        loitering_alerts = self._check_loitering(active_tracks, timestamp)
        new_alerts.extend(loitering_alerts)
        
        # Check for idle behavior
        idle_alerts = self._check_idle_behavior(active_tracks, timestamp)
        new_alerts.extend(idle_alerts)
        
        # Process new alerts
        for alert in new_alerts:
            self._process_alert(alert)
        
        return new_alerts
    
    def _check_crowd(self, tracks: List[Track], timestamp: float) -> Optional[Alert]:
        """Check if crowd threshold is exceeded"""
        people_count = len(tracks)
        
        if people_count >= self.crowd_threshold:
            # Check if we already have an active crowd alert
            for alert in self.active_alerts:
                if alert.alert_type == AlertType.CROWD_DETECTED and not alert.resolved:
                    # Update existing alert
                    alert.details['current_count'] = people_count
                    return None
            
            # Create new crowd alert
            alert = Alert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.CROWD_DETECTED,
                level=AlertLevel.WARNING,
                timestamp=timestamp,
                message=f"Crowd detected: {people_count} people",
                details={
                    'people_count': people_count,
                    'threshold': self.crowd_threshold
                }
            )
            return alert
        else:
            # Resolve any active crowd alerts
            self._resolve_alerts_by_type(AlertType.CROWD_DETECTED)
        
        return None
    
    def _check_loitering(
        self,
        tracks: List[Track],
        timestamp: float
    ) -> List[Alert]:
        """Check for people loitering (staying too long)"""
        alerts = []
        
        for track in tracks:
            if track.duration > self.loitering_time:
                # Check if we already alerted for this track
                alert_exists = any(
                    a.details.get('track_id') == track.track_id 
                    and a.alert_type == AlertType.LOITERING 
                    and not a.resolved
                    for a in self.active_alerts
                )
                
                if not alert_exists:
                    alert = Alert(
                        alert_id=self._generate_alert_id(),
                        alert_type=AlertType.LOITERING,
                        level=AlertLevel.INFO,
                        timestamp=timestamp,
                        message=f"Person loitering: ID {track.track_id}",
                        details={
                            'track_id': track.track_id,
                            'duration': track.duration,
                            'threshold': self.loitering_time
                        },
                        location={'position': track.last_position}
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _check_idle_behavior(
        self,
        tracks: List[Track],
        timestamp: float
    ) -> List[Alert]:
        """Check for people standing idle for extended periods"""
        alerts = []
        
        for track in tracks:
            if track.is_stationary and track.idle_duration > 60.0:  # 1 minute
                # Check if already alerted
                alert_exists = any(
                    a.details.get('track_id') == track.track_id 
                    and a.alert_type == AlertType.SUSPICIOUS_BEHAVIOR 
                    and not a.resolved
                    for a in self.active_alerts
                )
                
                if not alert_exists:
                    alert = Alert(
                        alert_id=self._generate_alert_id(),
                        alert_type=AlertType.SUSPICIOUS_BEHAVIOR,
                        level=AlertLevel.INFO,
                        timestamp=timestamp,
                        message=f"Idle behavior detected: ID {track.track_id}",
                        details={
                            'track_id': track.track_id,
                            'idle_duration': track.idle_duration,
                            'position': track.last_position
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def create_custom_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        details: Dict = None,
        location: Dict = None
    ) -> Alert:
        """
        Create a custom alert
        
        Args:
            alert_type: Type of alert
            level: Alert severity
            message: Alert message
            details: Additional details
            location: Location information
            
        Returns:
            Created alert
        """
        alert = Alert(
            alert_id=self._generate_alert_id(),
            alert_type=alert_type,
            level=level,
            timestamp=time.time(),
            message=message,
            details=details or {},
            location=location
        )
        
        self._process_alert(alert)
        return alert
    
    def _process_alert(self, alert: Alert):
        """Process and store alert"""
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        self.total_alerts += 1
        self.alerts_by_type[alert.alert_type] += 1
        
        # Log alert
        if self.enable_logging:
            self._log_alert(alert)
        
        # Trigger callbacks
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️  Alert callback error: {e}")
        
        # Print to console
        self._print_alert(alert)
    
    def _resolve_alerts_by_type(self, alert_type: AlertType):
        """Resolve all active alerts of a specific type"""
        for alert in self.active_alerts:
            if alert.alert_type == alert_type and not alert.resolved:
                alert.resolve()
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"ALERT_{int(time.time() * 1000)}_{self.total_alerts}"
    
    def _log_alert(self, alert: Alert):
        """Log alert to file"""
        from core.config import REPORTS_DIR
        
        log_file = REPORTS_DIR / "alerts.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            log_entry = {
                "timestamp": datetime.fromtimestamp(alert.timestamp).isoformat(),
                "alert": alert.to_dict()
            }
            f.write(json.dumps(log_entry) + "\n")
    
    def _print_alert(self, alert: Alert):
        """Print alert to console"""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emoji.get(alert.level, "🔔")
        print(f"\n{emoji} [{alert.level.value.upper()}] {alert.message}")
        print(f"   Type: {alert.alert_type.value}")
        print(f"   Time: {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}")
        if alert.details:
            print(f"   Details: {alert.details}")
    
    def register_callback(self, callback: Callable):
        """
        Register a callback function to be called when alerts are generated
        
        Args:
            callback: Function that takes an Alert object as parameter
        """
        self.callbacks.append(callback)
        print(f"✅ Alert callback registered: {callback.__name__}")
    
    def get_active_alerts(self, alert_type: AlertType = None) -> List[Alert]:
        """
        Get active (unresolved) alerts
        
        Args:
            alert_type: Filter by alert type (optional)
            
        Returns:
            List of active alerts
        """
        alerts = [a for a in self.active_alerts if not a.resolved]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return alerts
    
    def get_alert_history(
        self,
        limit: int = 100,
        alert_type: AlertType = None
    ) -> List[Alert]:
        """
        Get alert history
        
        Args:
            limit: Maximum number of alerts to return
            alert_type: Filter by type
            
        Returns:
            List of historical alerts
        """
        alerts = self.alert_history
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return alerts[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        active_count = len([a for a in self.active_alerts if not a.resolved])
        
        return {
            "total_alerts": self.total_alerts,
            "active_alerts": active_count,
            "resolved_alerts": self.total_alerts - active_count,
            "alerts_by_type": {
                k.value: v for k, v in self.alerts_by_type.items()
            },
            "alert_history_size": len(self.alert_history)
        }
    
    def clear_resolved_alerts(self):
        """Remove resolved alerts from active list"""
        before_count = len(self.active_alerts)
        self.active_alerts = [a for a in self.active_alerts if not a.resolved]
        removed = before_count - len(self.active_alerts)
        
        if removed > 0:
            print(f"🧹 Cleared {removed} resolved alerts")
    
    def reset(self):
        """Reset alert system"""
        self.active_alerts.clear()
        self.alert_history.clear()
        self.total_alerts = 0
        self.alerts_by_type = {alert_type: 0 for alert_type in AlertType}
        print("🔄 Alert system reset")


class AlertNotifier:
    """
    Sends alert notifications via different channels
    Can be extended to support email, SMS, webhooks, etc.
    """
    
    def __init__(self):
        self.notification_channels = []
    
    def send_notification(self, alert: Alert):
        """Send notification for an alert"""
        # This is a placeholder for future notification implementations
        # Can be extended to send:
        # - Email notifications
        # - SMS alerts
        # - Webhook posts
        # - Push notifications
        pass
    
    def add_channel(self, channel: str, config: Dict):
        """Add a notification channel"""
        self.notification_channels.append({
            "channel": channel,
            "config": config
        })


if __name__ == "__main__":
    print("✅ Alert System Module Ready")
    print("🚨 Alert Types:")
    for alert_type in AlertType:
        print(f"   - {alert_type.value}")
    print("\n💡 Usage:")
    print("  system = AlertSystem()")
    print("  alerts = system.check_alerts(tracks, timestamp, frame_num)")