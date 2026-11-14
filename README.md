# ModMerge Studio

A Windows-friendly desktop utility for inspecting Minecraft mod archives, bundling Java mods, merging compatible Bedrock packs, and explaining conversion limits.

## Current MVP

- Detects common Java loader metadata: Fabric, Forge, NeoForge, Quilt, and legacy Forge.
- Builds a Java **mod bundle ZIP** containing the original JARs under `mods/`. It does not pretend to merge bytecode into one installable JAR.
- Merges Bedrock resource packs with other resource packs, or behavior packs with other behavior packs.
- Stops on conflicting file paths instead of silently overwriting user content.
- Generates new Bedrock header/module UUIDs.
- Provides an honest conversion checker for Java ↔ Bedrock and Java loader changes.

## Important compatibility note

A Forge/Fabric/NeoForge/Quilt JAR is executable Java code that depends on loader-specific APIs. A Bedrock `.mcpack` uses a different manifest, content model, and Script API. Renaming or repacking a file cannot port its gameplay logic. Real Java ↔ Bedrock conversion requires a mod-specific rewrite. Similarly, changing Forge to Fabric generally requires source-level porting.

Bedrock merge is best-effort: identical file collisions are deduplicated, differing collisions stop the operation. The MVP does not rewrite identifiers referenced inside JSON, merge arbitrary scripts, or resolve third-party dependencies. Test output in a disposable world and keep backups.

## Run from source

Requires Python 3.10+ (Tkinter is included with most Windows Python installers).

```powershell
py -m venv .venv
.\.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Run tests:

```powershell
py -m unittest discover -s tests -v
```

## Roadmap

- Inspect mod dependencies and Minecraft version constraints.
- Add explicit conflict resolution UI for Bedrock files.
- Add Java resource-pack conversion helpers (textures, block/item models, language files) with a compatibility report.
- Add optional packaging adapters for Modrinth/CurseForge/Prism Launcher.
- Build signed Windows releases.

## License

MIT
