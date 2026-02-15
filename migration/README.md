# Migration Workspace

This folder tracks artifacts and implementation files for the Urubu to Pelican + PageFind migration.

## Baseline Artifacts

Run this command to refresh baseline captures from the current Urubu build output:

```bash
python3 scripts/capture_baseline.py
```

Generated files are written to `migration/baseline/` and include:

- URL inventory from `_build`.
- Representative URL sample list by section.
- Metadata/front matter usage counts from Markdown source.
- Urubu layout template inventory.
- Tipue Search source/build asset inventory.

## Redirect Mapping

`migration/redirects.csv` is the source-of-truth mapping for legacy URL redirects when URL parity is not possible during migration.
