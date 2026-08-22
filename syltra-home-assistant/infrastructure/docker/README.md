# Container definitions

Spec §8 places Dockerfiles here. This directory is empty on purpose.

Each service owns its own `Dockerfile` beside its code, so a service is buildable from its own directory and a move does not break a path in a shared tree.

An empty directory makes a claim of its own — `models/exported/` reads as
"models are exported, and this is where they land", and both halves of that
would be wrong. This file is here so the directory stops making it.
