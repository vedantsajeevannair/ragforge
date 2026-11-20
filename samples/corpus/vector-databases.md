# Vector databases

A vector database stores embeddings together with metadata and answers nearest-neighbour queries.

## Exact versus approximate search
Exact (brute-force) search compares the query with every vector and is fine up to a few hundred thousand vectors. Approximate nearest-neighbour indexes such as HNSW trade a little recall for much lower latency on millions of vectors.

## Metadata filtering
Filters restrict a search to vectors whose metadata matches, for example one collection, one file type or documents a user is allowed to see. Applying the filter during search avoids returning fewer than k results.
