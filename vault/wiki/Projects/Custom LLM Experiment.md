---
title: Custom LLM Experiment
folder: Projects
source_ids: [src_bc08c49a00]
original_files: ["Custom LLM Assignment README.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Custom LLM Experiment

## Summary

This custom LLM experiment involved training a tiny word-level language model, Karpathy's nanoGPT, from scratch on CPU. Two experiments were conducted, one using a starter corpus and one expanded with teaching files on grammar, opposites, and spatial relations.

## Details

- The model is a tiny word-level language model: Karpathy's nanoGPT (2 blocks, 4 heads, 64-number embeddings, 48-token context), trained from scratch on CPU. *(Custom LLM Assignment README, My Custom LLM Experiment (MBA 290T, Assignment 3))*
- Two experiments were run with identical settings: the supplied starter corpus, then the starter corpus plus my own teaching files for grammar, opposites, and spatial relations. *(Custom LLM Assignment README, My Custom LLM Experiment (MBA 290T, Assignment 3))*
- The model continues short sentences; it is not a chatbot. *(Custom LLM Assignment README, My Custom LLM Experiment (MBA 290T, Assignment 3))*
- Experiment 1 used the starter corpus, while Experiment 2 used the starter corpus plus three plain-text files. *(Custom LLM Assignment README, 1. Corpus, sources, and permissions)*
- The teaching files included passages on grammar, opposites, and spatial relations. *(Custom LLM Assignment README, 1. Corpus, sources, and permissions)*
- Training steps were set to 3,000, which is enough practice for a model this small to learn the sentence patterns. *(Custom LLM Assignment README, 2. My three choices and prediction)*
- The learning rate was set to 0.001, which is large enough to make progress within 3,000 steps and small enough to avoid overshooting. *(Custom LLM Assignment README, 2. My three choices and prediction)*
- The fixed settings across both experiments included seed 42, model size, batch size, steps, learning rate, the 48-case eval suite, and the eval generation settings. *(Custom LLM Assignment README, 3. My runs)*

## Sources

- [[Custom LLM Assignment README|Custom LLM Assignment README]]
  - My Custom LLM Experiment (MBA 290T, Assignment 3) (lines 3-10)
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 1. Corpus, sources, and permissions (lines 19-35)
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 2. My three choices and prediction (lines 45-74)
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 3. My runs (lines 83-103)

## Related notes

- [[Transformer Architecture]] - My A3 nanoGPT model is built from pieces this note describes: token embeddings (64 numbers) and blocks with attention heads (2 blocks, 4 heads).
- [[Transformer Training Methods]] - Both use learning-rate warmup: my A3 run warmed the rate up over the first 100 steps, and this note describes warmup from the original transformer paper.
- [[Custom LLM Training Results]] - The custom LLM experiment conducted two distinct training experiments, and the Custom LLM Training Results section compares their outcomes.
