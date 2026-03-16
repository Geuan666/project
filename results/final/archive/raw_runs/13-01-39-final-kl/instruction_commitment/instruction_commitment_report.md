# Instruction-Line Commitment Audit

- `clean_full`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `clean_with_corrupt_instruction`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.
- `corrupt_with_clean_instruction`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`.
- `corrupt_full`: decision `-4.562`, tool-top1 `0.000`, no-tool-top1 `0.999`.

- Query chain on `clean_with_corrupt_instruction`: `L20H5|L21H1|L21H12|L24H6|MLP27` -> rescue `0.991`, tool-top1 `0.937`.
- No-tool chain on `corrupt_with_clean_instruction`: `L16H4|MLP17|L23H6` -> rescue `0.795`, no-tool-top1 `0.516`.

Interpretation:
- If swapping only the first instruction line moves the decision strongly, the dataset's key user-side variable is not the problem body but the instruction-level commitment cue.
- If the fixed-schema query chain rescues `clean_with_corrupt_instruction`, then that chain carries the missing commitment signal from the instruction line into the late writer.
