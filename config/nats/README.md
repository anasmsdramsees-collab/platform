# NATS configuration

For the Phase 0 skeleton, NATS runs from command-line flags in
`docker-compose.yml` (JetStream enabled, credentials from `.env`).

Phase 1 replaces the flags with a full server config here covering:

- JetStream stream definitions for the `syltra.*` subject hierarchy (spec §12);
- per-stream retention policies (raw high-frequency shorter than derived;
  configurable per privacy class);
- durable consumers and dead-letter streams (`syltra.deadletter.{service}`);
- account/user authorization scoped per service (least privilege, spec §25.1).
