"""
Verification service — ported from Notebook 08.

Provides:
  - NLI model loading (cross-encoder/nli-deberta-v3-base)
  - Claim extraction from LLM answers
  - Claim-to-hypothesis mapping
  - Semantic similarity calculation
  - NLI scoring (single-pair and batched)
  - Claim-level evidence verification
  - Confidence scoring (NB06 formula)
  - Hallucination decision
"""

import re
from typing import Optional, List, Dict, Any, Union
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import settings
from app.services.retrieval import is_reference_chunk


class VerificationService:
    def __init__(self):
        self.nli_tokenizer = None
        self.nli_model = None
        self._loaded = False

    # ─── Model Loading ───────────────────────────────────────────

    def load_nli_model(self):
        """Load the NLI model and tokenizer at startup."""
        model_name = settings.NLI_MODEL_NAME
        print(f"Loading NLI model: {model_name}")

        self.nli_tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.nli_model = AutoModelForSequenceClassification.from_pretrained(
            model_name
        )
        self.nli_model.eval()
        self._loaded = True

        print(f"NLI model loaded. Labels: {self.nli_model.config.num_labels}")

    def _ensure_loaded(self):
        if not self._loaded:
            raise RuntimeError(
                "NLI model not loaded. Call load_nli_model() at startup."
            )

    # ─── NLI Scoring ─────────────────────────────────────────────

    def nli_score(self, premise: str, hypothesis: str) -> dict:
        """
        Single-pair NLI inference.
        Returns contradiction, entailment, neutral probabilities.
        Label order for cross-encoder/nli-deberta-v3-base:
          0 = contradiction, 1 = entailment, 2 = neutral
        """
        self._ensure_loaded()

        inputs = self.nli_tokenizer(
            premise, hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=384
        )

        with torch.no_grad():
            outputs = self.nli_model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()

        return {
            "contradiction": float(probs[0]),
            "entailment": float(probs[1]),
            "neutral": float(probs[2]),
        }

    def nli_score_batch(
        self,
        premises: list,
        hypotheses: list,
        batch_size: int = 16
    ) -> list:
        """
        Batched NLI inference — the missing function from Notebook 08.
        Processes premise-hypothesis pairs in batches for efficiency.
        """
        self._ensure_loaded()

        results = []

        for start in range(0, len(premises), batch_size):
            batch_premises = premises[start:start + batch_size]
            batch_hypotheses = hypotheses[start:start + batch_size]

            inputs = self.nli_tokenizer(
                batch_premises,
                batch_hypotheses,
                return_tensors="pt",
                truncation=True,
                max_length=384,
                padding=True
            )

            with torch.no_grad():
                outputs = self.nli_model(**inputs)

            probs = torch.softmax(outputs.logits, dim=1).cpu().numpy()

            for prob in probs:
                results.append({
                    "contradiction": float(prob[0]),
                    "entailment": float(prob[1]),
                    "neutral": float(prob[2]),
                })

        return results

    # ─── Semantic Similarity ─────────────────────────────────────

    @staticmethod
    def semantic_similarity(
        answer: str,
        documents: list,
        embedding_model
    ) -> float:
        """
        Max cosine similarity between answer and retrieved doc chunks.
        Matches Notebook 08 verify_answer().
        """
        if not answer or not documents:
            return 0.0

        answer_embedding = embedding_model.encode(
            [answer], normalize_embeddings=True
        )[0]

        doc_embeddings = embedding_model.encode(
            [doc["text"] for doc in documents],
            normalize_embeddings=True
        )

        similarities = np.dot(doc_embeddings, answer_embedding)
        return float(np.max(similarities))

    # ─── Claim Extraction ────────────────────────────────────────

    @staticmethod
    def extract_claims(answer: str) -> list:
        """
        Extract individual factual claims from a medical answer using general text processing.
        Preserves negation, numbers, units, qualifiers, and clinically important context.
        """
        if not answer or not answer.strip():
            return []

        text = answer.strip()

        # 1. Clean citation references (e.g. [Page 12], [p. 15], [1])
        text = re.sub(r"\[(?:Page|p\.)\s*\d+(?:-\d+)?\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[\d+\]", "", text)

        # 2. Clean markdown bold, italic, code formatting without deleting enclosed content
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        raw_lines = text.splitlines()
        candidate_units = []

        # Common conversational preamble prefixes to strip from sentences
        preamble_regex = re.compile(
            r"^(?:"
            r"(?:based on|according to|in accordance with|as per)\s+(?:the\s+)?(?:(?:provided|medical|retrieved|current|available|clinical)\s+)*(?:context|guidelines?|documents?|evidence|data|literature),?\s*"
            r"|the\s+(?:(?:provided|retrieved|medical|clinical|available)\s+)*(?:context|documents?|guidelines?)\s+(?:states?|indicates?|shows?|recommends?|suggests?|notes?)\s+(?:that\s+)?"
            r"|here\s+(?:are|is)\s+the\s+(?:risk factors|key factors|guidelines|recommendations|details|findings|considerations)\b[\s:]*"
            r"|(?:it\s+is\s+important\s+to\s+note\s+that|it\s+should\s+be\s+noted\s+that|please\s+note\s+that|note\s+that)\s*"
            r")",
            re.IGNORECASE
        )

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line is an itemized list (bullet / number)
            is_list_item = bool(re.match(r"^[-•*]\s+|^\d+[.)]\s+", line))
            clean_line = re.sub(r"^[-•*]\s+|^\d+[.)]\s+", "", line).strip()
            if not clean_line:
                continue

            # Generic heading and category lead-in detection:
            # Any line ending with a colon functions as an introductory lead-in, not a factual assertion
            if clean_line.endswith(":"):
                continue

            # Strip conversational preamble if present at start of line
            clean_line = preamble_regex.sub("", clean_line).strip()
            # If line had a secondary preamble (e.g. "Based on ..., here are the key factors:")
            clean_line = preamble_regex.sub("", clean_line).strip()
            if not clean_line or clean_line.endswith(":"):
                continue

            if is_list_item:
                # List items are already natural units
                candidate_units.append(clean_line)
            else:
                # Prose paragraph: split into sentences conservatively
                # Fixed-width lookbehind (?<=\.) splits at terminal period followed by whitespace and uppercase/digit
                raw_sentences = [
                    s.strip()
                    for s in re.split(r"(?<=\.)\s+(?=[A-Z0-9])", clean_line)
                    if s.strip()
                ]
                # Re-join sentences if split occurred on common abbreviations
                abbrs = ("e.g.", "i.e.", "vs.", "dr.", "mr.", "mrs.", "ms.", "prof.", "fig.", "tab.", "no.", "vol.")
                merged_sentences = []
                for s in raw_sentences:
                    if merged_sentences and merged_sentences[-1].lower().endswith(abbrs):
                        merged_sentences[-1] = merged_sentences[-1] + " " + s
                    else:
                        merged_sentences.append(s)

                for s in merged_sentences:
                    if s:
                        candidate_units.append(s)

        # 3. Filter incomplete fragments, meta-disclaimers, and validate candidate claims
        dangling_endings = re.compile(
            r"\b(?:and|or|with|to|of|for|including|such as|cuts off)$",
            re.IGNORECASE
        )

        valid_claims = []
        seen = set()

        for unit in candidate_units:
            unit = re.sub(r"\s+", " ", unit).strip()
            if not unit:
                continue

            # Strip preamble if present on candidate unit / individual sentence
            unit = preamble_regex.sub("", unit).strip()
            unit = preamble_regex.sub("", unit).strip()
            if not unit:
                continue

            # Remove trailing colon if leftover from an inline label
            unit = re.sub(r":$", "", unit).strip()

            # Capitalize first character if it became lowercase after stripping preamble
            if unit and unit[0].islower():
                unit = unit[0].upper() + unit[1:]

            lower = unit.lower()

            # Skip conversational refusal/disclaimer lines that contain no medical assertions
            if lower.startswith("i am an ai") or lower.startswith("the context does not provide"):
                continue

            # Reject incomplete fragments:
            # - Fewer than 2 words or fewer than 8 characters (single words like 'Atypical' are not claims)
            # - Ends with dangling prepositions/conjunctions
            tokens = unit.split()
            if len(tokens) < 2 or len(unit) < 8:
                continue
            if dangling_endings.search(lower):
                continue

            normalized_key = lower
            if normalized_key not in seen:
                seen.add(normalized_key)
                valid_claims.append(unit)

        return valid_claims

    # ─── Claim-to-Hypothesis Mapping ─────────────────────────────

    @staticmethod
    def _legacy_claim_to_hypothesis(claim: str) -> str:
        """
        Legacy diabetes-specific template mapping (Notebook 08 Cell 22).
        Retained strictly for regression comparison when USE_LEGACY_CLAIM_TEMPLATES=True.
        """
        claim = re.sub(r"\s+", " ", claim).strip()
        claim = re.sub(r"\[[^\]]*\]", "", claim).strip()

        lower = claim.lower()

        # Age
        if ("age" in lower and ("45" in lower or "older" in lower)) or (lower.startswith("age:") and "45" in lower):
            return "Increasing age is a risk factor for type 2 diabetes."

        # Obesity / Overweight
        if ("overweight" in lower or "obese" in lower or "obesity" in lower) and ("bmi" in lower or "weight" in lower):
            return (
                "Overweight or obesity is a risk factor for type 2 diabetes, "
                "with increased risk associated with BMI ≥25 kg/m² "
                "or ≥23 kg/m² for Asian Americans."
            )

        # Prediabetes
        if "prediabetes" in lower and ("a1c" in lower or "igt" in lower or "risk" in lower or "factor" in lower or len(lower.split()) < 6):
            return "Prediabetes is a risk factor for type 2 diabetes."

        # Family history
        if ("family history" in lower or "first-degree relative" in lower or "parent or sibling" in lower) and "diabetes" in lower:
            return (
                "Having a parent or sibling with diabetes "
                "is a risk factor for type 2 diabetes."
            )

        # High-risk populations
        if ("high-risk" in lower or "african american" in lower or "hispanic" in lower or "latino" in lower or "asian american" in lower) and ("race" in lower or "ethnic" in lower or "american" in lower):
            return (
                "Being African American, Hispanic or Latino, "
                "American Indian, Alaska Native, Asian American, "
                "or Pacific Islander American is a risk factor "
                "for type 2 diabetes."
            )

        # Gestational diabetes
        if "gestational" in lower and "diabetes" in lower:
            return (
                "A history of gestational diabetes mellitus "
                "is a risk factor for type 2 diabetes."
            )

        # Physical inactivity
        if "physical inactivity" in lower or ("inactivity" in lower and "physical" in lower) or "sedentary" in lower:
            return "Physical inactivity is a risk factor for type 2 diabetes."

        # Hypertension
        if ("hypertension" in lower or "blood pressure" in lower) and ("140/90" in lower or "bp" in lower or "therapy" in lower or len(lower.split()) < 6):
            return "Hypertension is a risk factor for type 2 diabetes."

        # HDL
        if ("hdl" in lower or "high-density lipoprotein" in lower) and ("35" in lower or "cholesterol" in lower or "low" in lower):
            return (
                "A high-density lipoprotein cholesterol level "
                "of 35 mg/dL or lower is a risk factor for type 2 diabetes."
            )

        # Triglycerides
        if "triglyceride" in lower and ("250" in lower or "high" in lower or "fasting" in lower):
            return (
                "A fasting triglyceride level of 250 mg/dL or higher "
                "is a risk factor for type 2 diabetes."
            )

        # Insulin resistance
        if "acanthosis" in lower or "polycystic" in lower or "pcos" in lower or "insulin resistance" in lower:
            return (
                "Acanthosis nigricans, nonalcoholic steatohepatitis, "
                "polycystic ovary syndrome, and other conditions "
                "associated with insulin resistance are risk factors "
                "for type 2 diabetes."
            )

        # Cardiovascular disease
        if "cardiovascular" in lower or "cvd" in lower or "atherosclerotic" in lower:
            return (
                "Atherosclerotic cardiovascular disease is a risk factor "
                "for type 2 diabetes."
            )

        # Depression
        if "depression" in lower and len(lower.split()) < 6:
            return "Depression is a risk factor for type 2 diabetes."

        # Sleep apnea
        if "sleep apnea" in lower:
            return (
                "Obstructive sleep apnea is an emerging risk factor "
                "for type 2 diabetes."
            )

        # Sleep deprivation
        if "sleep deprivation" in lower and ("6 hours" in lower or "chronic" in lower or len(lower.split()) < 8):
            return (
                "Chronic sleep deprivation of less than 6 hours per day "
                "is an emerging risk factor for type 2 diabetes."
            )

        if "atypical medications" in lower:
            return claim

        return claim

    @staticmethod
    def claim_to_hypothesis(claim: str) -> str:
        """
        Map a medical claim to a normalized NLI hypothesis statement.
        Preserves the actual extracted claim's meaning, negation, numbers, units,
        populations, and qualifiers without hand-written template substitution.
        """
        if not claim or not isinstance(claim, str):
            return ""

        # Check explicit configuration flag for legacy template behavior
        if getattr(settings, "USE_LEGACY_CLAIM_TEMPLATES", False):
            return VerificationService._legacy_claim_to_hypothesis(claim)

        # 1. Clean bracketed citations and empty/reference brackets (e.g. [Page 5], [p. 12], [1], [])
        norm = re.sub(r"\[[^\]]*\]", "", claim).strip()

        # 2. Clean markdown emphasis markers without stripping content
        norm = re.sub(r"\*\*([^*]+)\*\*", r"\1", norm)
        norm = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", norm)
        norm = re.sub(r"__([^_]+)__", r"\1", norm)
        norm = re.sub(r"`([^`]+)`", r"\1", norm)

        # 3. Clean leading bullet markers or numbering if still present
        norm = re.sub(r"^[-•*]\s+|^\d+[.)]\s+", "", norm).strip()

        # 4. Collapse whitespace
        norm = re.sub(r"\s+", " ", norm).strip()

        # Reject empty or purely punctuation inputs
        if not norm or not re.search(r"\w", norm):
            return ""

        # 5. Ensure declarative terminal punctuation for NLI cross-encoder
        if not norm.endswith((".", "!", "?")):
            norm = norm + "."

        return norm


    # ─── Claim Support Decision ──────────────────────────────────

    @staticmethod
    def is_claim_supported(evidence: Optional[dict]) -> bool:
        """
        Determine if a claim is supported by evidence.
        Ported from Notebook 08 Cell 25.
        """
        if not evidence:
            return False

        entailment = float(evidence.get("entailment", 0.0))
        contradiction = float(evidence.get("contradiction", 0.0))
        similarity = float(evidence.get("similarity", 0.0))
        evidence_score = float(evidence.get("evidence_score", 0.0))

        # Strong direct evidence
        if (
            entailment >= 0.80
            and contradiction < 0.20
            and evidence_score >= 0.65
        ):
            return True

        # Good combined semantic + NLI evidence
        if (
            entailment >= 0.65
            and similarity >= 0.45
            and contradiction < 0.10
            and evidence_score >= 0.55
        ):
            return True

        return False

    @staticmethod
    def classify_claim_status(evidence: Union[dict, List[dict], None]) -> str:
        """
        Consolidated 3-way claim classification decision rule shared between
        production and evaluation:
          - "CONTRADICTED": strong NLI contradiction signal
          - "SUPPORTED": meets evidence score, entailment, and similarity thresholds
          - "UNSUPPORTED": missing, irrelevant, or insufficient evidence
        """
        if evidence is None:
            return "UNSUPPORTED"

        if isinstance(evidence, list):
            if not evidence:
                return "UNSUPPORTED"
            # If any candidate chunk shows strong contradiction, flag CONTRADICTED
            for ev in evidence:
                if VerificationService.classify_claim_status(ev) == "CONTRADICTED":
                    return "CONTRADICTED"
            # If any candidate chunk provides verified support, flag SUPPORTED
            for ev in evidence:
                if VerificationService.classify_claim_status(ev) == "SUPPORTED":
                    return "SUPPORTED"
            return "UNSUPPORTED"

        contra = float(evidence.get("contradiction", 0.0))
        ent = float(evidence.get("entailment", 0.0))

        # Contradiction threshold
        if contra >= 0.40 or (contra > ent and contra >= 0.25):
            return "CONTRADICTED"

        if VerificationService.is_claim_supported(evidence):
            return "SUPPORTED"

        return "UNSUPPORTED"

    # ─── Claim-Level Verification (batched) ──────────────────────

    def verify_claims(
        self,
        answer: str,
        chunks: list,
        embeddings: np.ndarray,
        index,
        embedding_model,
        top_n: int = 10,
        batch_size: int = 16
    ) -> dict:
        """
        Batched claim-level verification using generic hypotheses and retrieved evidence.
        """
        self._ensure_loaded()

        # 1. Extract claims
        all_claims = self.extract_claims(answer)
        claims = [c for c in all_claims if c and c.strip()]

        if not claims:
            return {
                "claims": [],
                "supported_claims": 0,
                "total_claims": 0,
                "consistency_score": 0.0,
            }

        # 2. Map to hypotheses
        hypotheses = [self.claim_to_hypothesis(c) for c in claims]

        # Filter valid non-empty hypotheses
        valid_indices = [i for i, h in enumerate(hypotheses) if h and h.strip()]
        if not valid_indices:
            return {
                "claims": [
                    {
                        "claim_number": i + 1,
                        "claim": claim,
                        "hypothesis": hypotheses[i],
                        "supported": False,
                        "evidence": None,
                    }
                    for i, claim in enumerate(claims)
                ],
                "supported_claims": 0,
                "total_claims": len(claims),
                "consistency_score": 0.0,
            }

        valid_hypotheses = [hypotheses[i] for i in valid_indices]

        # 3. Encode hypotheses
        hypothesis_embeddings = embedding_model.encode(
            valid_hypotheses, normalize_embeddings=True
        )
        raw_query_embeddings = embedding_model.encode(
            valid_hypotheses
        ).astype("float32")

        # 4. Retrieve evidence candidates
        search_k = min(max(top_n * 3, 15), len(chunks))
        distances, indices_arr = index.search(raw_query_embeddings, search_k)

        # 5. Normalize stored embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        normalized_embeddings = embeddings / norms

        # 6. Build NLI pairs (prioritize non-reference clinical chunks)
        premises = []
        nli_hypotheses = []
        metadata = []

        for v_pos, claim_idx in enumerate(valid_indices):
            claim_candidates = []
            for rank, chunk_idx in enumerate(indices_arr[v_pos]):
                chunk_idx = int(chunk_idx)
                if chunk_idx < 0 or chunk_idx >= len(chunks):
                    continue

                chunk = chunks[chunk_idx]
                if is_reference_chunk(chunk.get("text", "")):
                    continue

                claim_candidates.append((rank, chunk_idx, chunk))
                if len(claim_candidates) >= top_n:
                    break

            # Backfill if all candidates were bibliography references
            if not claim_candidates:
                for rank, chunk_idx in enumerate(indices_arr[v_pos][:top_n]):
                    chunk_idx = int(chunk_idx)
                    if 0 <= chunk_idx < len(chunks):
                        claim_candidates.append((rank, chunk_idx, chunks[chunk_idx]))

            for rank, chunk_idx, chunk in claim_candidates:
                similarity = float(np.dot(
                    normalized_embeddings[chunk_idx],
                    hypothesis_embeddings[v_pos]
                ))

                premises.append(chunk["text"])
                nli_hypotheses.append(valid_hypotheses[v_pos])
                metadata.append({
                    "claim_idx": claim_idx,
                    "rank": rank + 1,
                    "chunk": chunk,
                    "similarity": similarity,
                })

        # 7. Batched NLI
        if premises:
            nli_results = self.nli_score_batch(
                premises, nli_hypotheses, batch_size=batch_size
            )
        else:
            nli_results = []

        # 8. Select strongest evidence per claim
        best_evidence = [None] * len(claims)

        for meta, nli in zip(metadata, nli_results):
            evidence_score = (
                0.70 * nli["entailment"]
                + 0.30 * meta["similarity"]
                - 0.30 * nli["contradiction"]
            )

            evidence = {
                "chunk_id": meta["chunk"].get("chunk_id", "unknown_chunk"),
                "page": meta["chunk"].get("page"),
                "text": meta["chunk"].get("text", ""),
                "similarity": meta["similarity"],
                "entailment": nli["entailment"],
                "contradiction": nli["contradiction"],
                "neutral": nli["neutral"],
                "evidence_score": evidence_score,
            }

            ci = meta["claim_idx"]
            if (
                best_evidence[ci] is None
                or evidence_score > best_evidence[ci]["evidence_score"]
            ):
                best_evidence[ci] = evidence

        # 9. Evaluate claim support
        results = []
        supported_count = 0

        for i, (claim, hypothesis, evidence) in enumerate(
            zip(claims, hypotheses, best_evidence), start=1
        ):
            supported = self.is_claim_supported(evidence)
            if supported:
                supported_count += 1

            results.append({
                "claim_number": i,
                "claim": claim,
                "hypothesis": hypothesis,
                "supported": supported,
                "status": self.classify_claim_status(evidence),
                "evidence": evidence,
            })

        # 10. Consistency
        consistency_score = supported_count / len(claims) if claims else 0.0

        return {
            "claims": results,
            "supported_claims": supported_count,
            "total_claims": len(claims),
            "consistency_score": consistency_score,
        }

    # ─── Confidence Scoring ──────────────────────────────────────

    @staticmethod
    def calculate_confidence(
        answer: str,
        question: str,
        retrieved_docs: list,
        claim_verification: dict,
        embedding_model
    ) -> dict:
        """
        Final confidence scoring.
        Preserves Notebook 06 formula:
          0.30 × answer semantic similarity
          0.30 × NLI entailment
          0.20 × retrieval quality
          0.20 × claim consistency
        """

        # 1. Answer semantic similarity
        if not answer or not retrieved_docs:
            sem_sim = 0.0
        else:
            answer_emb = embedding_model.encode(
                [answer], normalize_embeddings=True
            )[0]
            doc_embs = embedding_model.encode(
                [d["text"] for d in retrieved_docs],
                normalize_embeddings=True
            )
            sims = np.dot(doc_embs, answer_emb)
            sem_sim = float(np.clip(np.max(sims), 0.0, 1.0))

        # 2. Claim-level NLI entailment
        valid = [
            r for r in claim_verification.get("claims", [])
            if r.get("evidence") and "entailment" in r["evidence"]
        ]
        if valid:
            scores = [r["evidence"]["entailment"] for r in valid]
            nli_ent = float(np.clip(np.mean(scores), 0.0, 1.0))
        else:
            nli_ent = 0.0

        # 3. Retrieval quality
        if retrieved_docs:
            q_emb = embedding_model.encode(
                [question], normalize_embeddings=True
            )[0]
            ret_embs = embedding_model.encode(
                [d["text"] for d in retrieved_docs],
                normalize_embeddings=True
            )
            ret_sims = np.dot(ret_embs, q_emb)
            top_k = min(5, len(ret_sims))
            top_scores = np.sort(ret_sims)[-top_k:]
            ret_quality = float(np.clip(np.mean(top_scores), 0.0, 1.0))
        else:
            ret_quality = 0.0

        # 4. Claim consistency
        consistency = float(claim_verification["consistency_score"])

        # 5. Weighted confidence
        confidence = (
            0.30 * sem_sim
            + 0.30 * nli_ent
            + 0.20 * ret_quality
            + 0.20 * consistency
        )
        confidence = float(np.clip(confidence, 0.0, 1.0))

        # 6. Level
        if confidence >= 0.80:
            level = "HIGH"
        elif confidence >= 0.60:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "semantic_similarity": sem_sim,
            "nli_entailment": nli_ent,
            "retrieval_quality": ret_quality,
            "claim_consistency": consistency,
            "confidence_score": confidence,
            "confidence_level": level,
        }

    # ─── Hallucination Decision ──────────────────────────────────

    @staticmethod
    def determine_decision(
        claim_verification: dict,
        confidence_result: dict
    ) -> dict:
        """
        Final hallucination status.
        Ported from Notebook 08 Cell 32.
        """
        consistency = claim_verification["consistency_score"]
        confidence = confidence_result["confidence_score"]

        # Count strong contradictions
        strong_contradictions = 0
        for result in claim_verification["claims"]:
            ev = result["evidence"]
            if ev and ev["contradiction"] >= 0.50:
                strong_contradictions += 1

        # Decision
        if strong_contradictions > 0:
            decision = "CONTRADICTED"
        elif consistency < 0.60 or confidence < 0.60:
            decision = "POTENTIAL HALLUCINATION"
        else:
            decision = "SUPPORTED"

        return {
            "decision": decision,
            "claim_consistency": consistency,
            "confidence_score": confidence,
            "strong_contradictions": strong_contradictions,
        }


# Module-level singleton
verification_service = VerificationService()
