# Chunking strategies

Documents are split into chunks before indexing because embedding models and LLM context windows have limited length, and smaller passages make retrieval more precise.

## Fixed-size chunking
Fixed-size chunking cuts text every N characters with some overlap. It is simple but can cut sentences in half.

## Recursive chunking
Recursive chunking tries paragraph breaks first, then line breaks, then sentence ends, then spaces, so chunks end at natural boundaries while staying under the size limit.

## Overlap
An overlap of 10 to 20 percent of the chunk size keeps facts that straddle a boundary retrievable from at least one chunk.

## Heading-aware chunking
For Markdown, splitting on headings and storing the heading path with each chunk gives the model useful context, such as "Installation > Linux".
