# Re-ranking and diversity

First-stage retrievers are tuned for recall. A re-ranker then reorders a small candidate pool for precision.

## Cross-encoders
A cross-encoder reads the query and a passage together and outputs a relevance score. It is more accurate than comparing separate embeddings but too slow to run over the whole corpus, so it is applied only to the top candidates.

## Maximal marginal relevance
Maximal marginal relevance (MMR) selects passages that are relevant to the query but not too similar to passages already selected. A lambda of 1.0 gives pure relevance; lower values trade relevance for diversity. MMR stops the context window filling up with near-duplicate chunks.
