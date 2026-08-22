# ADR-006: Polars for the feature pipeline

- Status: Accepted
- Date: 2026-08-18
- Deciders: Implementation engineering (Phase 4)

## Context

Spec §7.5 lists "pandas or Polars, **select one and record the decision**". The
feature pipeline turns local event history into training and inference features
on a SYLTRA Hub — a constrained edge device (spec §6.2), not a workstation.

The workload is narrow and known: group events by home, device and capability;
bucket them by weekday and time-of-day; compute exponentially weighted
frequencies and rolling robust statistics. That is almost entirely group-by and
window work over tabular data of modest size.

NumPy is already mandated (§7.5) and scikit-learn depends on it, so the
dataframe library is an *additional* dependency either way.

## Decision

Use **Polars**.

Reasons, in the order they mattered:

1. **Edge memory footprint.** Polars' Arrow-backed columnar layout uses
   materially less memory than pandas' object-heavy representation for the
   string-keyed, mixed-type event data this pipeline handles. On a hub sharing
   RAM with Home Assistant, a database and several services, that is a real
   constraint rather than a micro-optimization.
2. **The operations we actually perform are its strength.** Group-by and window
   aggregations over event history are Polars' fastest path.
3. **Strict schemas fit the requirement.** Spec §22 Phase 4 demands a *versioned
   feature schema*, and Phase 4 acceptance requires validated inference input.
   Polars raises on schema mismatch rather than silently upcasting, so a feature
   drift shows up as an error at the boundary instead of a quietly wrong model
   input.
4. **No index semantics.** pandas' implicit index is a recurring source of
   subtle bugs in pipelines that reshape data repeatedly. Polars has no index,
   so a join or group-by cannot silently realign rows.

## Consequences

- Model *training* uses Polars; model *artifacts* are ONNX (spec §7.5), so the
  dataframe choice never reaches the inference boundary. Swapping it later would
  touch the feature pipeline only, not the models or the serving path.
- scikit-learn consumes NumPy arrays; the pipeline converts explicitly at that
  boundary (`.to_numpy()`), which is also where feature ordering is pinned to
  the schema — an accidental column reorder becomes impossible to miss.
- pandas is *not* added as a dependency. Any future need for it requires
  superseding this ADR rather than quietly importing both.
- Polars ships prebuilt wheels for aarch64 Linux, which the pilot hub target
  needs; this was checked before adopting it.

## Alternatives considered

- **pandas** — the more familiar option and better represented in tutorials, but
  heavier at runtime, with index semantics we would spend effort defending
  against. Its ecosystem advantages (plotting, wide I/O support) are irrelevant
  to a headless edge pipeline.
- **NumPy alone** — tempting, since NumPy is required anyway. Rejected because
  the group-by and time-bucketing logic would be hand-rolled, and hand-rolled
  aggregation is exactly where reproducibility bugs hide. The spec also asks for
  one of the two named libraries.
