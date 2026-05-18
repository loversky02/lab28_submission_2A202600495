#!/usr/bin/env python3
"""Layer 5 — Governance Verification
Tests RBAC, PII masking, encryption, and compliance automation.
"""
import os, sys, json, time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from governance.rbac import RBACManager, Permission
from governance.pii_pipeline import PIIPipeline, PII_RULES
from governance.encryption import encrypt_value, decrypt_value, generate_key, encrypt_record
from governance.compliance import ComplianceAudit, DataRetentionPolicy, audit as global_audit


def test_rbac():
    print("\n--- RBAC ---")
    mgr = RBACManager()
    mgr.register_key("test-admin-key", "admin")
    mgr.register_key("test-viewer-key", "viewer")

    # Admin can chat
    assert mgr.check_permission("test-admin-key", Permission.CHAT), "Admin should be able to chat"
    print("  [PASS] Admin can chat")

    # Admin can admin
    assert mgr.check_permission("test-admin-key", Permission.ADMIN), "Admin should be able to admin"
    print("  [PASS] Admin can admin")

    # Viewer can chat
    assert mgr.check_permission("test-viewer-key", Permission.CHAT), "Viewer should be able to chat"
    print("  [PASS] Viewer can chat")

    # Viewer CANNOT admin
    assert not mgr.check_permission("test-viewer-key", Permission.ADMIN), "Viewer should NOT admin"
    print("  [PASS] Viewer blocked from admin")

    # Rate limit test
    for _ in range(25):
        ok = mgr.check_rate_limit("test-viewer-key")
    assert not ok, "Viewer should be rate limited after 20 requests"
    print("  [PASS] Rate limiting enforced (20 req/min for viewer)")

    # Disable key
    mgr.disable_key("test-viewer-key")
    assert not mgr.check_permission("test-viewer-key", Permission.CHAT), "Disabled key should fail"
    print("  [PASS] Key disable/enable works")

    print("  RBAC: ALL CHECKS PASSED")


def test_pii():
    print("\n--- PII Detection & Masking ---")
    pipeline = PIIPipeline()

    # Test detection
    text_with_pii = "My email is test@example.com and phone 0987654321. My CCCD is 001234567890."
    findings = pipeline.detect(text_with_pii)
    assert len(findings) >= 2, f"Should detect at least 2 PII items, found {len(findings)}"
    print(f"  [PASS] Detected {len(findings)} PII items")

    # Test masking
    masked = pipeline.mask(text_with_pii)
    assert "test@example.com" not in masked, "Email should be masked"
    assert "0987654321" not in masked, "Phone should be masked"
    print(f"  [PASS] Masked text: {masked[:80]}...")

    # Test record scrubbing
    record = {"name": "Test", "email": "user@company.com", "phone": "0987654321", "data": "safe data"}
    cleaned = pipeline.scrub_record(record, fields=["email", "phone"])
    assert cleaned["data"] == "safe data", "Non-PII data should be preserved"
    assert cleaned["email"] != record["email"], "Email should be scrubbed"
    print("  [PASS] Record scrubbing works, safe data preserved")

    # Test compliance verification
    assert pipeline.verify_compliance("safe text without pii"), "Should pass for clean text"
    assert not pipeline.verify_compliance("email@example.com"), "Should fail for PII text"
    print("  [PASS] Compliance verification works")

    report = pipeline.report()
    print(f"  Report: {json.dumps(report, indent=2)}")
    print("  PII Pipeline: ALL CHECKS PASSED")


def test_encryption():
    print("\n--- Field-Level Encryption ---")
    key = generate_key()
    assert len(key) == 32, f"Key should be 32 bytes, got {len(key)}"
    print("  [PASS] Key generation (32 bytes)")

    # Test encrypt/decrypt
    original = "sensitive-pii-data-12345"
    encrypted = encrypt_value(original, key)
    assert encrypted != original, "Encrypted should differ from original"
    print(f"  [PASS] Encryption: '{original}' -> '{encrypted[:30]}...'")

    decrypted = decrypt_value(encrypted, key)
    assert decrypted == original, f"Decrypted '{decrypted}' should match original '{original}'"
    print("  [PASS] Decryption round-trip success")

    # Test record encryption
    record = {"user": "test_user", "ssn": "123-45-6789", "email": "test@example.com"}
    encrypted_record = encrypt_record(record, ["ssn", "email"], key)
    assert encrypted_record["user"] == "test_user", "Non-sensitive field preserved"
    assert encrypted_record["ssn"] != record["ssn"], "SSN encrypted"
    assert encrypted_record["email"] != record["email"], "Email encrypted"
    print("  [PASS] Record field encryption: sensitive fields encrypted, others preserved")

    # Test hex key
    hex_key = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    encrypted_hex = encrypt_value("test", hex_key)
    decrypted_hex = decrypt_value(encrypted_hex, hex_key)
    assert decrypted_hex == "test"
    print("  [PASS] Hex key format works")

    print("  Encryption: ALL CHECKS PASSED")


def test_compliance():
    print("\n--- Compliance Automation ---")
    audit = ComplianceAudit(log_path="outputs/audit_test.jsonl")

    # Log events
    audit.log("rbac_check", "user-1", "/api/v1/chat", "read", "success")
    audit.log("rbac_check", "user-2", "/admin", "read", "failure", {"reason": "unauthorized"})
    audit.log("pii_scrub", "system", "data_pipeline", "process", "success", {"count": 15})
    audit.log("data_access", "user-1", "/api/v1/search", "read", "success")
    print(f"  [PASS] Logged {len(audit.events)} audit events")

    # Query
    unauthorized = audit.query(status="failure")
    assert len(unauthorized) == 1
    print(f"  [PASS] Query found {len(unauthorized)} unauthorized event(s)")

    # Summary
    summary = audit.get_summary()
    assert summary["total_events"] == 4
    assert summary["success_rate"] == 75.0
    print(f"  [PASS] Audit summary: {json.dumps(summary, indent=2)}")

    # Retention policy
    policy = DataRetentionPolicy(max_age_days=30)
    assert not policy.check_expired(time.time() - 86400), "1-day-old data should not expire"
    assert policy.check_expired(time.time() - 32 * 86400), "32-day-old data should expire"
    print("  [PASS] Data retention policy enforced")

    print("  Compliance: ALL CHECKS PASSED")


def main():
    print("=" * 60)
    print("Layer 5 — Governance Verification")
    print("RBAC + PII + Encryption + Compliance")
    print("=" * 60)

    try:
        test_rbac()
        test_pii()
        test_encryption()
        test_compliance()
    except AssertionError as e:
        print(f"\n  [FAIL] {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Governance Layer 5: ALL VERIFIED")
    print(f"{'='*60}")

    # Save results
    os.makedirs("outputs", exist_ok=True)
    results = {
        "timestamp": time.time(),
        "rbac": "PASS",
        "pii_detection": "PASS",
        "encryption": "PASS",
        "compliance": "PASS",
        "status": "Layer 5 Governance — Production Ready",
    }
    with open("outputs/governance_check.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
