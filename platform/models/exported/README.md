# Exported models

Spec §8 places exported model artifacts here. This directory is empty on purpose.

Nothing is exported into the repository, and nothing should be: a trained model is one household's behaviour. ONNX export writes to the hub's own model store at runtime (`services/adaptive-engine/src/syltra_adaptive_engine/registry.py`).

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
