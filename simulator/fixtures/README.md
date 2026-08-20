# Simulator fixtures

Spec §8 places fixtures here. This directory is empty on purpose.

Deterministic household histories are built by `libs/testing/src/syltra_testing/`, so tests and the simulator share one source rather than drifting apart.

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
