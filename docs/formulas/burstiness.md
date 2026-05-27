# Burstiness

Burstiness follows Goh and Barabasi's interval-based form.

Formula:

```text
B = (sigma - mu) / (sigma + mu)
```

Where:

- `mu` is the mean interval between switches.
- `sigma` is the standard deviation of switch intervals.

If there are fewer than two intervals, the value is `0`.
