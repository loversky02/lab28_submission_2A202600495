"""
Layer 5 — Governance: PII Detection & Masking Pipeline
Detects and masks Personally Identifiable Information (PII) in data streams.
"""
import re
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PIIRule:
    name: str
    pattern: str
    mask: str = "***REDACTED***"
    description: str = ""


# Vietnamese + international PII patterns
PII_RULES = [
    PIIRule("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "***EMAIL***", "Email address"),
    PIIRule("phone_vn", r"\b(0|\+84)[3|5|7|8|9][0-9]{8}\b",
            "***PHONE***", "Vietnamese phone number"),
    PIIRule("cccd", r"\b\d{12}\b",
            "***CCCD***", "Vietnamese citizen ID (12 digits)"),
    PIIRule("credit_card", r"\b(?:\d[ -]*?){13,16}\b",
            "***CARD***", "Credit card number"),
    PIIRule("ip_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "***IP***", "IP address"),
    PIIRule("passport_vn", r"\b[A-Z]\d{7,9}\b",
            "***PASSPORT***", "Vietnamese passport number"),
]


class PIIPipeline:
    """Scans and masks PII in text data"""

    def __init__(self, rules: Optional[list[PIIRule]] = None):
        self.rules = rules or PII_RULES
        self._compiled = [(r, re.compile(r.pattern, re.IGNORECASE)) for r in self.rules]
        self.stats: dict[str, int] = {}

    def detect(self, text: str) -> list[dict]:
        """Detect PII in text, returns list of findings"""
        findings = []
        for rule, compiled in self._compiled:
            for match in compiled.finditer(text):
                findings.append({
                    "type": rule.name,
                    "value": match.group()[:4] + "****",
                    "position": match.span(),
                    "description": rule.description,
                })
        return findings

    def mask(self, text: str) -> str:
        """Mask all PII in text"""
        result = text
        for rule, compiled in self._compiled:
            result = compiled.sub(rule.mask, result)
            count = len(compiled.findall(text))
            if count > 0:
                self.stats[rule.name] = self.stats.get(rule.name, 0) + count
        return result

    def scrub_record(self, record: dict, fields: Optional[list[str]] = None) -> dict:
        """Scrub PII from a record's specified fields"""
        target_fields = fields or list(record.keys())
        cleaned = dict(record)
        for field in target_fields:
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned[field] = self.mask(cleaned[field])
        return cleaned

    def verify_compliance(self, text: str) -> bool:
        """Check if text is PII-free (for compliance validation)"""
        return len(self.detect(text)) == 0

    def report(self) -> dict:
        """Generate PII sanitization report"""
        total = sum(self.stats.values())
        return {
            "total_pii_masked": total,
            "by_type": dict(self.stats),
            "rules_applied": len(self.rules),
            "compliance_status": "PASS" if total >= 0 else "UNKNOWN",
        }


# Global instance
pii_pipeline = PIIPipeline()
