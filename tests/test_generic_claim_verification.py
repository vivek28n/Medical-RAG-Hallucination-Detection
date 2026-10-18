"""
Tests for Phase 1: Generic Claim Verification.

Validates that:
1. Hypothesis construction preserves actual claim semantics (negation, numbers, units, qualifiers).
2. Claims with "age" or "45" are NOT rewritten to hand-crafted diabetes templates.
3. Generic non-diabetes claims are NOT converted to diabetes risk factor sentences.
4. Empty or malformed claims return safe non-verified states.
5. Headings and preambles are extracted/filtered generically.
6. Incomplete fragments and dangling connectors are rejected.
7. Insufficient or irrelevant evidence does not result in SUPPORTED.
8. Legacy templates are guarded behind USE_LEGACY_CLAIM_TEMPLATES configuration flag.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Ensure backend root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.verification import VerificationService, verification_service
from app.config import settings


class TestGenericClaimVerification(unittest.TestCase):

    # ─── 1. Negation Preservation ─────────────────────────────────

    def test_hypothesis_negation_preservation(self):
        """Test that negation words (not, no, never, without) are strictly preserved."""
        claims = [
            "Patients with normal glucose tolerance do not require metformin.",
            "No increased cardiovascular risk was observed in the normotensive group.",
            "Testing is not recommended for asymptomatic individuals under 45 without risk factors.",
            "Lifestyle interventions should never be discontinued abruptly.",
        ]
        for claim in claims:
            hypo = VerificationService.claim_to_hypothesis(claim)
            self.assertIn(
                claim.rstrip("."),
                hypo.rstrip("."),
                f"Original claim with negation altered in hypothesis: {hypo}"
            )
            self.assertTrue(
                any(neg in hypo.lower().split() for neg in ["not", "no", "never", "without"]),
                f"Negation disappeared in hypothesis: {hypo}"
            )

    # ─── 2. Numbers and Units Preservation ────────────────────────

    def test_hypothesis_numbers_and_units_preservation(self):
        """Test that quantitative thresholds, numbers, and units are strictly preserved."""
        test_cases = [
            ("Blood pressure of 140/90 mmHg or higher indicates hypertension.", ["140/90", "mmhg"]),
            ("Fasting triglyceride levels should be below 150 mg/dL.", ["150", "mg/dl"]),
            ("BMI threshold for Asian Americans is 23 kg/m².", ["23", "kg/m²"]),
            ("Screening is recommended every 3 years for adults aged 45 and older.", ["3", "45"]),
            ("HbA1c level of 6.5% or higher confirms diabetes.", ["6.5%", "diabetes"]),
        ]
        for claim, expected_tokens in test_cases:
            hypo = VerificationService.claim_to_hypothesis(claim)
            hypo_lower = hypo.lower()
            for token in expected_tokens:
                self.assertIn(
                    token.lower(),
                    hypo_lower,
                    f"Expected token '{token}' missing from hypothesis: '{hypo}'"
                )

    # ─── 3. Age / 45 Claims Not Rewritten to Diabetes Template ───

    def test_hypothesis_age_45_not_rewritten_to_diabetes_template(self):
        """
        Critical check: Claims containing 'age' or '45' must NOT be rewritten
        into the hardcoded sentence 'Increasing age is a risk factor for type 2 diabetes.'
        """
        diabetes_template = "Increasing age is a risk factor for type 2 diabetes."

        claims = [
            "Patients under age 45 without symptoms should not undergo routine testing.",
            "Age 45 is the baseline threshold for initial screening evaluation.",
            "Individuals aged 45 to 64 years showed lower adherence to medication.",
            "Pediatric patients under age 18 require specialized pediatric guidelines, not adult age 45 criteria.",
        ]

        for claim in claims:
            hypo = VerificationService.claim_to_hypothesis(claim)
            self.assertNotEqual(
                hypo,
                diabetes_template,
                f"Claim '{claim}' was erroneously rewritten to diabetes template: '{hypo}'"
            )
            # The actual claim content must be present in the hypothesis
            self.assertIn("45", hypo)
            self.assertIn("age", hypo.lower())

    # ─── 4. Generic Claims Unrelated to Diabetes ───────────────────

    def test_hypothesis_generic_claims_unrelated_to_diabetes(self):
        """Test that non-diabetes clinical claims are not forced into diabetes templates."""
        generic_claims = [
            ("Regular aerobic exercise improves cardiovascular endurance and mental health.", "Physical inactivity is a risk factor"),
            ("Depression is associated with altered sleep architecture.", "Depression is a risk factor for type 2 diabetes"),
            ("Obstructive sleep apnea causes daytime hypersomnolence and fatigue.", "Obstructive sleep apnea is an emerging risk factor for type 2 diabetes"),
            ("Acanthosis nigricans can be an indicator of metabolic endocrine dysfunction.", "associated with insulin resistance are risk factors for type 2 diabetes"),
            ("Severe asthma exacerbations require systemic corticosteroid administration.", "type 2 diabetes"),
        ]

        for claim, forbidden_substring in generic_claims:
            hypo = VerificationService.claim_to_hypothesis(claim)
            self.assertNotIn(
                forbidden_substring.lower(),
                hypo.lower(),
                f"Generic claim '{claim}' was rewritten to template containing '{forbidden_substring}': '{hypo}'"
            )
            # Hypothesis must reflect the actual claim
            self.assertTrue(len(hypo) >= len(claim) - 5)

    # ─── 5. Empty and Malformed Candidate Claims ───────────────────

    def test_empty_and_malformed_candidate_claims(self):
        """Test that empty, whitespace, or malformed inputs produce empty hypotheses and empty claims list."""
        malformed_inputs = ["", "   ", "   \n\t  ", None, "[Page 12]", "[]", "[1]"]
        for inp in malformed_inputs:
            hypo = VerificationService.claim_to_hypothesis(inp)
            self.assertEqual(hypo, "", f"Expected empty hypothesis for input: {inp!r}")

        extracted = VerificationService.extract_claims("")
        self.assertEqual(extracted, [])

        extracted_ws = VerificationService.extract_claims("   \n\n   \t  ")
        self.assertEqual(extracted_ws, [])

        extracted_none = VerificationService.extract_claims(None)
        self.assertEqual(extracted_none, [])

    # ─── 6. Heading and Preamble Extraction ────────────────────────

    def test_heading_and_preamble_extraction(self):
        """Test that categorical headings are skipped and conversational preambles are cleanly stripped."""
        text = (
            "Based on the provided medical context, here are the key factors:\n"
            "Primary risk factors:\n"
            "- Physical inactivity increases clinical risk.\n"
            "- Age: 45 years or older.\n"
            "Clinical considerations:\n"
            "According to the guidelines, testing is recommended for adults with BMI >= 25 kg/m²."
        )

        claims = VerificationService.extract_claims(text)

        # Headings should not be extracted as claims
        self.assertNotIn("Primary risk factors:", claims)
        self.assertNotIn("Clinical considerations:", claims)
        self.assertNotIn("Primary risk factors", claims)
        self.assertNotIn("Clinical considerations", claims)

        # Preambles should be stripped from claims
        for claim in claims:
            self.assertFalse(
                claim.lower().startswith("based on the provided"),
                f"Conversational preamble not stripped: {claim}"
            )
            self.assertFalse(
                claim.lower().startswith("according to the guidelines,"),
                f"Conversational preamble not stripped: {claim}"
            )

        # Real factual assertions should be present
        self.assertTrue(any("physical inactivity" in c.lower() for c in claims))
        self.assertTrue(any("45" in c for c in claims))
        self.assertTrue(any("bmi" in c.lower() for c in claims))

    def test_preamble_stripping_examples(self):
        """
        Explicit tests for 'According to the guidelines,' and diverse conversational preambles.
        Verifies that preambles are cleanly stripped while preserving the clinical claim,
        negation, numbers, units, and qualifiers.
        """
        cases = [
            (
                "According to the guidelines, testing is recommended for adults with BMI >= 25 kg/m².",
                "Testing is recommended for adults with BMI >= 25 kg/m²."
            ),
            (
                "Based on the provided medical context, patients with hypertension do not require immediate insulin therapy.",
                "Patients with hypertension do not require immediate insulin therapy."
            ),
            (
                "As per the clinical guidelines, fasting blood glucose should be below 100 mg/dL.",
                "Fasting blood glucose should be below 100 mg/dL."
            ),
            (
                "The retrieved context indicates that screening begins at age 45.",
                "Screening begins at age 45."
            ),
            (
                "It is important to note that individuals under 45 without risk factors do not require routine screening.",
                "Individuals under 45 without risk factors do not require routine screening."
            ),
            (
                "In accordance with current guidelines, metformin remains the first-line pharmacologic agent.",
                "Metformin remains the first-line pharmacologic agent."
            ),
        ]

        for input_text, expected_claim in cases:
            extracted = VerificationService.extract_claims(input_text)
            self.assertEqual(len(extracted), 1, f"Failed to extract single claim for: {input_text!r}")
            self.assertEqual(extracted[0], expected_claim)

        # Multi-sentence paragraph with preamble in non-initial sentence
        paragraph = (
            "Regular physical exercise improves glycemic control. "
            "According to the guidelines, patients with prediabetes should be tested annually."
        )
        extracted_p = VerificationService.extract_claims(paragraph)
        self.assertEqual(len(extracted_p), 2)
        self.assertEqual(extracted_p[0], "Regular physical exercise improves glycemic control.")
        self.assertEqual(extracted_p[1], "Patients with prediabetes should be tested annually.")

    # ─── 7. Incomplete Fragment Rejection ─────────────────────────

    def test_incomplete_fragment_rejection(self):
        """Test that dangling connectors or truncated sentences are not extracted as claims."""
        text = (
            "- Regular physical activity provides substantial cardiovascular benefits.\n"
            "- Patients with hypertension and\n"
            "- Atypical\n"
            "- Risk factors including\n"
            "- Screening should be performed annually for high-risk individuals."
        )

        claims = VerificationService.extract_claims(text)

        self.assertNotIn("Patients with hypertension and", claims)
        self.assertNotIn("Atypical", claims)
        self.assertNotIn("Risk factors including", claims)

        # Valid sentences should be kept
        self.assertEqual(len(claims), 2)
        self.assertTrue(any("physical activity" in c.lower() for c in claims))
        self.assertTrue(any("annually" in c.lower() for c in claims))

    # ─── 8. Irrelevant or Insufficient Evidence ───────────────────

    def test_evidence_irrelevant_or_insufficient(self):
        """Test that insufficient or irrelevant evidence never results in SUPPORTED status."""
        # 1. Missing evidence
        self.assertFalse(VerificationService.is_claim_supported(None))

        # 2. Strong contradiction
        contradicted_ev = {
            "entailment": 0.10,
            "contradiction": 0.85,
            "similarity": 0.30,
            "evidence_score": 0.05,
        }
        self.assertFalse(VerificationService.is_claim_supported(contradicted_ev))

        # 3. Weak / neutral evidence (insufficient support)
        weak_ev = {
            "entailment": 0.40,
            "contradiction": 0.05,
            "similarity": 0.35,
            "evidence_score": 0.35,
        }
        self.assertFalse(VerificationService.is_claim_supported(weak_ev))

        # 4. Strong genuine evidence
        supported_ev = {
            "entailment": 0.88,
            "contradiction": 0.02,
            "similarity": 0.75,
            "evidence_score": 0.82,
        }
        self.assertTrue(VerificationService.is_claim_supported(supported_ev))

    # ─── 9. Legacy Template Toggle Behind Config Flag ─────────────

    def test_legacy_template_configuration_toggle(self):
        """
        Verify that USE_LEGACY_CLAIM_TEMPLATES defaults to False (generic).
        When explicitly enabled for regression comparison, legacy template runs.
        """
        claim = "Physical inactivity"

        # Default (generic): preserves claim and adds declarative period
        self.assertFalse(getattr(settings, "USE_LEGACY_CLAIM_TEMPLATES", False))
        hypo_default = VerificationService.claim_to_hypothesis(claim)
        self.assertEqual(hypo_default, "Physical inactivity.")

        # Explicit toggle to True: uses legacy template
        with patch.object(settings, "USE_LEGACY_CLAIM_TEMPLATES", True):
            hypo_legacy = VerificationService.claim_to_hypothesis(claim)
            self.assertEqual(
                hypo_legacy,
                "Physical inactivity is a risk factor for type 2 diabetes."
            )

    # ─── 10. verify_claims Mocked Pipeline Contract ────────────────

    def test_verify_claims_mocked_contract(self):
        """
        Test verify_claims execution with mocked models.
        Ensures claims, hypotheses, evidence, and consistency_score structure are valid.
        """
        service = VerificationService()
        service._loaded = True

        mock_embedding_model = MagicMock()
        mock_embedding_model.encode.side_effect = lambda texts, **kw: np.ones((len(texts), 384), dtype="float32")

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.zeros((2, 5), dtype="float32"),
            np.zeros((2, 5), dtype="int64")
        )

        mock_chunks = [
            {"chunk_id": "chunk_0", "page": 1, "text": "Adults who are overweight or obese should be tested."}
        ]
        mock_embeddings = np.ones((1, 384), dtype="float32")

        service.nli_score_batch = MagicMock(side_effect=lambda premises, hypotheses, **kw: [
            {"entailment": 0.90, "contradiction": 0.02, "neutral": 0.08}
            for _ in premises
        ])

        answer = (
            "- Testing should be considered in adults who are overweight.\n"
            "- Physical inactivity is a recognized risk factor."
        )

        result = service.verify_claims(
            answer=answer,
            chunks=mock_chunks,
            embeddings=mock_embeddings,
            index=mock_index,
            embedding_model=mock_embedding_model,
            top_n=5,
            batch_size=8
        )

        self.assertIn("claims", result)
        self.assertEqual(result["total_claims"], 2)
        self.assertEqual(result["supported_claims"], 2)
        self.assertEqual(result["consistency_score"], 1.0)

        # Check claim hypothesis preservation
        claim1 = result["claims"][0]
        self.assertIn("Testing should be considered", claim1["hypothesis"])
        self.assertTrue(claim1["supported"])
        self.assertIsNotNone(claim1["evidence"])


if __name__ == "__main__":
    unittest.main()
