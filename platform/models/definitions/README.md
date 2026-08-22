# Model definitions

Spec §8 places model definitions here. This directory is empty on purpose.

They live in `services/adaptive-engine/src/syltra_adaptive_engine/models/`, next to the service that trains and serves them, because a Python workspace resolves imports by package rather than by directory layout.

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
