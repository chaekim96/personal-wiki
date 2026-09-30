---
title: Transformer Architecture
folder: Concepts
source_ids: [src_f00a37228f]
original_files: ["Wikipedia - Transformer architecture.md"]
generated_by: gemma4:e2b-it-qat (local)
updated: 2026-09-29
reviewed: 2026-09-29 (checked against raw; hand-edited)
---

# Transformer Architecture

## Summary

The Transformer Architecture has primary components including tokenizers, an embedding layer, transformer layers, and an un-embedding layer. It operates by mapping text to numerical sequences, processing these sequences through layers that alternate between attention and feedforward mechanisms, and then converting the final representation back to a probability distribution over tokens.

## Details

- All transformers have the same primary components: Tokenizers, which convert text into tokens, Embedding layer, which converts tokens and positions of the tokens into vector representations, Transformer layers, which carry out repeated transformations on the vector representations, extracting more and more linguistic information, Un-embedding layer, which converts the final vector representations back to a probability distribution over the tokens. *(Transformer (deep learning), Architecture)*
- The input text is treated by a preprocessor, which performs both textual transformations and splits the text into coarse-grained segments called pretokens. The latter is referred to as pretokenization. *(Transformer (deep learning), Tokenization)*
- Each pretoken is segmented further into tokens by a tokenizer that expects to only see pretokens output by its preprocessor. Each token it produces is a string of one or more characters belonging to a finite set of strings called the vocabulary $V$. *(Transformer (deep learning), Tokenization)*
- Each integer token identifier is converted into an embedding vector via a lookup table. Equivalently stated, it multiplies a one-hot representation of the token identifier by an embedding matrix $M$. *(Transformer (deep learning), Embedding)*
- The token embedding vectors are added to their respective positional encoding vectors (see below), producing the sequence of input vectors. *(Transformer (deep learning), Embedding)*
- The dimension of an embedding vector is called hidden size or embedding size and written as $d_{	ext{emb}}$. This size is written as $d_{	ext{model}}$. *(Transformer (deep learning), Embedding)*
- An un-embedding layer is a linear-softmax layer: $	ext{UnEmbed} (x)=	ext{softmax} (xW+b)$ The matrix has shape $(d_{	ext{emb}},|V|)$. *(Transformer (deep learning), Un-embedding)*
- A positional encoding is a fixed-size vector representation of the relative positions of tokens within a sequence: it provides the transformer model with information about where the words are in the input sequence. *(Transformer (deep learning), Positional encoding)*
- The feedforward network (FFN) modules in a transformer are 2-layered multilayer perceptrons: $	ext{FFN} (x)=\phi (xW^{(1)}+b^{(1)})W^{(2)}+b^{(2)}$ where $W^{(1)}$ $W^{(2)}$ $b^{(1)}$ $b^{(2)}$ $\phi$. *(Transformer (deep learning), Feedforward network)*

## Sources

- [[Wikipedia - Transformer architecture|Transformer (deep learning)]] · [Wikipedia permalink](https://en.wikipedia.org/w/index.php?oldid=1377565152) · CC BY-SA 4.0
  - Architecture (lines 125-132)
  - Architecture > Tokenization (lines 146-147)
  - Architecture > Embedding (lines 234-234)
  - Architecture > Un-embedding (lines 343-345)
  - Architecture > Positional encoding (lines 428-668)
  - Architecture > Encoder–decoder (overview) (lines 833-835)
  - Architecture > Feedforward network (lines 840-840)

## Related notes

- [[Custom LLM Experiment]] - My A3 nanoGPT model is built from pieces this note describes: token embeddings (64 numbers) and blocks with attention heads (2 blocks, 4 heads).
