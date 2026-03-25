# Fixed-Schema Query Decision Chain

This report only compares `clean_full` vs `corrupt_full`, which keep the same schema/protocol and change the user-side prompt.

## Query-Side Route

- `L20H5` direct clean->corrupt rescue median `0.305`, top1 `0.006`.
- `L21H1` direct rescue median `0.568`; `L21H12` direct rescue median `0.705`.
- `MLP27` direct rescue median `0.807`, top1 `0.286`.
- Cumulative query route `L20H5|L21H1|L21H12|L24H6|MLP27` reaches decision `1.929` and tool-top1 `0.939` on `corrupt_full`.
- Path mediation: `L20H5->L21H1` `0.053`, `L20H5->L21H12` `0.094`, `L21H12->MLP27` `0.329`.

## Competing No-Tool Route

- `MLP17` direct corrupt->clean no-tool rescue median `0.474`.
- Cumulative suppress route `L16H4|MLP17|L23H6` reaches decision `-0.086` and no-tool top1 `0.517` on `clean_full`.
- `MLP17->L20H5` mediation `0.050`, consistent with the no-tool chain suppressing a user-to-tool ingress point.

## Interpretation

- Under fixed schema/protocol, the user-side difference is not expressed through an early isolated reader. Instead, it enters the late tool path at `L20H5`, is routed through `L21H1/L21H12`, and is then written out by `MLP27`.
- The competing no-tool route can push the same fixed-schema prompt back toward `no_tool` by writing through `MLP17` and suppressing downstream late tool ingress.
