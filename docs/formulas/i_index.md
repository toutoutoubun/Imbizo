# I-index

The I-index estimates how often language switches occur at possible token
boundaries.

Formula:

```text
I = observed_switch_points / possible_adjacent_annotated_token_boundaries
```

The denominator is the number of annotated tokens minus one. If fewer than two
annotated tokens are present, the value is `0`.
