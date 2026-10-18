"""
Benchmark dataset for Medical RAG Hallucination Detection.

Provenance:
  Document: "Guiding Principles for the Care of People With or at Risk for Diabetes"
  Publisher: National Diabetes Education Program (NDEP), NIH Publication No. 14-4343
  Total Guideline Pages: 83
  Corpus Size: 268 chunk FAISS index

Labels:
  - SUPPORTED: Entailed by specific clinical guideline text.
  - CONTRADICTED: Explicitly contradicts guideline recommendations (hallucination test probe).
  - UNSUPPORTED: Not supported by the guideline corpus (insufficient evidence or out-of-domain).
"""

from typing import List, Dict, Any

BENCHMARK_PROVENANCE: Dict[str, Any] = {
    "source_document": "NIDDK Guiding Principles for the Care of People With or at Risk for Diabetes",
    "publisher": "National Diabetes Education Program • NIH / CDC",
    "document_pages": 83,
    "vector_chunks": 268,
    "benchmark_type": "Curated Gold Regression Suite (Smoke Benchmark)",
    "dataset_scope": "Small, high-precision regression probe suite (15 items) designed for deterministic pipeline validation; not a statistical train/dev/test split.",
    "page_verification_method": "Programmatic text inspection aligning citation_page to 0-indexed PyMuPDF/FAISS chunk page metadata while preserving original booklet_page.",
    "label_definitions": {
        "SUPPORTED": "Claim is directly entailed and substantiated by the indexed NIDDK clinical guideline text.",
        "CONTRADICTED": "Claim asserts a clinical counter-statement directly refuted by the indexed guideline recommendations.",
        "UNSUPPORTED": "Claim is not substantiated by the indexed guideline (out-of-domain query or insufficient evidence).",
    },
    "limitations": [
        "NLI entailment scores measure textual consistency against the indexed 83-page guideline; they do not establish independent medical ground truth across external literature.",
        "A claim classified as UNSUPPORTED indicates the current corpus lacks sufficient evidence; it does not necessarily indicate the statement is false in general medicine.",
        "Benchmark is scoped specifically to diabetes care principles and deliberate hallucination/counter-factual probes.",
        "With 15 total items, this dataset serves as a deterministic regression test suite; it does not support an empirical train/dev/test statistical split.",
    ],
    "reproduction_instructions": "Run 'python -m unittest tests/test_evaluation.py' or call POST /api/evaluation/run."
}

