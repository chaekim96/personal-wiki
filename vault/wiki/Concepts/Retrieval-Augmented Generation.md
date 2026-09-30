---
title: Retrieval-Augmented Generation
folder: Concepts
source_ids: [src_a442819898]
original_files: ["Wikipedia - Retrieval-augmented generation.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Retrieval-Augmented Generation

## Summary

Retrieval-augmented generation (RAG) is a technique that allows large language models (LLMs) to retrieve and incorporate new information from external data sources. This process supplements the LLM's pre-existing training data, enabling them to use domain-specific or updated information. RAG improves LLM performance by blending the LLM process with information retrieval to help LLMs stick to facts and reduce AI hallucinations.

## Details

- Retrieval-augmented generation (RAG) is a technique that enables large language models (LLMs) to retrieve and incorporate new information from external data sources. *(Retrieval-augmented generation, Introduction)*
- RAG improves LLMs by incorporating information retrieval before generating responses. *(Retrieval-augmented generation, Introduction)*
- RAG pulls relevant text from databases, uploaded documents, or web sources. *(Retrieval-augmented generation, Introduction)*
- This method helps reduce AI hallucinations, which have caused chatbots to describe policies that don't exist, or recommend nonexistent legal cases to lawyers that are looking for citations to support their arguments. *(Retrieval-augmented generation, Introduction)*
- RAG also reduces the need to retrain LLMs with new data, saving on computational and financial costs. *(Retrieval-augmented generation, Introduction)*
- Beyond efficiency gains, RAG also allows LLMs to include sources in their responses, so users can verify the cited sources. *(Retrieval-augmented generation, Introduction)*
- The term retrieval-augmented generation (RAG) was introduced in a 2020 paper that described combining a parametric language model with a non-parametric external memory accessed through retrieval at inference time. *(Retrieval-augmented generation, Introduction)*
- Typically, the data to be referenced is converted into LLM embeddings, numerical representations in the form of a large vector space. *(Retrieval-augmented generation, RAG key stages)*
- Given a user query, a document retriever is first called to select the most relevant documents that will be used to augment the query. *(Retrieval-augmented generation, RAG key stages)*
- The model feeds this relevant retrieved information into the LLM via prompt engineering of the user's original query. *(Retrieval-augmented generation, RAG key stages)*
- Finally, the LLM can generate output based on both the query and the retrieved documents. *(Retrieval-augmented generation, RAG key stages)*
- RAG is used in applications where generated responses need to be grounded in external or frequently updated information. *(Retrieval-augmented generation, Applications)*

## Sources

- [[Wikipedia - Retrieval-augmented generation|Retrieval-augmented generation]] · [Wikipedia permalink](https://en.wikipedia.org/w/index.php?oldid=1377227095) · CC BY-SA 4.0
  - Introduction (lines 8-11)
  - RAG and LLM limitations (lines 15-16)
  - Process (lines 20-20)
  - Process > RAG key stages (lines 25-28)
  - Applications (lines 32-33)
  - Improvements (lines 37-37)
  - Improvements > Encoder (lines 41-46)
  - Improvements > Retriever-centric methods (lines 50-54)
  - Improvements > Language model (lines 59-60)
  - Improvements > Chunking (lines 65-65)
  - Improvements > Hybrid search (lines 69-69)
  - Challenges (lines 73-74)

## Related notes

- (none: my current sources do not state a direct connection to the other notes)
