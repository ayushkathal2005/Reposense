from typing import List, Dict, Any, Set, Optional

class BenchmarkScorer:
    """Calculates factual, deterministic evaluation metrics for RepoSense intelligence."""

    @staticmethod
    def calculate_recall_at_k(retrieved_items: List[str], ground_truth_items: List[str], k: int = 5) -> float:
        if not ground_truth_items:
            return 1.0
        top_k = retrieved_items[:k]
        hits = sum(
            1 for gt in ground_truth_items
            if any(gt.lower() in item.lower() for item in top_k)
        )
        return float(hits) / float(len(ground_truth_items))

    @staticmethod
    def calculate_evidence_correctness(
        retrieved_evidence: List[Dict[str, Any]],
        expected_files: List[str]
    ) -> float:
        if not retrieved_evidence or not expected_files:
            return 1.0 if not expected_files else 0.0

        matches = 0
        for ev in retrieved_evidence:
            ev_file = ev.get("file", "") or ev.get("file_path", "")
            if any(ef in ev_file for ef in expected_files):
                matches += 1

        return float(matches) / float(len(retrieved_evidence))

    @staticmethod
    def calculate_path_accuracy(
        predicted_path: List[str],
        expected_path: List[str]
    ) -> float:
        if not expected_path:
            return 1.0
        if not predicted_path:
            return 0.0

        # Exact subsequence alignment
        matches = 0
        pred_idx = 0
        for exp_step in expected_path:
            found = False
            while pred_idx < len(predicted_path):
                if exp_step.lower() in predicted_path[pred_idx].lower():
                    found = True
                    pred_idx += 1
                    break
                pred_idx += 1
            if found:
                matches += 1

        return float(matches) / float(len(expected_path))

    @staticmethod
    def calculate_citation_correctness(citations: List[str], valid_files: Set[str]) -> float:
        if not citations:
            return 0.0
        valid_citations = 0
        for cit in citations:
            file_part = cit.split(":")[0] if ":" in cit else cit
            if any(vf in file_part for vf in valid_files):
                valid_citations += 1
        return float(valid_citations) / float(len(citations))

    @staticmethod
    def calculate_hallucination_rate(
        referenced_symbols: List[str],
        known_graph_symbols: Set[str]
    ) -> float:
        if not referenced_symbols:
            return 0.0
        hallucinated = 0
        for sym in referenced_symbols:
            if not any(ks in sym or sym in ks for ks in known_graph_symbols):
                hallucinated += 1
        return float(hallucinated) / float(len(referenced_symbols))
