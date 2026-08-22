# Model evaluation

Spec §8 places evaluation code here. This directory is empty on purpose.

Evaluation runs as part of training and its results are recorded on the model card in `services/adaptive-engine/src/syltra_adaptive_engine/registry.py`. A worked example of a card is in `contracts/examples/`.

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
