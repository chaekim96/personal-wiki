---
title: Custom LLM Evaluation
folder: Projects
source_ids: [src_bc08c49a00]
original_files: ["Custom LLM Assignment README.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Custom LLM Evaluation

## Summary

The fixed 48-case language eval suite I ran on my A3 nanoGPT model before and after training. A case scores 1 only if the correct word has the highest probability of its four choices; the results show the model learned templates rather than language.

## Details

- The scoring rule states that only the prefix goes into the model, with no answer choices or key. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- A case scores 1 if the correct word has the highest probability among its four choices, and ties result in a score of 0. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- Any unknown prompt or answer word marks the case as `out_of_vocabulary`, which counts as 0 in the all-case rate. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- A separate free continuation is generated for every case with a temperature of 0.8, per-case seed, and 24 tokens, but it is not scored. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- The coverage rose from 24/48 to 26/48 because my files made 1 opposites case and 1 spatial case scorable. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- Training cannot change coverage; only corpus text can. *(Custom LLM Assignment README, 7. Fixed language evals (48 cases))*
- The model learned templates, not language, with 16/16 success on familiar patterns, but new wording was mostly guessing in Experiment 1. *(Custom LLM Assignment README, 9. Limitation and next experiment)*

## Sources

- [[Custom LLM Assignment README|Custom LLM Assignment README]]
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 7. Fixed language evals (48 cases) (lines 274-356)
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 9. Limitation and next experiment (lines 412-416)

## Related notes

- [[Transformer Architecture]] - The Transformer Architecture provides the foundational structure for the language models used in custom LLM experiments.
- [[Custom LLM Experiment]] - The Custom LLM Experiment details the specific training process that informs the evaluation metrics described in the current note.
