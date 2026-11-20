# Prompting for retrieval-augmented generation

The prompt combines a system instruction, the numbered context passages and the user's question.

## Context ordering
Put the most relevant passages first. Models pay most attention to the beginning and end of long contexts, so burying the key passage in the middle can hurt accuracy.

## Context budget
Limit the total context length. Too many passages raise cost and latency and can distract the model with irrelevant text.

## Temperature
Use a low temperature, around 0 to 0.2, for factual question answering so the model sticks closely to the sources.
