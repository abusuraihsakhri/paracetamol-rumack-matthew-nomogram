"""
Automated Pytest for paracetamol-rumack-matthew-nomogram Enrichment Modules.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    EnrichmentmdEngine,
    LongitudinalScoreTrackingEngine,
    EhrfhirIntegrationEngine,
    VisualDashboardEngine,
    AlertEscalationEngine,
    PatientStratificationEngine,
    CrossinstitutionalAnalyticsEngine,
    AutomatedReportingEngine,
    ParacetamolrumackmatthewnomogramEnrichmentSuite,
    enrichment_suite,
)

def test_enrichment_suite_execution():
    suite = ParacetamolrumackmatthewnomogramEnrichmentSuite()
    res = suite.execute_all(primary_val=0.5, secondary_val=0.2)
    assert len(res) >= 1
    for k, v in res.items():
        assert v.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
        assert isinstance(v.recommendations, list)

def test_enrichment_threshold_escalation():
    suite = ParacetamolrumackmatthewnomogramEnrichmentSuite()
    res = suite.execute_all(primary_val=10.0, secondary_val=5.0)
    for k, v in res.items():
        assert v.status in ["WARNING", "CRITICAL_ALERT"]
        assert len(v.alerts) > 0
