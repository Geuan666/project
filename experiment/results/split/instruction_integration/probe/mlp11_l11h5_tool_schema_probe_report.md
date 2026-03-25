# MLP11 Probe Validation

- Probe: logistic regression on `MLP11` last-token output, trained on unmasked train clean/corrupt states.
- Intervention: zero attention weights from `L11H5` to the `tool_schema` span on both clean and corrupt prompts, then evaluate the fixed probe on held-out test states.

- Train baseline accuracy: `1.0000`
- Test baseline accuracy: `1.0000`
- Test masked accuracy: `1.0000`
- Accuracy drop: `0.0000`
- Clean positive-rate drop: `0.0000`
- Corrupt negative-rate drop: `0.0000`
- Interpretation: probe accuracy drop does not exceed 5%; route-score drop remains the primary causal evidence for Module 1.
