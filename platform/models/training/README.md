# Model training

Spec §8 places training code here. This directory is empty on purpose.

It lives in `services/adaptive-engine/src/syltra_adaptive_engine/`. Training runs in-process on the hub against that household's own data; there is no training pipeline to put in a separate tree.

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
