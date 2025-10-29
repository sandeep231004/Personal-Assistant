"""
Re-ranking strategies for RAG to improve retrieval quality.

Why Re-ranking?
- Initial vector search gets "similar" documents
- But similarity != relevance
- Re-ranker uses cross-encoder to score query-document pairs
- More accurate but slower (so we do it AFTER initial retrieval)
"""
from typing import List, Dict
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)


class ReRanker:
    """
    Re-ranking service using Cross-Encoder models.

    How it works:
    1. Vector search retrieves top-K candidates (fast, approximate)
    2. Cross-encoder re-scores each candidate (slow, accurate)
    3. Return top-N after re-ranking

    Example flow:
    Query: "How do I train a neural network?"

    Initial retrieval (10 results):
    - Doc 1: "Neural networks are..." (score: 0.82)
    - Doc 2: "Training involves..." (score: 0.80)
    - Doc 3: "Networks can learn..." (score: 0.79)
    ...

    After re-ranking:
    - Doc 2: "Training involves..." (score: 0.95) <- More relevant!
    - Doc 1: "Neural networks are..." (score: 0.88)
    - Doc 5: "Step-by-step training..." (score: 0.85)
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize re-ranker with cross-encoder model.

        Popular models:
        - cross-encoder/ms-marco-MiniLM-L-6-v2 (RECOMMENDED)
          - Fast, good quality
          - Trained on Microsoft MARCO dataset
          - ~80MB model

        - cross-encoder/ms-marco-MiniLM-L-12-v2
          - Better quality, slower
          - ~120MB model

        - BAAI/bge-reranker-base
          - Excellent quality
          - Slower
          - Good for production

        Args:
            model_name: HuggingFace model name
        """
        logger.info(f"Loading re-ranker model: {model_name}")

        try:
            self.model = CrossEncoder(model_name, max_length=512)
            self.model_name = model_name
            logger.info("Re-ranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load re-ranker model: {e}")
            logger.info("Re-ranking will be disabled")
            self.model = None

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Re-rank documents based on relevance to query.

        Args:
            query: User's search query
            documents: List of document dictionaries with 'content' key
            top_k: Number of top documents to return

        Returns:
            Re-ranked list of documents with updated scores
        """
        if not self.model:
            logger.warning("Re-ranker model not available, returning original order")
            return documents[:top_k]

        try:
            logger.info(f"Re-ranking {len(documents)} documents for query: {query[:50]}...")

            # Prepare query-document pairs
            pairs = [[query, doc['content']] for doc in documents]

            # Get cross-encoder scores
            scores = self.model.predict(pairs)

            # Add rerank scores to documents
            for idx, doc in enumerate(documents):
                doc['rerank_score'] = float(scores[idx])
                # Keep original similarity score for comparison
                if 'similarity_score' in doc:
                    doc['original_score'] = doc['similarity_score']

            # Sort by rerank score (descending)
            reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

            # Return top-k
            top_results = reranked[:top_k]

            logger.info(f"Re-ranking complete. Top result score: {top_results[0]['rerank_score']:.3f}")

            return top_results

        except Exception as e:
            logger.error(f"Error during re-ranking: {e}", exc_info=True)
            return documents[:top_k]


# Singleton instance
_reranker_instance = None


def get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    enable: bool = True
) -> ReRanker:
    """
    Get or create re-ranker instance.

    Args:
        model_name: Cross-encoder model to use
        enable: Whether to enable re-ranking

    Returns:
        ReRanker instance or None if disabled
    """
    global _reranker_instance

    if not enable:
        return None

    if _reranker_instance is None:
        _reranker_instance = ReRanker(model_name)

    return _reranker_instance


"""
UNDERSTANDING RE-RANKING IN DEPTH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. WHY RE-RANKING IS NEEDED

Vector Search (Bi-Encoder):
✓ Fast - encodes query & documents separately
✓ Scalable - can search millions of docs
✗ Approximate - uses cosine similarity on vectors
✗ Misses nuance - "king" and "queen" are similar vectors but different meanings

Re-Ranking (Cross-Encoder):
✓ Accurate - processes query+document together
✓ Captures nuance - understands relationship
✗ Slow - must process each pair
✗ Not scalable for large datasets

Solution: Combine both!
1. Vector search: Get top 20-50 candidates (fast)
2. Re-rank: Score top candidates accurately (slow but only on few docs)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. HOW CROSS-ENCODERS WORK

Bi-Encoder (for vector search):
    Query → Encoder → Vector
    Doc   → Encoder → Vector
    Similarity = cosine(Query Vector, Doc Vector)

Cross-Encoder (for re-ranking):
    [Query, Doc] → Encoder → Relevance Score
    Processes both together - can see relationships!

Example:
Query: "best programming language for beginners"
Doc1: "Python is easy to learn"
Doc2: "Python programming language guide"

Bi-Encoder might prefer Doc2 (more keyword matches)
Cross-Encoder understands Doc1 better answers "for beginners"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. WHEN TO USE RE-RANKING

Use Re-Ranking When:
✓ Retrieval quality is critical
✓ Have small-to-medium result sets (<100 docs)
✓ Query is complex or ambiguous
✓ Can afford slight latency increase (~100-500ms)

Skip Re-Ranking When:
✓ Speed is critical
✓ Large result sets (>100 docs)
✓ Simple keyword queries
✓ Limited compute resources

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. CONFIGURATION TRADE-OFFS

Initial Retrieval: top_k=10
Re-rank to: top_n=3

Pros:
- Fast (only re-rank 10)
- Good quality (cross-encoder on finalists)

Cons:
- Might miss relevant docs if not in top 10

Initial Retrieval: top_k=50
Re-rank to: top_n=5

Pros:
- Better recall (more candidates)
- Less likely to miss relevant docs

Cons:
- Slower (re-rank 50 docs)
- Diminishing returns after ~20-30

RECOMMENDED:
- Retrieve: 15-20 candidates
- Re-rank to: 3-5 final results
- Good balance of speed and quality

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. ALTERNATIVE: COHERE RE-RANK API

Cohere provides a re-ranking API:
- Best-in-class quality
- No local model loading
- Free tier: 1000 requests/month
- Paid: $1 per 1000 re-rank requests

Usage:
```python
import cohere
co = cohere.Client(api_key)
results = co.rerank(
    query="Python tutorial",
    documents=docs,
    top_n=3,
    model="rerank-english-v2.0"
)
```

Pros:
✓ Better quality than open-source
✓ No model loading overhead
✓ Multilingual support

Cons:
✗ API costs
✗ Requires internet
✗ Privacy considerations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. MEASURING RE-RANKING IMPACT

Metrics to track:
- MRR (Mean Reciprocal Rank): Position of first relevant result
- NDCG (Normalized Discounted Cumulative Gain): Overall ranking quality
- User satisfaction: Click-through rate, time to find answer

Before re-ranking:
Query: "reset password"
Results: [Setup guide, API docs, Password reset, ...]
MRR: 1/3 = 0.33

After re-ranking:
Results: [Password reset, Setup guide, API docs, ...]
MRR: 1/1 = 1.0

Improvement: 3x better!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""