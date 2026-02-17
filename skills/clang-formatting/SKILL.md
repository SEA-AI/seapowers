---
name: clang-formatting
description: >
  SEA.AI C/C++/CUDA formatting conventions based on clang-format. Use when writing,
  reviewing, or refactoring C, C++, or CUDA code in SEA.AI repositories.
  Triggers on any task involving C/C++/CUDA code.
---

# C/C++/CUDA Formatting

SEA.AI uses **clang-format** for all C, C++, and CUDA source files. The config lives in
`.clang-format` at the repository root.

## Style

- **Base style:** Google
- **Indent:** 4 spaces
- **Column limit:** 120

```yaml
# .clang-format
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 120
```

## Excluded paths

The following vendored directories are excluded from formatting:

- `Core/BoatbusInterface/nmea2000library/include/`
- `Core/BosonSDK/`

Do not reformat code inside these paths.

## Verification

clang-format runs automatically as a pre-commit hook on all `.c`, `.cpp`, `.h`, `.hpp`, and `.cu` files (excluding the paths above).

To format manually:

```bash
clang-format -i <files>
```
