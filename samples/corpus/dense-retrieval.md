# Dense retrieval

Dense retrieval encodes queries and passages as vectors with an embedding model and ranks passages by vector similarity.

## Similarity
Most systems normalise embeddings to unit length and use cosine similarity, which then equals the dot product. Nearest-neighbour search returns the passages whose vectors point in the most similar direction to the query vector.

## Why it helps
Because embeddings capture meaning, dense retrieval can match a question about "car repair costs" with a passage about "automobile maintenance prices" even when no words overlap.

## Limitations
Dense models can miss exact identifiers and rare terms they never saw in training. They also require an embedding model, which costs compute at indexing time and at query time.
