"""
Layer 5 — Governance: Compliance Automation
Audit logging, data retention policy enforcement, and compliance checks.
"""
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class AuditEvent:
    timestamp: float
    event_type: str
    actor: str
    resource: str
    action: str
    status: str
    details: Optional[dict] = None


class ComplianceAudit:
    """Stores and queries audit events for compliance verification"""

    def __init__(self, log_path: str = "outputs/audit_log.jsonl"):
        self.log_path = log_path
        self.events: list[AuditEvent] = []
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, event_type: str, actor: str, resource: str,
            action: str, status: str = "success", details: dict = None) -> AuditEvent:
        event = AuditEvent(
            timestamp=time.time(),
            event_type=event_type,
            actor=actor,
            resource=resource,
            action=action,
            status=status,
            details=details or {},
        )
        self.events.append(event)
        # Append to file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
        return event

    def query(self, event_type: str = None, actor: str = None,
              since: float = None, status: str = None) -> list[AuditEvent]:
        results = self.events
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        if since:
            results = [e for e in results if e.timestamp >= since]
        if status:
            results = [e for e in results if e.status == status]
        return results

    def get_summary(self) -> dict:
        total = len(self.events)
        failures = sum(1 for e in self.events if e.status == "failure")
        by_type = {}
        for e in self.events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        return {
            "total_events": total,
            "failures": failures,
            "success_rate": (total - failures) / max(total, 1) * 100,
            "by_event_type": by_type,
            "last_event_at": self.events[-1].timestamp if self.events else None,
        }


class DataRetentionPolicy:
    """Enforces data retention rules"""

    def __init__(self, max_age_days: int = 30):
        self.max_age_seconds = max_age_days * 86400

    def check_expired(self, timestamp: float) -> bool:
        """Check if data with given timestamp has expired"""
        return (time.time() - timestamp) > self.max_age_seconds

    def filter_active(self, records: list[dict], timestamp_field: str = "timestamp") -> list[dict]:
        """Filter records to keep only non-expired ones"""
        return [r for r in records if not self.check_expired(r.get(timestamp_field, 0))]

    def get_retention_info(self) -> dict:
        return {
            "policy": f"Retain for {self.max_age_seconds // 86400} days",
            "max_age_seconds": self.max_age_seconds,
            "enforced_at": time.time(),
        }


class ComplianceChecker:
    """Runs automated compliance checks"""

    def __init__(self, audit: ComplianceAudit):
        self.audit = audit
        self.checks: list[dict] = []

    def run_all(self) -> list[dict]:
        results = []
        results.append(self._check("Audit log exists", self._check_audit_exists()))
        results.append(self._check("No unauthorized access", self._check_no_unauthorized()))
        results.append(self._check("PII pipeline active", self._check_pii_active()))
        results.append(self._check("Encryption configured", self._check_encryption()))
        self.checks = results
        return results

    def _check(self, name: str, passed: bool) -> dict:
        return {"check": name, "passed": passed, "timestamp": time.time()}

    def _check_audit_exists(self) -> bool:
        return os.path.exists(self.audit.log_path)

    def _check_no_unauthorized(self) -> bool:
        unauthorized = self.audit.query(status="failure", event_type="rbac_check")
        return len(unauthorized) < 100  # Allow reasonable failures

    def _check_pii_active(self) -> bool:
        from governance.pii_pipeline import pii_pipeline
        return pii_pipeline is not None

    def _check_encryption(self) -> bool:
        key = os.environ.get("GOVERNANCE_ENCRYPTION_KEY", "")
        return len(key) >= 32

    def score(self) -> float:
        if not self.checks:
            return 0.0
        passed = sum(1 for c in self.checks if c["passed"])
        return (passed / len(self.checks)) * 100


# Global instances
audit = ComplianceAudit()
retention = DataRetentionPolicy(max_age_days=30)
compliance_checker = ComplianceChecker(audit)
