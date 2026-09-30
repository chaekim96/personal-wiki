# Wiki review (2026-09-29)

Each generated note was compared with the raw passages it cites. Fixes were made in `vault/wiki/` only;
`vault/raw/` is unchanged (sha1 checked before and after). Edited notes carry `reviewed:` in their
frontmatter, and `wiki ingest` keeps them (it skips files whose content changed since it last wrote them).

## Method
A script paired every detail claim with the closest sentence in its cited section and flagged
low-overlap claims and numbers missing from the section. Each flag was then checked by hand in the raw file.

## Findings
- **Detail claims (57):** all supported by the cited section. Flags were false alarms caused by
  README sentences wrapping across lines. Examples checked: pre-LN (Transformer line 53), pretraining
  task list (after line 61), MQA "increases inference speed" (after line 4488), README line 278
  "Only the prefix goes into the model".
- **Problems were all in free-written text** (summaries and related-note reasons), not in details.

## Fixes
| Note | Problem | Fix |
|---|---|---|
| Custom LLM Training Results | README section 4 (samples/loss) missing; mostly a ~700-word random-word block | Added 3 details with line numbers (138, 171, 140-141) |
| Custom LLM Training Results, Custom LLM Evaluation, Transformer Efficient Implementations | Summaries said "This section/document/topic..." | Rewrote summaries to describe the subject |
| Custom LLM Experiment <-> Transformer Training Methods | Unsupported reasons ("necessitates", "fine-tuning") | Replaced with a stated connection: both use learning-rate warmup |
| Custom LLM Experiment <-> Transformer Architecture | "nanoGPT is based on the Transformer" is not stated in my sources | Replaced with: model has token embeddings and blocks with attention heads |
| Training Results -> Transformer Training Methods | Temperature is inference, not training | Removed |
| Evaluation -> Transformer Training Methods | Unsupported | Removed |
| Efficient Implementations -> Custom LLM Experiment | Unsupported | Removed |
| Retrieval-Augmented Generation -> Transformer Architecture | "Transformer allows retrieval" is wrong | Removed; RAG note has no related notes |

## Checks after the fixes
- `wiki ingest "./vault/raw/Custom LLM Assignment README.md" --force`: all edited notes kept, file list unchanged (no duplicates)
- No broken `[[links]]` in the vault
- `vault/raw/` sha1 unchanged
