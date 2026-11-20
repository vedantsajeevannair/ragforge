# Reducing hallucinations

A hallucination is a fluent answer that is not supported by the source material.

## Grounding instructions
Tell the model to answer only from the provided passages and to say when the answer is not present. Ask it to cite passage numbers for every claim so answers can be checked.

## Abstaining
If no passage scores above a relevance threshold, the system should refuse to answer instead of guessing. A clear "I could not find this in the documents" is better than a confident wrong answer.

## Verifying citations
Remove citation markers that point to passages that were never provided, and show the cited snippets to the user next to the answer.
