# Switch Density

Switch density counts language switches per `N` annotated tokens.

Formula:

```text
switch_density = switch_count / annotated_token_count * N
```

The MVP uses `N = 100` by default.
