# Evaluating RAG systems

Retrieval and generation should be evaluated separately so failures can be traced to the right stage.

## Retrieval metrics
Recall@k measures the share of relevant documents found in the top k results. Mean reciprocal rank (MRR) rewards putting the first relevant result near the top. nDCG discounts relevant results that appear lower in the ranking.

## Answer metrics
Groundedness checks whether the answer is supported by the retrieved passages. Citation precision measures the share of cited passages that are actually relevant. Keep a small labelled question set and rerun it after every change to chunking, embeddings or prompts.
