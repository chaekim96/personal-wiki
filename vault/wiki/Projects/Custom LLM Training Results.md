---
title: Custom LLM Training Results
folder: Projects
source_ids: [src_bc08c49a00]
original_files: ["Custom LLM Assignment README.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Custom LLM Training Results

## Summary

The training results of my A3 nanoGPT runs: how samples improved from random words to template sentences, what the loss values mean, and how sampling temperature changed the output of the same trained weights.

## Details

- Same trained weights, same starting token and sampling seed; only the temperature differs. *(Custom LLM Assignment README, 6. Temperature comparison)*
- In Experiment 1, temperature barely mattered. *(Custom LLM Assignment README, 6. Temperature comparison)*
- 0.8 and 1.2 gave identical samples in Experiment 1. *(Custom LLM Assignment README, 6. Temperature comparison)*
- At temperature 0.3 in Experiment 1, one sample swapped a single word (deposit → investment) and one became a different sentence entirely. *(Custom LLM Assignment README, 6. Temperature comparison)*
- In Experiment 2, 1.2 produced a garbled line, because a 481-word vocabulary has more low-probability tail to sample from. *(Custom LLM Assignment README, 6. Temperature comparison)*
- Temperature changes the odds before the pick. Low makes the top word win more, high spreads it out. The weights never change. *(Custom LLM Assignment README, 6. Temperature comparison)*

- Samples changed from random words to complete template sentences by step 1,500, with little change after that. *(Custom LLM Assignment README, 4. Evidence: samples and loss, line 138)*
- Step-0 loss is about ln(vocabulary size): ln 136 ≈ 4.91, ln 481 ≈ 6.18, which is a uniform guess. *(Custom LLM Assignment README, 4. Evidence: samples and loss, line 171)*
- In Experiment 2, no sample uses my new material; the new files are only ~7% of the training passages. *(Custom LLM Assignment README, 4. Evidence: samples and loss, lines 140-141)*

## Sources

- [[Custom LLM Assignment README|Custom LLM Assignment README]]
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 4. Evidence: samples and loss (lines 113-171)
  - My Custom LLM Experiment (MBA 290T, Assignment 3) > 6. Temperature comparison (lines 249-264)

## Related notes

- [[Custom LLM Experiment]] - The Custom LLM Training Results compare experiments based on temperature settings, which is a specific aspect of a custom LLM experiment.
- [[Custom LLM Evaluation]] - The comparison of results across different temperature settings is a form of evaluation for the custom LLM experiment.
