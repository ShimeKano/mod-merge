# ModMerge Studio

Static browser-based Minecraft mod utility. Files are processed locally in the browser.

## Current capabilities
- Java: identifies common loader metadata and creates a modpack ZIP containing separate JAR files. It does not merge Java bytecode into one JAR.
- Bedrock: merges multiple same-kind Resource Packs or Behavior Packs into one .mcpack. It validates v2 manifests, UUIDs, versions, JSON files and archive paths; remaps module UUIDs; preserves external header dependencies; rejects conflicting file contents and conflicting dependency versions.
- Independent diagnostics and recovery page for GitHub Pages.

## Bedrock merger limits
- Supports manifest format_version 2 and module types resources, data and script.
- Packs containing both resource and behavior modules must be separated first.
- Script API references, identifiers, loot tables, recipes, entity references, texture references and other semantic links are not rewritten. Only manifest module UUID dependencies are remapped.
- Differing files at the same path are rejected rather than overwritten.
- External dependencies are retained; dependencies pointing at an input pack header UUID are treated as internal.
- Test output in a disposable world. This is a cautious archive/manifest merge, not a guarantee that arbitrary add-ons are semantically compatible.

## GitHub Pages
The site is static and can be deployed from the repository root or through .github/workflows/pages.yml. Open diagnostics.html if the main page fails.

## Local tests
Run `node --test tests/bedrock-merger.test.js` with Node.js 18+.
