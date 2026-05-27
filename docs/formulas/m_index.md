# M-index

The M-index estimates how evenly language tokens are distributed.

Formula:

```text
M = (1 - sum(p_i ** 2)) * (k / (k - 1))
```

Where:

- `p_i` is the proportion of annotated tokens in language `i`.
- `k` is the number of languages present.

If fewer than two languages are present, the value is `0`.
