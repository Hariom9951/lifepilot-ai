from typing import Any


class RAGReranker:
    """Lightweight local reranking engine combining keyword density and semantic scores."""

    @staticmethod
    def rerank(
        query: str, matches: list[dict[str, Any]], top_n: int = 5
    ) -> list[dict[str, Any]]:
        """
        Fuses the vector similarity score with keyword overlap density.
        """
        if not matches:
            return []

        query_words = set(query.lower().split())
        reranked_matches = []

        for match in matches:
            content = match.get("content", "").lower()
            orig_score = match.get("score", 0.0)

            # Proximity/Overlap text matching density
            if query_words:
                matched_words = sum(1 for word in query_words if word in content)
                overlap_score = matched_words / len(query_words)
                final_score = 0.6 * orig_score + 0.4 * overlap_score
            else:
                final_score = orig_score

            match_copy = dict(match)
            match_copy["score"] = round(float(final_score), 4)
            reranked_matches.append(match_copy)

        reranked_matches.sort(key=lambda x: x["score"], reverse=True)
        return reranked_matches[:top_n]
