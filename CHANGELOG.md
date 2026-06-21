# Changelog

## v1.2.0

- Cleaned generated artifacts from the release package.
- Fixed local pytest discovery for the `src/` layout.
- Unified package and runtime version metadata at `1.2.0`.
- Added CLI `--version` support.
- Added `audit_manifest.json` with version, output inventory, severity counts, and category counts.
- Added support for both list-style and `{ "figures": [...] }` figure manifests.
- Improved fuzzy descriptor column matching for unit-decorated headers such as `BET (m²/g)`, `Specific capacity (mAh/g)`, and `Initial Coulombic Efficiency (%)`.
- Prevented missing numeric values (`NaN`) from being incorrectly flagged as physically impossible values.
- Added stable CSV headers for empty audit outputs.
- Expanded tests from 3 to 6 cases.
