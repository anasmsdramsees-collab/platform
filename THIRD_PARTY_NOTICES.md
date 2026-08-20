# Third-Party Notices

This file records third-party software used by the SYLTRA Adaptive Edge Platform and
the license obligations that come with it. Update it whenever a dependency is added or
removed; CI records dependency licenses on every run (spec §30).

## Boundary commitments

- **Home Assistant Core** is used unmodified, in its own container, as an embedded and
  replaceable device-integration runtime (see ADR-001). SYLTRA integrates only through
  supported APIs and a separate custom integration (`home-assistant/custom_components/
  syltra_edge/`).
- Home Assistant trademarks are not presented as SYLTRA property; the Home Assistant
  frontend is not copied, re-skinned, or rebranded. The HA UI is a development and
  installer diagnostic tool only.
- Dependencies with incompatible or unclear licenses are flagged before adoption.

## Platform runtime components (containers)

| Component | License | Use |
|---|---|---|
| Home Assistant Core | Apache-2.0 | Device integration runtime (unmodified container) |
| Eclipse Mosquitto | EPL-2.0 / EDL-1.0 | MQTT broker |
| NATS Server (JetStream) | Apache-2.0 | Messaging and durable event streams |
| PostgreSQL | PostgreSQL License | Relational storage |
| TimescaleDB | Timescale License (community: Apache-2.0 core) | Time-series storage extension |

Apache-2.0 notice: Home Assistant Core and NATS Server are distributed under the Apache
License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0). Their NOTICE files
ship inside the respective container images, which are used unmodified.

## Python dependencies (workspace)

Exact versions are pinned in `uv.lock`. Principal direct dependencies and licenses:

| Package | License |
|---|---|
| pydantic | MIT |
| ruff | MIT |
| mypy | MIT |
| pytest | MIT |
| pytest-asyncio | Apache-2.0 |
| hypothesis | MPL-2.0 |
| bandit | Apache-2.0 |
| coverage | Apache-2.0 |

Later phases add (and must record here): FastAPI (MIT), SQLAlchemy (MIT), Alembic
(MIT), nats-py (Apache-2.0), asyncpg (Apache-2.0), NumPy (BSD-3-Clause), scikit-learn
(BSD-3-Clause), ONNX (Apache-2.0), ONNX Runtime (MIT), testcontainers (Apache-2.0).

## Website dependencies

The Next.js website under `src/` has its own dependency set in `package.json`
(Next.js — MIT, React — MIT, Tailwind CSS — MIT, and others recorded in
`package-lock.json`).
