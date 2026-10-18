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
    "label_definitions": {
        "SUPPORTED": "Claim is directly entailed and substantiated by the indexed NIDDK clinical guideline text.",
        "CONTRADICTED": "Claim asserts a clinical counter-statement directly refuted by the indexed guideline recommendations.",
        "UNSUPPORTED": "Claim is not substantiated by the indexed guideline (out-of-domain query or insufficient evidence).",
    },
    "limitations": [
        "NLI entailment scores measure textual consistency against the indexed 83-page guideline; they do not establish independent medical ground truth across external literature.",
        "A claim classified as UNSUPPORTED indicates the current corpus lacks sufficient evidence; it does not necessarily indicate the statement is false in general medicine.",
        "Benchmark is scoped specifically to diabetes care principles and deliberate hallucination/counter-factual probes.",
    ],
    "reproduction_instructions": "Run 'python -m unittest tests/test_evaluation.py' or call POST /api/evaluation/run."
}

BENCHMARK_ITEMS: List[Dict[str, Any]] = [
    # ── Principle 1: Screening & Risk Factors ───────────────────────
    {
        "id": "BM-01",
        "claim": "Testing for prediabetes and type 2 diabetes should be considered in adults who are overweight or obese and have one or more additional risk factors.",
        "hypothesis": "Overweight or obesity is a risk factor for type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Identify People with Undiagnosed Diabetes and Prediabetes",
        "citation_page": 12,
        "rationale": "Directly stated in Principle 1 recommendations for high-risk adult screening."
    },
    {
        "id": "BM-02",
        "claim": "For all adults without risk factors, testing for prediabetes and diabetes should begin at age 45.",
        "hypothesis": "Increasing age is a risk factor for type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Identify People with Undiagnosed Diabetes and Prediabetes",
        "citation_page": 14,
        "rationale": "Guideline establishes routine testing for all asymptomatic individuals starting at age 45."
    },
    # ── Principle 2: Diagnostic Criteria ────────────────────────────
    {
        "id": "BM-03",
        "claim": "Prediabetes is diagnosed with fasting plasma glucose of 100 to 125 mg/dL, 2-hour oral glucose tolerance test of 140 to 199 mg/dL, or A1C of 5.7% to 6.4%.",
        "hypothesis": "Prediabetes is identified by specific blood glucose and A1C criteria.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 1: Diagnostic Criteria",
        "citation_page": 16,
        "rationale": "Standard diagnostic numerical thresholds defined in the guideline tables."
    },
    # ── Principle 3: Prevention & Lifestyle ─────────────────────────
    {
        "id": "BM-04",
        "claim": "Structured lifestyle intervention programs focusing on weight loss and physical activity can reduce the incidence of type 2 diabetes by up to 58%.",
        "hypothesis": "Intensive lifestyle intervention reduces the risk of developing type 2 diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 2: Support Lifestyle Change",
        "citation_page": 22,
        "rationale": "Cites the Diabetes Prevention Program (DPP) landmark outcome documented in the guideline."
    },
    # ── Principle 4: Glycemic Control & Individualization ───────────
    {
        "id": "BM-05",
        "claim": "Glycemic targets such as A1C should be individualized based on duration of diabetes, age, life expectancy, comorbid conditions, and hypoglycemia risk.",
        "hypothesis": "A1C goals should be tailored to individual patient characteristics.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 4: Facilitate Effective Glycemic Control",
        "citation_page": 34,
        "rationale": "Guideline explicitly mandates personalizing A1C goals rather than applying a rigid single threshold."
    },
    # ── Principle 5: Cardiovascular Risk Management ─────────────────
    {
        "id": "BM-06",
        "claim": "Blood pressure control and statin therapy are recommended to reduce cardiovascular morbidity in adults with diabetes.",
        "hypothesis": "Managing cardiovascular risk factors is essential in diabetes care.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 5: Control Blood Pressure and Lipids",
        "citation_page": 42,
        "rationale": "Guideline dedicates Principle 5 to aggressive multifactorial cardiovascular risk reduction."
    },
    # ── Principle 6: Microvascular & Nephropathy Screening ───────────
    {
        "id": "BM-07",
        "claim": "Screening for diabetic kidney disease should include annual assessment of urinary albumin-to-creatinine ratio and estimated GFR.",
        "hypothesis": "Annual kidney function tests are recommended for people with diabetes.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 6: Detect and Treat Microvascular Complications",
        "citation_page": 48,
        "rationale": "Annual microalbuminuria and eGFR screening are explicit Principle 6 recommendations."
    },

    # ── Contradiction Hallucination Probes ───────────────────────────
    {
        "id": "BM-08",
        "claim": "Adults who are severely overweight or obese should never be screened or tested for type 2 diabetes.",
        "hypothesis": "Overweight individuals do not require diabetes screening.",
        "ground_truth": "CONTRADICTED",
        "principle": "Principle 1 Probe",
        "citation_page": 12,
        "rationale": "Directly refutes Principle 1, which identifies obesity as a primary indication for immediate screening."
    },
    {
        "id": "BM-09",
        "claim": "A fasting plasma glucose concentration of 300 mg/dL is optimal and indicates normal non-diabetic glucose regulation.",
        "hypothesis": "Fasting glucose of 300 mg/dL is normal and healthy.",
        "ground_truth": "CONTRADICTED",
        "principle": "Diagnostic Criteria Probe",
        "citation_page": 16,
        "rationale": "Fasting glucose ≥126 mg/dL is the threshold for diabetes; 300 mg/dL is marked hyperglycemia."
    },
    {
        "id": "BM-10",
        "claim": "An A1C level below 5.7% confirms severe uncontrolled diabetes with acute organ failure risk.",
        "hypothesis": "A1C below 5.7 percent represents severe uncontrolled diabetes.",
        "ground_truth": "CONTRADICTED",
        "principle": "Diagnostic Criteria Probe",
        "citation_page": 16,
        "rationale": "A1C < 5.7% is normal; inverting the threshold is a critical clinical contradiction probe."
    },
    {
        "id": "BM-11",
        "claim": "Lifestyle changes including physical activity and weight loss have no beneficial effect on delaying diabetes progression.",
        "hypothesis": "Lifestyle intervention has no impact on diabetes prevention.",
        "ground_truth": "CONTRADICTED",
        "principle": "Principle 2 Probe",
        "citation_page": 22,
        "rationale": "Contradicts the DPP trial evidence where lifestyle modification reduced diabetes incidence by 58%."
    },

    # ── Out-of-Domain & Insufficient Evidence Probes ─────────────────
    {
        "id": "BM-12",
        "claim": "Internal combustion engines require spark plug replacements every 30,000 miles to prevent misfiring.",
        "hypothesis": "Car engine spark plugs require replacement after 30,000 miles.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Out-of-Domain Probe",
        "citation_page": None,
        "rationale": "Automotive engineering text completely absent from the medical diabetes care guidelines."
    },
    {
        "id": "BM-13",
        "claim": "Amoxicillin and clavulanate should be prescribed as first-line treatment for uncomplicated acute viral rhinovirus infections.",
        "hypothesis": "Antibiotics should be used for viral common cold infections.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Insufficient Evidence / Irrelevant Clinical Probe",
        "citation_page": None,
        "rationale": "No guideline text in the diabetes guidelines addresses upper respiratory viral infections."
    },
    {
        "id": "BM-14",
        "claim": "Superconducting transmon qubits require dilution refrigerators operating at 15 millikelvin for quantum coherence.",
        "hypothesis": "Quantum computing hardware operates at millikelvin temperatures.",
        "ground_truth": "UNSUPPORTED",
        "principle": "Out-of-Domain Probe",
        "citation_page": None,
        "rationale": "Quantum computing physics completely absent from the diabetes corpus."
    },
    {
        "id": "BM-15",
        "claim": "Annual comprehensive foot examinations should be conducted to detect neuropathy, peripheral artery disease, and ulcer risks.",
        "hypothesis": "Comprehensive foot examinations are recommended annually for diabetes patients.",
        "ground_truth": "SUPPORTED",
        "principle": "Principle 7: Check and Care for Feet",
        "citation_page": 56,
        "rationale": "Principle 7 explicitly details visual inspection, sensory testing, and annual comprehensive foot examination."
    },
]
