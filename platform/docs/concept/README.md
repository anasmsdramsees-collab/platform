# Where this platform came from

Six documents, rescued from `syltra concept/` before that folder was cleared.
None of them describes what is built today — `IMPLEMENTATION_STATUS.md` does
that — and none of them is a specification. They are kept because a build with
no record of its own reasoning is a build nobody can argue with later.

| Document | What it is | Standing |
|---|---|---|
| `SYLTRA_Adaptive_Concept.md` | The product vision: *manage the environment, not the devices*, and the thirteen-layer loop from state to reconciliation. | **Live.** This is the idea the platform is trying to be. |
| `adaptive-intelligence-layer.md` | The intelligence layer as the owner drew it, with the diagram the services were built from. | **Live**, and largely implemented. |
| `SYLTRA_CloudCodeMax_HomeAssistant_to_Hub_Build_Prompt.md` | An earlier build prompt routing devices through **SYLTRA Cloud**. | **Superseded.** ADR-001 and the master spec put the intelligence on the hub; §0 forbids a cloud dependency for local control. Kept because it is where the decision that mattered most was made, and reversing it later should mean reading this first. |
| `hardware-integration-contract.md` | What a device must expose to be integrated. | Reference. |
| `installer-flow.md` | The commissioning walk-through. | Reference; the installations work is still open (GAPS §2.2). |
| `security-checklist.md` | An early checklist. | Superseded by the safety invariants and `SECURITY.md`. |
| `SYLTRA_PLATFORM_OVERVIEW.md` | The platform explained for a reader who is not going to open the code. | Reference. |
| `SYLTRA_GAPS.md` | The previous generation's gaps register. | Superseded by `docs/GAPS.md`, kept because it shows which of them were closed rather than forgotten. |
| `SYLTRA_GAP_CLOSURE_AND_MULTIPROTOCOL_HUB_DIRECTIVE_v1.md` | An owner directive on closing those gaps and on a multiprotocol hub. | **Partly open.** The multiprotocol half is not built. |
| `SYLTRA_EXTERNAL_REVIEW_BRIEF.md` | The brief written for an outside reviewer. | Reference. |

## The one idea from here that was missing

§08 of the concept sets out a case the build did not handle:

> The air conditioning is on. The room reaches 27° and stops. The goal is not
> met. **The system does not repeat the same command.** It examines the
> difference, finds the window open, the curtains open and 43° outside, and
> changes the plan.

Goals were correcting and re-correcting on a timer with no idea whether the
correction was working. `platform/services/automation-engine/.../reconciliation.py`
is that missing layer.


## And one document that should never have been out here

`SYLTRA_Platform_UI_UX_Guidelines.md` — 1,792 lines — is now
`platform/docs/guidelines/`. It is not history: the console and the wall panel
cite it constantly (`§8` on colour never carrying a state alone, `§13.4` on the
recommendation card, `§24` on generated design tokens), and the design-system
tests enforce it. It was sitting in a folder outside the repository, tracked by
nothing, while the code that obeys it was under version control. A rule nobody
can find is a rule the next person breaks.
