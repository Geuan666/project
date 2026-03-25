# Instruction Lead-Phrase Audit

- `clean_full`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `clean_with_corrupt_lead`: decision `-4.594`, tool-top1 `0.000`, no-tool-top1 `0.998`.
- `corrupt_with_clean_lead`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `corrupt_full`: decision `-4.594`, tool-top1 `0.000`, no-tool-top1 `0.998`.
- Query chain on `clean_with_corrupt_lead`: `L20H5|L21H1|L21H12|L24H6|MLP27` -> rescue `0.991`, tool-top1 `0.939`.
