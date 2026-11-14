# ModMerge Studio

Static browser-based Minecraft mod utility. No backend: selected files are processed locally in the browser.

## Pages
- `index.html`: main app.
- `diagnostics.html`: independent recovery page. Checks browser APIs, published files and both JSZip CDN endpoints; can copy a diagnostic report.
- `404.html`: fallback page with links to the app and diagnostics.

## GitHub Pages setup
Repository → Settings → Pages → Build and deployment:
- Source: Deploy from a branch
- Branch: `main`
- Folder: `/(root)`

Ensure `index.html`, `styles.css`, `app.js`, `diagnostics.html`, and `.nojekyll` are in the selected publishing root. Wait for the Pages deployment to complete in Actions. Project site URL: `https://shimekano.github.io/mod-merge/`.

## Troubleshooting
Open `https://shimekano.github.io/mod-merge/diagnostics.html` if the main app is blank or broken. The diagnostics page is standalone and does not depend on the app stylesheet or JSZip.

## Features
- Java: inspect common loader metadata and package compatible JARs into one ZIP under `mods/`.
- Bedrock: best-effort merge of same-type resource or behavior packs.
- Compatibility notes for Java ↔ Bedrock and Forge ↔ Fabric conversions.

## Limitations
- Java JARs remain separate files; bytecode is not merged into one installable JAR.
- Java ↔ Bedrock gameplay conversion requires rewriting mod logic for different APIs.
- Forge/Fabric/NeoForge/Quilt porting is source/API-level work, not archive conversion.
- Bedrock merging does not resolve all script references, identifiers, JSON links or external dependencies. Back up and test in a disposable world.
- JSZip is fetched from jsDelivr with cdnjs fallback; internet access is required for ZIP operations.
