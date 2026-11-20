# Hybrid search

Hybrid search runs a lexical retriever such as BM25 and a dense retriever side by side and merges their results.

## Reciprocal rank fusion
Reciprocal rank fusion (RRF) merges ranked lists without needing comparable scores. Each document receives the sum of 1 / (k + rank) over every list it appears in, with k usually set to 60. Documents ranked highly by both retrievers rise to the top.

## When to use it
Hybrid search is a strong default for question answering over mixed documents: BM25 catches exact terms and identifiers, while dense retrieval catches paraphrases.
