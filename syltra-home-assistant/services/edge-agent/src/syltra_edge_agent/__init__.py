"""SYLTRA Edge Agent (spec §14.1).

Bridges the Home Assistant integration runtime to the SYLTRA platform:
authenticates over WebSocket, maps entities to normalized capabilities,
publishes raw and normalized events to JetStream, detects duplicates and
out-of-order delivery, reconnects with bounded backoff, and never lets the
Home Assistant token reach logs or events.
"""
