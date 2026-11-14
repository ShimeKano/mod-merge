from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

JAVA_SUFFIXES = {".jar"}
BEDROCK_SUFFIXES = {".mcpack", ".mcaddon", ".zip"}


@dataclass
class ModInfo:
    path: str
    filename: str
    kind: str
    loaders: list[str]
    minecraft_versions: list[str]
    mod_id: str | None
    name: str | None
    warnings: list[str]


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any] | None:
    try:
        value = json.loads(zf.read(name).decode("utf-8-sig"))
        return value if isinstance(value, dict) else None
    except (KeyError, ValueError, UnicodeDecodeError):
        return None


def inspect_mod(path: str | Path) -> ModInfo:
    file = Path(path)
    warnings: list[str] = []
    loaders: list[str] = []
    versions: list[str] = []
    mod_id = name = None
    kind = "unknown"
    try:
        with zipfile.ZipFile(file) as zf:
            names = set(zf.namelist())
            if "fabric.mod.json" in names:
                meta = _read_json(zf, "fabric.mod.json") or {}
                loaders.append("Fabric")
                kind = "Java mod"
                mod_id = meta.get("id")
                name = meta.get("name")
                depends = meta.get("depends", {})
                if isinstance(depends, dict) and isinstance(depends.get("minecraft"), str):
                    versions.append(depends["minecraft"])
            if "quilt.mod.json" in names:
                meta = _read_json(zf, "quilt.mod.json") or {}
                loaders.append("Quilt")
                kind = "Java mod"
                qmeta = meta.get("quilt_loader", {})
                if isinstance(qmeta, dict):
                    mod_id = mod_id or qmeta.get("id")
                    name = name or qmeta.get("metadata", {}).get("name")
            if "META-INF/mods.toml" in names:
                loaders.append("Forge")
                kind = "Java mod"
            if "META-INF/neoforge.mods.toml" in names:
                loaders.append("NeoForge")
                kind = "Java mod"
            if "mcmod.info" in names:
                loaders.append("Legacy Forge")
                kind = "Java mod"
                try:
                    legacy = json.loads(zf.read("mcmod.info").decode("utf-8"))
                    if isinstance(legacy, list) and legacy:
                        mod_id = mod_id or legacy[0].get("modid")
                        name = name or legacy[0].get("name")
                except (ValueError, UnicodeDecodeError):
                    warnings.append("Không đọc được mcmod.info.")
            if not loaders:
                if any(n.startswith("assets/") for n in names) and "pack.mcmeta" in names:
                    kind = "Java resource pack"
                    loaders.append("Java")
                elif "manifest.json" in names:
                    kind = "Bedrock pack"
                    loaders.append("Bedrock")
                else:
                    warnings.append("Không nhận diện được metadata mod phổ biến.")
            if len(loaders) > 1:
                warnings.append("Có nhiều metadata loader; cần kiểm tra thủ công.")
    except (zipfile.BadZipFile, OSError) as exc:
        warnings.append(f"Không mở được archive: {exc}")
    return ModInfo(str(file), file.name, kind, loaders, versions, mod_id, name, warnings)


def inspect_bedrock_pack(path: str | Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        manifest = _read_json(zf, "manifest.json")
        if not manifest:
            raise ValueError(f"{Path(path).name}: thiếu manifest.json hợp lệ.")
        modules = manifest.get("modules", [])
        types = {m.get("type") for m in modules if isinstance(m, dict)}
        if "resources" in types and "data" in types:
            pack_type = "mixed"
        elif "resources" in types:
            pack_type = "resource"
        elif "data" in types or "script" in types:
            pack_type = "behavior"
        else:
            pack_type = "unknown"
        return {"manifest": manifest, "type": pack_type}


def build_java_bundle(paths: list[str], output: str, target_loader: str) -> dict[str, Any]:
    if not paths:
        raise ValueError("Chưa chọn mod nào.")
    infos = [inspect_mod(p) for p in paths]
    bad = [i.filename for i in infos if i.kind != "Java mod"]
    if bad:
        raise ValueError("Chỉ nhận Java mod .jar. Không hợp lệ: " + ", ".join(bad))
    mismatched = [
        i.filename for i in infos
        if i.loaders and target_loader not in i.loaders and not (
            target_loader == "Forge" and "Legacy Forge" in i.loaders
        )
    ]
    if mismatched:
        raise ValueError(
            "Không thể đóng gói an toàn cho " + target_loader + " vì khác loader: "
            + ", ".join(mismatched)
            + ". Hãy chọn đúng loader hoặc dùng các mod tương thích."
        )
    report = {
        "tool": "ModMerge Studio",
        "format": "Java mod bundle (not a merged JAR)",
        "target_loader": target_loader,
        "mods": [asdict(i) for i in infos],
        "note": "Giữ nguyên từng JAR trong thư mục mods/. Không hợp nhất bytecode của các mod.",
    }
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as out:
        for p in paths:
            out.write(p, f"mods/{Path(p).name}")
        out.writestr("modmerge-report.json", json.dumps(report, ensure_ascii=False, indent=2))
        out.writestr("README.txt",
            "ModMerge Studio bundle.\n"
            "Giải nén nội dung vào profile Minecraft dùng đúng loader/phiên bản.\n"
            "Các file JAR vẫn là mod riêng; chúng không bị ghép bytecode thành một JAR.\n")
    return report


def _safe_name(name: str) -> str:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"Đường dẫn không an toàn trong pack: {name}")
    return str(p)


