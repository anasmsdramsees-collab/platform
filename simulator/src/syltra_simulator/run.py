"""``make simulate`` entrypoint: run deterministic scenarios end to end.

By default runs entirely in-process (mock Home Assistant + Edge Agent +
in-memory capture) and prints a per-scenario assertion report — no
infrastructure required. With ``--nats`` it publishes into a running
JetStream instead, so ``make demo`` can show real streams.
"""

import argparse
import asyncio
import sys

from syltra_simulator.harness import SimulationRun
from syltra_simulator.scenarios import SCENARIOS, Scenario


async def run_scenario(name: str, scenario: Scenario, use_nats: bool) -> bool:
    publisher = None
    nc = None
    if use_nats:
        import nats

        from syltra_eventing import EventPublisher, ensure_streams

        nc = await nats.connect("nats://localhost:4222")
        js = nc.jetstream()
        await ensure_streams(js)
        publisher = EventPublisher(js, service="simulator")

    run = SimulationRun(publisher=publisher)
    try:
        await run.start()
        before_raw, before_norm, before_dl = run.mark()
        events = await run.run_scenario(scenario)
        normalized = len(events.normalized) - before_norm
        deadletter = len(events.deadletter) - before_dl
        raw = len(events.raw) - before_raw
    finally:
        await run.stop()
        if nc is not None:
            await nc.drain()

    if use_nats:
        print(f"  {name}: published to JetStream (raw={raw})")
        return True

    ok = True
    expects = scenario.expects
    checks: list[str] = []
    if "normalized" in expects:
        passed = normalized >= expects["normalized"]
        ok &= passed
        checks.append(f"normalized={normalized} (expect ≥{expects['normalized']}) {_m(passed)}")
    if "deadletter" in expects:
        passed = deadletter == expects["deadletter"]
        ok &= passed
        checks.append(f"deadletter={deadletter} (expect {expects['deadletter']}) {_m(passed)}")
    print(f"  {name}: {'; '.join(checks)}")
    return bool(ok)


def _m(passed: bool) -> str:
    return "✔" if passed else "✘"


async def main(names: list[str], use_nats: bool) -> int:
    selected = names or list(SCENARIOS)
    unknown = [n for n in selected if n not in SCENARIOS]
    if unknown:
        print(f"unknown scenario(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(SCENARIOS)}", file=sys.stderr)
        return 2

    print(f"SYLTRA simulator — {len(selected)} scenario(s)")
    results = [await run_scenario(name, SCENARIOS[name], use_nats) for name in selected]
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} scenarios passed")
    return 1 if failed else 0


def cli() -> None:
    parser = argparse.ArgumentParser(prog="syltra-simulate", description=__doc__)
    parser.add_argument("scenarios", nargs="*", help="scenario names (default: all)")
    parser.add_argument(
        "--nats", action="store_true", help="publish into a running JetStream instead of memory"
    )
    parser.add_argument("--list", action="store_true", help="list available scenarios")
    args = parser.parse_args()
    if args.list:
        for name, scenario in SCENARIOS.items():
            print(f"{name:24s} {scenario.description}")
        return
    raise SystemExit(asyncio.run(main(args.scenarios, args.nats)))


if __name__ == "__main__":
    cli()
