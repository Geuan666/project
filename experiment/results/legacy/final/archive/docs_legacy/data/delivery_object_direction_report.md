# Delivery Object Direction Intervention

## Shared Direction Alignment

- `L2H14`: write-vs-develop cosine `0.972`, global-dir norm `1.000`.
- `MLP11`: write-vs-develop cosine `0.907`, global-dir norm `1.000`.
- `MLP16`: write-vs-develop cosine `0.871`, global-dir norm `1.000`.
- `MLP19`: write-vs-develop cosine `0.869`, global-dir norm `1.000`.
- `L20H5`: write-vs-develop cosine `0.844`, global-dir norm `1.000`.
- `L21H1`: write-vs-develop cosine `0.859`, global-dir norm `1.000`.
- `L21H12`: write-vs-develop cosine `0.868`, global-dir norm `1.000`.
- `L24H6`: write-vs-develop cosine `0.989`, global-dir norm `1.000`.
- `MLP27`: write-vs-develop cosine `0.743`, global-dir norm `1.000`.

## Direction-Level Intervention

- frame `develop` / node `L2H14` / mode `erase_file_component`: object-delta `-0.001`, boundary `0.999`, tool-logit `0.000`, distractor-logit `0.000`, MLP16 `-0.263`, MLP19 `-0.398`, L20H5 `0.051`, L21H12 `-0.075`, L24H6 `-0.321`, MLP27 `-1.255`.
- frame `develop` / node `L2H14` / mode `inject_file_into_answer`: object-delta `0.001`, boundary `0.117`, tool-logit `0.000`, distractor-logit `0.000`, MLP16 `0.468`, MLP19 `0.898`, L20H5 `-0.162`, L21H12 `0.088`, L24H6 `0.015`, MLP27 `0.714`.
- frame `develop` / node `MLP11` / mode `erase_file_component`: object-delta `-0.065`, boundary `0.941`, tool-logit `-0.250`, distractor-logit `0.375`, MLP16 `-3.779`, MLP19 `-9.843`, L20H5 `-0.294`, L21H12 `-1.351`, L24H6 `-6.593`, MLP27 `-25.380`.
- frame `develop` / node `MLP11` / mode `inject_file_into_answer`: object-delta `0.126`, boundary `0.540`, tool-logit `1.312`, distractor-logit `-1.250`, MLP16 `8.895`, MLP19 `19.839`, L20H5 `0.384`, L21H12 `4.755`, L24H6 `25.573`, MLP27 `56.222`.
- frame `write` / node `L2H14` / mode `erase_file_component`: object-delta `0.000`, boundary `0.995`, tool-logit `0.000`, distractor-logit `0.000`, MLP16 `-0.191`, MLP19 `-0.305`, L20H5 `0.066`, L21H12 `0.005`, L24H6 `-0.089`, MLP27 `0.141`.
- frame `write` / node `L2H14` / mode `inject_file_into_answer`: object-delta `0.002`, boundary `0.122`, tool-logit `0.000`, distractor-logit `0.000`, MLP16 `0.259`, MLP19 `0.566`, L20H5 `-0.214`, L21H12 `0.081`, L24H6 `0.168`, MLP27 `1.443`.
- frame `write` / node `MLP11` / mode `erase_file_component`: object-delta `-0.189`, boundary `0.911`, tool-logit `-0.500`, distractor-logit `0.375`, MLP16 `-4.431`, MLP19 `-10.651`, L20H5 `-0.240`, L21H12 `-1.841`, L24H6 `-4.699`, MLP27 `-26.738`.
- frame `write` / node `MLP11` / mode `inject_file_into_answer`: object-delta `0.678`, boundary `0.635`, tool-logit `1.375`, distractor-logit `-1.625`, MLP16 `9.257`, MLP19 `20.265`, L20H5 `1.802`, L21H12 `8.264`, L24H6 `27.378`, MLP27 `94.680`.

## Bottom Line

If `MLP11` carries a cross-frame file-vs-answer direction and editing only that direction moves `MLP16 -> MLP19 -> late tool route`, while `L2H14` does not, then `MLP11` is the first stable delivery-object writer and `L2H14` is not.
