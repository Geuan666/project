# Reverse / No-Tool Overlap

## Main takeaway

- The minimal no-tool decision chain `L16H4 -> MLP17 -> L23H6` is fully contained in the reverse core.
- If we expand the no-tool semantic line to the reverse-aligned suppressive branch `{MLP12, L15H5, L16H13, L16H4, L16H8, L16H9, MLP17, L17H2, L23H6}`, it matches all 8 reverse-selective nodes plus one extra shared late node `L23H6`.
- On edges, that reverse-aligned no-tool semantic line covers 14/15 reverse-selective edges; the missing edge is a late `MLP17 -> Residual Output: decision` shortcut, while `L23H6 -> Residual Output: decision` is the extra shared late-output edge.

## Node overlap

### minimal_no_tool

- reverse-core recall: `1.0000`
- reverse-selective recall: `0.6667`
- reverse-selective precision: `0.2500`
- reverse-selective jaccard: `0.2222`
- overlap with reverse-selective: `L16H4, MLP17`

### semantic_no_tool

- reverse-core recall: `0.3750`
- reverse-selective recall: `0.7500`
- reverse-selective precision: `0.7500`
- reverse-selective jaccard: `0.6000`
- overlap with reverse-selective: `L15H5, L16H13, L16H4, L16H9, MLP12, MLP17`

### reverse_aligned_no_tool

- reverse-core recall: `0.4444`
- reverse-selective recall: `0.8889`
- reverse-selective precision: `1.0000`
- reverse-selective jaccard: `0.8889`
- overlap with reverse-selective: `L15H5, L16H13, L16H4, L16H8, L16H9, L17H2, MLP12, MLP17`

## Edge overlap

### minimal_no_tool

- reverse-core recall: `0.6667`
- reverse-selective recall: `0.3333`
- reverse-selective precision: `0.0667`
- reverse-selective jaccard: `0.0588`

### semantic_no_tool

- reverse-core recall: `0.1875`
- reverse-selective recall: `0.8750`
- reverse-selective precision: `0.9333`
- reverse-selective jaccard: `0.8235`

### reverse_aligned_no_tool

- reverse-core recall: `0.1875`
- reverse-selective recall: `0.8750`
- reverse-selective precision: `0.9333`
- reverse-selective jaccard: `0.8235`

