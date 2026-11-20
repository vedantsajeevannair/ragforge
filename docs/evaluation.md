# Evaluation notes

All numbers come from `python -m app.eval.cli` on `samples/` (9 documents, 40 questions, k = 3,
offline hashing embedder). The corpus is small and on a single topic, so treat the numbers as a
way to compare pipeline changes, not as an estimate of accuracy on your own documents.

## Pipeline comparison (original 26 questions)

| config | hit@1 | hit@3 | MRR | nDCG@3 |
|---|---:|---:|---:|---:|
| BM25 | 0.923 | 0.962 | 0.942 | 0.947 |
| Dense (hashing) | 0.846 | 0.962 | 0.904 | 0.919 |
| Hybrid (RRF) | 0.885 | 0.962 | 0.923 | 0.933 |
| Hybrid + re-rank + query expansion | 0.962 | 0.962 | 0.962 | 0.962 |
| Hybrid + re-rank + expansion + MMR | 0.846 | 0.923 | 0.885 | 0.895 |

Observations:

- Plain RRF sits between its two inputs here: the weaker dense ranker pulls BM25 down on
  a few questions. The term-coverage re-ranker recovers them.
- MMR hurts on this set because every question has exactly one relevant document, so
  diversity only pushes the right document down. It is meant for corpora with many
  near-duplicate chunks.
- The one remaining miss ("Why combine lexical and semantic retrieval?") is a vocabulary gap:
  the relevant document never uses the word "semantic". A neural embedding model would be
  expected to close it; the hashing embedder cannot.

## Harder questions

14 questions were added that paraphrase the source ("exact product codes" for a passage about
exact matches, "almost identical passages" for near-duplicates). On all 40:

| config | hit@1 | hit@3 | MRR |
|---|---:|---:|---:|
| BM25 | 0.925 | 0.975 | 0.950 |
| Dense (hashing) | 0.750 | 0.900 | 0.825 |
| Hybrid, equal weights | 0.825 | 0.925 | 0.875 |
| Hybrid, dense weight 0.5 | 0.875 | 0.975 | 0.921 |
| Hybrid + re-rank + expansion | 0.925 | 0.950 | 0.933 |

The hashing embedder only matches shared words and word pieces, so paraphrases hurt it most.

## Experiments

### Dense weight in fusion

Sweeping the dense weight in RRF (BM25 fixed at 1.0), plain hybrid:

| dense weight | hit@1 | hit@3 | MRR |
|---:|---:|---:|---:|
| 1.0 | 0.825 | 0.925 | 0.875 |
| 0.75 | 0.875 | 0.950 | 0.908 |
| 0.5 | 0.875 | 0.975 | 0.921 |
| 0.3 | 0.925 | 0.975 | 0.946 |

The default is 0.5 for the hashing embedder rather than the best-scoring 0.3, to avoid tuning
too closely to a 40-question set; it is 1.0 when a real embedding model is configured.
Set `RAGFORGE_DENSE_WEIGHT` to override.


### Extractive answer filtering

Two changes to the offline answerer: skip Markdown heading lines, and drop sentences scoring
below 60% of the best sentence.

| | citation precision | phrase recall |
|---|---:|---:|
| before | 0.679 | 0.864 |
| after | 0.891 | 0.864 |

Kept.

### Contextual chunk headers

Prepending the file name and heading path to each chunk before indexing:

| config | hit@1 off | hit@1 on |
|---|---:|---:|
| BM25 | 0.923 | 0.885 |
| Dense | 0.846 | 0.846 |
| Hybrid + re-rank + expansion | 0.962 | 0.962 |

Not kept as the default. Repeating header words in every chunk of a file lowers their IDF and
makes all chunks from the same file look alike to BM25. Available with
`RAGFORGE_CONTEXTUAL_HEADERS=true` or `--headers` in the CLI for corpora with very short sections.

### Text processing fixes (found while testing the UI)

Asking "How does reciprocal rank fusion combine rankings?" returned two unrelated sentences.
Three causes: "rankings" stemmed to "ranking" instead of "rank"; question words ("how",
"does") counted as matches; and "nDCG discounts..." was glued to the previous sentence
because sentences were only split before capital letters.

| | hybrid hit@1 | citation precision | phrase recall |
|---|---:|---:|---:|
| before | 0.875 | 0.842 | 0.806 |
| after | 0.900 | 0.829 | 0.806 |

Retrieval improved and the example answer lost both unrelated sentences; citation precision
dipped slightly across the set. Kept, because the remaining off-topic citations are
vocabulary gaps (listed by `--failures`) that the old behaviour only hid by chance.

## Reproducing

```bash
cd backend
python -m app.eval.cli --corpus ../samples/corpus --dataset ../samples/eval.jsonl --failures
python -m app.eval.cli --corpus ../samples/corpus --dataset ../samples/eval.jsonl --headers
```
