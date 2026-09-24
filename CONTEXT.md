# Jev Decision Context

Domain terminology for evaluating application state using the Jev decision model.

## Language

**State**:
The subject data (raw text or structured key-value payload) presented for evaluation.
_Avoid_: Prompt, context window, input document

**Question**:
A typed, non-generative inquiry posed against a State.
_Avoid_: Query, instruction, prompt

**Noul**:
A binary decision primitive that evaluates a hypothesis against the State and returns the probability of truth.
_Avoid_: Boolean check, binary classification, yes-no prompt

**Choice**:
A categorical decision primitive that classifies State into one of several defined mutually exclusive candidates with criteria.
_Avoid_: Multi-choice prompt, tagger, classifier

**Score**:
An ordinal decision primitive that places State on an ordered scale of descriptive levels, returning a calibrated numeric rating.
_Avoid_: Rating prompt, sentiment score, scalar regression

**Decision**:
The structured collection of probabilistic answers produced for all Questions in a single parallel evaluation pass.
_Avoid_: Completion, generation, response text