def merge_bedrock_packs(paths: list[str], output: str) -> dict[str, Any]:
    if len(paths) < 2:
        raise ValueError("Cần ít nhất 2 pack Bedrock để gộp.")
    inspected = [(p, inspect_bedrock_pack(p)) for p in paths]
    types = {item["type"] for _, item in inspected}
    if len(types) != 1 or "unknown" in types or "mixed" in types:
        raise ValueError("Chỉ gộp các pack cùng loại (Behavior hoặc Resource). Không trộn hai loại.")
    pack_type = next(iter(types))
    merged_files: dict[str, bytes] = {}
    sources: dict[str, str] = {}
    manifests = []
    for path, info in inspected:
        manifests.append(info["manifest"])
        with zipfile.ZipFile(path) as zf:
            for raw_name in zf.namelist():
                name = _safe_name(raw_name)
                if name.endswith("/") or name == "manifest.json":
                    continue
                data = zf.read(raw_name)
                if name in merged_files:
                    if merged_files[name] != data:
                        raise ValueError(
                            f"Xung đột file '{name}' giữa {sources[name]} và {Path(path).name}. "
                            "Không tự ghi đè để tránh làm hỏng pack."
                        )
                    continue
                merged_files[name] = data
                sources[name] = Path(path).name

    base = dict(manifests[0])
    base_header = dict(base.get("header", {}))
    base_header["uuid"] = str(uuid.uuid4())
    base_header["name"] = "Merged " + str(base_header.get("name", "Bedrock Pack"))
    base["header"] = base_header
    merged_modules = []
    for manifest in manifests:
        for module in manifest.get("modules", []):
            if not isinstance(module, dict):
                continue
            module = dict(module)
            module["uuid"] = str(uuid.uuid4())
            merged_modules.append(module)
    base["modules"] = merged_modules
    base["dependencies"] = []
    base["format_version"] = max(m.get("format_version", 2) for m in manifests)
    merged_files["manifest.json"] = json.dumps(base, ensure_ascii=False, indent=2).encode("utf-8")

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in merged_files.items():
            out.writestr(name, data)
    return {
        "format": "Bedrock merged pack",
        "type": pack_type,
        "input_count": len(paths),
        "file_count": len(merged_files),
        "output": output,
        "warnings": [
            "UUID header/module đã được tạo mới.",
            "Dependencies bên ngoài của các pack chưa được tự động hợp nhất; hãy kiểm tra manifest và thử trong world mới.",
            "Script API, identifier trùng nhau và xung đột nội dung vẫn cần kiểm thử trong game.",
        ],
    }


def conversion_advice(path: str | Path, target: str) -> list[str]:
    info = inspect_mod(path)
    if info.kind == "Java mod" and target == "Bedrock":
        return [
            "Không thể chuyển Java mod thành Bedrock add-on chỉ bằng đổi đuôi file.",
            "Cần port logic Java (Forge/Fabric/NeoForge/Quilt) sang Bedrock Script API hoặc behavior components.",
            "Có thể trích xuất và chuyển một phần texture/model/blockstate, nhưng cần ánh xạ thủ công.",
        ]
    if info.kind == "Bedrock pack" and target == "Java":
        return [
            "Không thể chuyển Bedrock add-on thành Java mod tự động.",
            "Resource có thể cần đổi định dạng/đường dẫn; behavior và script phải viết lại bằng Java mod API.",
        ]
    if info.kind == "Java mod":
        return [
            "Đổi loader (Forge/Fabric/NeoForge/Quilt) không phải chuyển đổi định dạng archive.",
            "Cần source code và port API; tool chỉ có thể kiểm tra metadata và đóng gói mod tương thích.",
        ]
    return ["Định dạng này chưa có quy trình chuyển đổi tự động an toàn."]
