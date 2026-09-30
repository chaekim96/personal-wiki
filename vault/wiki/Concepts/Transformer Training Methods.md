---
title: Transformer Training Methods
folder: Concepts
source_ids: [src_f00a37228f]
original_files: ["Wikipedia - Transformer architecture.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Transformer Training Methods

## Summary

Transformer training methods cover techniques for stabilizing training, regularization, pretraining and fine-tuning, knowledge distillation, and various language modeling tasks. These methods address issues like convergence, overfitting, and task-specific adaptation.

## Details

- The original paper recommended using learning rate warmup, where the learning rate linearly scales up from 0 to a maximal value for the first part of training before decaying. *(Transformer (deep learning), Methods for stabilizing training)*
- Using layer normalization before multihead attention and feedforward layers stabilizes training, which is the 'pre-LN Transformer' and is more commonly used compared to the original 'post-LN Transformer'. *(Transformer (deep learning), Methods for stabilizing training)*
- Dropout was applied to the output of each sublayer before its residual connection and normalization, as well as to the sums of token embeddings and positional encodings during the original transformer training to reduce overfitting. *(Transformer (deep learning), Regularization)*
- The original paper also used label smoothing, which replaces a certain target distribution with one that assigns a small amount of probability to alternative tokens to improve generalization. *(Transformer (deep learning), Regularization)*
- Transformers are typically first pretrained by self-supervised learning on a large generic dataset, followed by supervised fine-tuning on a small task-specific dataset. *(Transformer (deep learning), Pretrain-finetune)*
- Tasks for pretraining and fine-tuning commonly include language modeling, next-sentence prediction, question answering, reading comprehension, sentiment analysis, and paraphrasing. *(Transformer (deep learning), Pretrain-finetune)*
- Knowledge distillation is a method for training a smaller model, called a 'student', to reproduce the output behavior of a larger 'teacher' model using the teacher's output probability distribution, intermediate representations, or attention patterns. *(Transformer (deep learning), Knowledge distillation)*
- Language modeling tasks are categorized into 'masked', 'autoregressive', and 'prefixLM' classes. *(Transformer (deep learning), Tasks)*
- In a masked task, one or more tokens are masked out, and the model predicts a probability distribution for the masked-out tokens based on the context. *(Transformer (deep learning), Tasks)*
- In an autoregressive task, the entire sequence is masked at first, and the model produces a probability distribution for the first token, which is then revealed to predict the second token, and so on. *(Transformer (deep learning), Tasks)*
- In a prefixLM task, the sequence is divided into two parts, where the first part is presented as context, and the model predicts the first token of the second part, which is then revealed to predict the second token, and so on. *(Transformer (deep learning), Tasks)*

## Sources

- [[Wikipedia - Transformer architecture|Transformer (deep learning)]] · [Wikipedia permalink](https://en.wikipedia.org/w/index.php?oldid=1377565152) · CC BY-SA 4.0
  - Training > Methods for stabilizing training (lines 52-53)
  - Training > Regularization (lines 57-57)
  - Training > Pretrain-finetune (lines 61-74)
  - Training > Knowledge distillation (lines 79-79)
  - Training > Tasks (lines 84-85)

## Related notes

- [[Transformer Architecture]] - The Transformer Architecture defines the primary components of the model, which are central to the training methods discussed in the main note.
- [[Transformer Efficient Implementations]] - Efficient implementations of the Transformer model focus on techniques to improve performance during training, which is a key aspect of Transformer training methods.
- [[Custom LLM Experiment]] - Both use learning-rate warmup: my A3 run warmed the rate up over the first 100 steps, and this note describes warmup from the original transformer paper.
