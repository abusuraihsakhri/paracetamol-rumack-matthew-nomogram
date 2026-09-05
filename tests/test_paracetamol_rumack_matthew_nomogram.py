"""
Automated Pytest Test Suite for Paracetamol Rumack Matthew Nomogram.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_detects_ssn():
    """SSN pattern (XXX-XX-XXXX) must be detected."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient SSN 123-45-6789")


def test_phi_guard_detects_phone():
    """Phone numbers must be detected."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Call patient at 555-123-4567")


def test_phi_guard_detects_email():
    """Email addresses must be detected."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Email results to doctor@hospital.org")


def test_phi_guard_detects_patient_name():
    """Patient Name patterns must be detected."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient Name John Smith admitted")


def test_phi_guard_redact():
    """PHI redact replaces sensitive patterns."""
    redacted = PHIGuard.redact_phi("Patient MRN-12345678 has SSN 123-45-6789")
    assert "MRN" not in redacted or "REDACTED" in redacted
    assert "REDACTED_IDENTIFIER" in redacted


def test_phi_guard_none_and_empty():
    """None and empty strings should pass without error."""
    PHIGuard.assert_no_phi(None)
    PHIGuard.assert_no_phi("")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_integrity_tampering():
    """Audit trail must detect tampering."""
    trail = AuditTrail(secret_key="test-key-for-integrity")
    trail.log("test", "tier", "EVENT", {"data": "value1"})
    trail.log("test", "tier", "EVENT", {"data": "value2"})
    assert trail.verify_integrity() is True

    # Tamper with a log entry
    trail.logs[0]["payload_hash"] = "tampered_hash"
    assert trail.verify_integrity() is False


def test_audit_trail_rejects_phi_in_log():
    """Audit log must reject PHI-containing payloads."""
    trail = AuditTrail(secret_key="test-key-phi")
    with pytest.raises(SecurityException):
        trail.log("test", "tier", "EVENT", {"patient": "MRN-12345678"})


def test_audit_trail_random_key_generation():
    """When no key is provided, a random key should be generated."""
    trail = AuditTrail()
    assert len(trail.secret_key) > 0
    trail.log("test", "tier", "EVENT", {"data": "value"})
    assert trail.verify_integrity() is True


def test_supervisor_blocks_phi_in_task_id():
    """Supervisor must reject PHI in task_id."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="Patient MRN-994827",
        target_identifier="KEY-01",
        primary_metric=10.0,
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)
