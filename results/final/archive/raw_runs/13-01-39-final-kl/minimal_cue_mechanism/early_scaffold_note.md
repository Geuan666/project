# Legacy Early Scaffold Note

This note records an older targeted post-check on a `200`-sample subset that
predated the full `1722`-sample rerun now stored in
`minimal_cue_mechanism/`.

Read it only as a historical exploratory note. The authoritative full-result
artifacts are now:

- `minimal_cue_mechanism_report.md`
- `minimal_cue_mechanism_summary.json`
- the `minimal_cue_*_per_sample.csv` / `minimal_cue_*_summary.csv` tables

Goal: connect the earliest cue-sensitive nodes from the 24-node scan to the
late decision chains.

## Early Edge Mediation

- Tool-side scaffold:
  - `MLP11 -> MLP16`: source `0.366`, blocked `0.085`, mediated `0.237`
  - `MLP16 -> L20H5`: source `0.553`, blocked `0.486`, mediated `0.047`
- No-tool-side scaffold:
  - `MLP16 -> MLP17`: source `0.429`, blocked `0.226`, mediated `0.224`
  - `MLP11 -> MLP12`: source `0.156`, blocked `0.046`, mediated `0.079`
  - `MLP12 -> L16H4`: source `0.214`, blocked `0.202`, mediated `0.000`
  - `MLP11 -> L16H4`: source `0.156`, blocked `0.175`, mediated `0.000`

## Interpretation

- The earliest cue-sensitive state is already visible around `MLP11`.
- On the tool side, the clearest early bridge is `MLP11 -> MLP16`, after which
  the signal reaches the late decision chain through `L20H5`.
- On the no-tool side, the strongest early bridge is not `MLP12 -> L16H4`;
  instead, the cleaner route on this minimal-cue check is `MLP16 -> MLP17`.
- So the best current picture is:
  - early shared cue-sensitive scaffold: `MLP11 -> MLP16`
  - tool late route: `... -> L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`
  - no-tool late route: `... -> MLP17 -> L23H6`, with `L16H4` acting as the
    minimal suppress-chain reader inside the late no-tool branch

## Scope

- These numbers come from a targeted historical post-check, not from the
  full `1722`-sample rerun.
- Use the main `minimal_cue_mechanism_report.md` and summary tables for the
  current authoritative result.