BENCHMARK_ITEMS: List[Dict[str, Any]] = [
    # ── Principle 1: Screening & Risk Factors ───────────────────────
    {
        "id": "BM-01",
        "claim": "Testing for prediabetes and type 2 diabetes should be considered in adults who are overweight or obese and have one or more additional risk factors.",
        "hypothesis": "Testing for prediabetes and type 2 diabetes should be considered in adults who are overweight or obese and have one or more additional risk factors.",
        "legacy_hypothesis": "Overweight or obesity is a risk factor for type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Identify People with Undiagnosed Diabetes and Prediabetes",
        "citation_page": 8,
        "booklet_page": 12,
        "verified_chunk_id": "page_8_chunk_1",
        "verification_status": "VERIFIED",
        "rationale": "Directly stated in Principle 1 (PDF p. 8, chunk page_8_chunk_1) for adults with BMI >= 25 kg/m² and risk factors."
    },
    {
        "id": "BM-02",
        "claim": "For all adults without risk factors, testing for prediabetes and diabetes should begin at age 45.",
        "hypothesis": "For all adults without risk factors, testing for prediabetes and diabetes should begin at age 45.",
        "legacy_hypothesis": "Increasing age is a risk factor for type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Identify People with Undiagnosed Diabetes and Prediabetes",
        "citation_page": 8,
        "booklet_page": 14,
        "verified_chunk_id": "page_8_chunk_1",
        "verification_status": "FLAGGED_FOR_HUMAN_REVIEW",
        "rationale": "Guideline Principle 1 (PDF p. 8-10) cites USPSTF screening ages 40-70 and Table 1 increasing age risk; age 45 threshold is an ADA standard adaptation requiring human review."
    },
    # ── Principle 2: Diagnostic Criteria ────────────────────────────
    {
        "id": "BM-03",
        "claim": "Prediabetes is diagnosed with fasting plasma glucose of 100 to 125 mg/dL, 2-hour oral glucose tolerance test of 140 to 199 mg/dL, or A1C of 5.7% to 6.4%.",
        "hypothesis": "Prediabetes is diagnosed with fasting plasma glucose of 100 to 125 mg/dL, 2-hour oral glucose tolerance test of 140 to 199 mg/dL, or A1C of 5.7% to 6.4%.",
        "legacy_hypothesis": "Prediabetes is identified by specific blood glucose and A1C criteria.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Diagnostic Criteria",
        "citation_page": 11,
        "booklet_page": 16,
        "verified_chunk_id": "page_11_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Explicit numerical diagnostic criteria specified in Table 2 (PDF p. 11, chunk page_11_chunk_0)."
    },
    # ── Principle 3: Prevention & Lifestyle ─────────────────────────
    {
        "id": "BM-04",
        "claim": "Structured lifestyle intervention programs focusing on weight loss and physical activity can reduce the incidence of type 2 diabetes by up to 58%.",
        "hypothesis": "Structured lifestyle intervention programs focusing on weight loss and physical activity can reduce the incidence of type 2 diabetes by up to 58%.",
        "legacy_hypothesis": "Intensive lifestyle intervention reduces the risk of developing type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 2: Support Lifestyle Change",
        "citation_page": 15,
        "booklet_page": 22,
        "verified_chunk_id": "page_15_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Cites the Diabetes Prevention Program (DPP) trial finding of 58% risk reduction in Principle 2 (PDF p. 15, chunk page_15_chunk_0)."
    },
    # ── Principle 4: Glycemic Control & Individualization ───────────
    {
        "id": "BM-05",
        "claim": "Glycemic targets such as A1C should be individualized based on duration of diabetes, age, life expectancy, comorbid conditions, and hypoglycemia risk.",
        "hypothesis": "Glycemic targets such as A1C should be individualized based on duration of diabetes, age, life expectancy, comorbid conditions, and hypoglycemia risk.",
        "legacy_hypothesis": "A1C goals should be tailored to individual patient characteristics.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 4: Facilitate Effective Glycemic Control",
        "citation_page": 49,
        "booklet_page": 34,
        "verified_chunk_id": "page_49_chunk_2",
        "verification_status": "VERIFIED",
        "rationale": "Principle 4 explicitly mandates individualizing A1C targets based on duration of diabetes, patient characteristics, and hypoglycemia risks (PDF p. 49, chunk page_49_chunk_2; legacy benchmark had listed booklet page 34)."
    },
    # ── Principle 5: Cardiovascular Risk Management ─────────────────
    {
        "id": "BM-06",
        "claim": "Blood pressure control and statin therapy are recommended to reduce cardiovascular morbidity in adults with diabetes.",
        "hypothesis": "Blood pressure control and statin therapy are recommended to reduce cardiovascular morbidity in adults with diabetes.",
        "legacy_hypothesis": "Managing cardiovascular risk factors is essential in diabetes care.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 5: Control Blood Pressure and Lipids",
        "citation_page": 58,
        "booklet_page": 42,
        "verified_chunk_id": "page_58_chunk_1",
        "verification_status": "VERIFIED",
        "rationale": "Principle 5 establishes multi-drug BP control and statin therapy for CVD risk reduction (PDF pp. 58-59, chunk page_58_chunk_1)."
    },
    # ── Principle 6: Microvascular & Nephropathy Screening ───────────
    {
        "id": "BM-07",
        "claim": "Screening for diabetic kidney disease should include annual assessment of urinary albumin-to-creatinine ratio and estimated GFR.",
        "hypothesis": "Screening for diabetic kidney disease should include annual assessment of urinary albumin-to-creatinine ratio and estimated GFR.",
        "legacy_hypothesis": "Annual kidney function tests are recommended for people with diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 6: Detect and Treat Microvascular Complications",
        "citation_page": 67,
        "booklet_page": 48,
        "verified_chunk_id": "page_67_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Principle 6 recommends annual assessment of spot urine UACR and eGFR (PDF p. 67, chunk page_67_chunk_0)."
    },

    # ── Contradiction Hallucination Probes ───────────────────────────
    {
        "id": "BM-08",
        "claim": "Adults who are severely overweight or obese should never be screened or tested for type 2 diabetes.",
        "hypothesis": "Adults who are severely overweight or obese should never be screened or tested for type 2 diabetes.",
        "legacy_hypothesis": "Overweight individuals do not require diabetes screening.",
        "ground_truth": "CONTRADICTED",
        "principle": "Principle 1 Probe",
        "citation_page": 8,
        "booklet_page": 12,
        "verified_chunk_id": "page_8_chunk_1",
        "verification_status": "VERIFIED",
        "rationale": "Directly refutes Principle 1 (PDF p. 8), which identifies overweight/obesity as a primary screening indication."
    },
    {
        "id": "BM-09",
        "claim": "A fasting plasma glucose concentration of 300 mg/dL is optimal and indicates normal non-diabetic glucose regulation.",
        "hypothesis": "A fasting plasma glucose concentration of 300 mg/dL is optimal and indicates normal non-diabetic glucose regulation.",
        "legacy_hypothesis": "Fasting glucose of 300 mg/dL is normal and healthy.",
        "ground_truth": "CONTRADICTED",
        "principle": "Diagnostic Criteria Probe",
        "citation_page": 11,
        "booklet_page": 16,
        "verified_chunk_id": "page_11_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Table 2 (PDF p. 11) sets FPG >= 126 mg/dL as diagnostic of diabetes; 300 mg/dL represents severe hyperglycemia."
    },
    {
        "id": "BM-10",
        "claim": "An A1C level below 5.7% confirms severe uncontrolled diabetes with acute organ failure risk.",
        "hypothesis": "An A1C level below 5.7% confirms severe uncontrolled diabetes with acute organ failure risk.",
        "legacy_hypothesis": "A1C below 5.7 percent represents severe uncontrolled diabetes.",
        "ground_truth": "CONTRADICTED",
        "principle": "Diagnostic Criteria Probe",
        "citation_page": 11,
        "booklet_page": 16,
        "verified_chunk_id": "page_11_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Table 2 (PDF p. 11) establishes A1C < 5.7% as the normal non-diabetic reference range."
    },
    {
        "id": "BM-11",
        "claim": "Lifestyle changes including physical activity and weight loss have no beneficial effect on delaying diabetes progression.",
        "hypothesis": "Lifestyle changes including physical activity and weight loss have no beneficial effect on delaying diabetes progression.",
        "legacy_hypothesis": "Lifestyle intervention has no impact on diabetes prevention.",
        "ground_truth": "CONTRADICTED",
        "principle": "Principle 2 Probe",
        "citation_page": 15,
        "booklet_page": 22,
        "verified_chunk_id": "page_15_chunk_0",
        "verification_status": "VERIFIED",
        "rationale": "Contradicts Principle 2 DPP trial outcome where lifestyle intervention reduced diabetes progression by 58% (PDF p. 15)."
    },

    # ── Out-of-Domain & Insufficient Evidence Probes ─────────────────
    {
        "id": "BM-12",
        "claim": "Internal combustion engines require spark plug replacements every 30,000 miles to prevent misfiring.",
        "hypothesis": "Internal combustion engines require spark plug replacements every 30,000 miles to prevent misfiring.",
        "legacy_hypothesis": "Car engine spark plugs require replacement after 30,000 miles.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Out-of-Domain Probe",
        "citation_page": None,
        "booklet_page": None,
        "verified_chunk_id": None,
        "verification_status": "NOT_APPLICABLE",
        "rationale": "Automotive engineering text completely absent from the medical diabetes care guidelines."
    },
    {
        "id": "BM-13",
        "claim": "Amoxicillin and clavulanate should be prescribed as first-line treatment for uncomplicated acute viral rhinovirus infections.",
        "hypothesis": "Amoxicillin and clavulanate should be prescribed as first-line treatment for uncomplicated acute viral rhinovirus infections.",
        "legacy_hypothesis": "Antibiotics should be used for viral common cold infections.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Insufficient Evidence / Irrelevant Clinical Probe",
        "citation_page": None,
        "booklet_page": None,
        "verified_chunk_id": None,
        "verification_status": "NOT_APPLICABLE",
        "rationale": "No guideline text in the diabetes guidelines addresses upper respiratory viral infections."
    },
    {
        "id": "BM-14",
        "claim": "Superconducting transmon qubits require dilution refrigerators operating at 15 millikelvin for quantum coherence.",
        "hypothesis": "Superconducting transmon qubits require dilution refrigerators operating at 15 millikelvin for quantum coherence.",
        "legacy_hypothesis": "Quantum computing hardware operates at millikelvin temperatures.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Out-of-Domain Probe",
        "citation_page": None,
        "booklet_page": None,
        "verified_chunk_id": None,
        "verification_status": "NOT_APPLICABLE",
        "rationale": "Quantum computing physics completely absent from the diabetes corpus."
    },
    {
        "id": "BM-15",
        "claim": "Annual comprehensive foot examinations should be conducted to detect neuropathy, peripheral artery disease, and ulcer risks.",
        "hypothesis": "Annual comprehensive foot examinations should be conducted to detect neuropathy, peripheral artery disease, and ulcer risks.",
        "legacy_hypothesis": "Comprehensive foot examinations are recommended annually for diabetes patients.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 7: Check and Care for Feet",
        "citation_page": 70,
        "booklet_page": 56,
        "verified_chunk_id": "page_70_chunk_2",
        "verification_status": "VERIFIED",
        "rationale": "Principle 7 explicitly details annual comprehensive foot examinations to evaluate neuropathy and ulcer risks (PDF p. 70, chunk page_70_chunk_2)."
    },
]
