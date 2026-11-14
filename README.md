# ModMerge Studio

Static browser-based Minecraft mod utility. No backend: selected files are processed locally in the browser.

## Features
- Java: inspect common loader metadata and package compatible JAR files into one ZIP under `mods/`.
- Bedrock: merge multiple resource packs or multiple behavior packs of the same type, with basic file-collision detection and regenerated header/module UUIDs.
- Compatibility notes for Java ↔ Bedrock and Forge ↔ Fabric conversions.

## Run
Open `index.html` in a modern browser or serve this directory with a static file server. GitHub Pages can host the project directly.

## Limitations
- Java JARs remain separate files; bytecode is not merged into one installable JAR.
- Java ↔ Bedrock gameplay conversion requires rewriting mod logic for different APIs.
- Forge/Fabric/NeoForge/Quilt porting is source/API-level work, not archive conversion.
- Bedrock merging is best-effort; scripts, JSON identifiers, external dependencies, and cross-pack references are not resolved automatically. Back up and test in a disposable world.
- JSZip loads from jsDelivr CDN, so an internet connection is required to load the library.

## GitHub Pages
Enable Pages for the `main` branch and root directory after merging this branch.
