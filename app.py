import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from modmerge.core import (
    build_java_bundle, conversion_advice, inspect_mod, merge_bedrock_packs
)


class ModMergeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ModMerge Studio")
        self.geometry("920x650")
        self.minsize(760, 540)
        self.java_files = []
        self.bedrock_files = []
        self._build()

    def _build(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="ModMerge Studio", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(root, text="Phân tích • Đóng gói Java • Gộp Bedrock • Kiểm tra khả năng chuyển đổi",
                  foreground="#666").pack(anchor="w", pady=(0, 12))
        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True)
        self.java_tab = ttk.Frame(tabs, padding=12)
        self.bedrock_tab = ttk.Frame(tabs, padding=12)
        self.convert_tab = ttk.Frame(tabs, padding=12)
        tabs.add(self.java_tab, text="Java mod bundle")
        tabs.add(self.bedrock_tab, text="Bedrock pack merge")
        tabs.add(self.convert_tab, text="Conversion checker")
        self._build_java()
        self._build_bedrock()
        self._build_convert()
        self.log = tk.Text(root, height=8, wrap="word", state="disabled")
        self.log.pack(fill="x", pady=(12, 0))
        self._write("Chào mừng! Chọn một tab để bắt đầu. Hãy sao lưu pack trước khi gộp.")

    def _write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _build_java(self):
        f = self.java_tab
        ttk.Label(f, text="Chọn nhiều file .jar thuộc cùng loader Minecraft.").pack(anchor="w")
        row = ttk.Frame(f); row.pack(fill="x", pady=8)
        ttk.Button(row, text="Thêm mod .jar", command=self._add_java).pack(side="left")
        ttk.Button(row, text="Xóa danh sách", command=lambda: self._clear("java")).pack(side="left", padx=6)
        self.java_list = tk.Listbox(f, height=12, selectmode="extended")
        self.java_list.pack(fill="both", expand=True)
        bottom = ttk.Frame(f); bottom.pack(fill="x", pady=10)
        ttk.Label(bottom, text="Loader đích:").pack(side="left")
        self.loader = tk.StringVar(value="Fabric")
        ttk.Combobox(bottom, textvariable=self.loader,
                     values=["Fabric", "Forge", "NeoForge", "Quilt", "Legacy Forge"],
                     state="readonly", width=18).pack(side="left", padx=6)
        ttk.Button(bottom, text="Đóng gói thành ZIP", command=self._build_java_bundle).pack(side="right")

    def _build_bedrock(self):
        f = self.bedrock_tab
        ttk.Label(f, text="Gộp các .mcpack cùng loại (Behavior hoặc Resource).").pack(anchor="w")
        row = ttk.Frame(f); row.pack(fill="x", pady=8)
        ttk.Button(row, text="Thêm pack", command=self._add_bedrock).pack(side="left")
        ttk.Button(row, text="Xóa danh sách", command=lambda: self._clear("bedrock")).pack(side="left", padx=6)
        self.bedrock_list = tk.Listbox(f, height=14, selectmode="extended")
        self.bedrock_list.pack(fill="both", expand=True)
        ttk.Button(f, text="Gộp thành .mcpack", command=self._merge_bedrock).pack(anchor="e", pady=10)

    def _build_convert(self):
        f = self.convert_tab
        ttk.Label(f, text="Chọn một mod/pack để xem khả năng chuyển đổi.").pack(anchor="w")
        row = ttk.Frame(f); row.pack(fill="x", pady=10)
        ttk.Button(row, text="Chọn file", command=self._check_conversion).pack(side="left")
        self.target = tk.StringVar(value="Bedrock")
        ttk.Label(row, text="Nền tảng đích:").pack(side="left", padx=(18, 4))
        ttk.Combobox(row, textvariable=self.target, values=["Bedrock", "Java", "Forge", "Fabric", "NeoForge", "Quilt"],
                     state="readonly", width=16).pack(side="left")
        self.conversion_text = tk.Text(f, height=16, wrap="word")
        self.conversion_text.pack(fill="both", expand=True)

    def _add_java(self):
        files = filedialog.askopenfilenames(filetypes=[("Java mods", "*.jar"), ("All files", "*.*")])
        for p in files:
            if p not in self.java_files:
                self.java_files.append(p); self.java_list.insert("end", p)
                info = inspect_mod(p)
                self._write(f"{Path(p).name}: {info.kind} | {', '.join(info.loaders) or 'unknown'}")

    def _add_bedrock(self):
        files = filedialog.askopenfilenames(filetypes=[("Bedrock packs", "*.mcpack *.zip"), ("All files", "*.*")])
        for p in files:
            if p not in self.bedrock_files:
                self.bedrock_files.append(p); self.bedrock_list.insert("end", p)

    def _clear(self, which):
        if which == "java":
            self.java_files.clear(); self.java_list.delete(0, "end")
        else:
            self.bedrock_files.clear(); self.bedrock_list.delete(0, "end")

    def _build_java_bundle(self):
        if not self.java_files:
            messagebox.showwarning("Thiếu file", "Hãy thêm ít nhất một mod .jar."); return
        out = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP bundle", "*.zip")])
        if not out: return
        try:
            report = build_java_bundle(self.java_files, out, self.loader.get())
            self._write(f"Đã tạo bundle: {out}")
            messagebox.showinfo("Hoàn tất", f"Đã đóng gói {len(report['mods'])} mod.\nĐây là ZIP chứa các JAR riêng, không phải một JAR đã hợp nhất.")
        except Exception as exc:
            messagebox.showerror("Không thể đóng gói", str(exc)); self._write(f"Lỗi: {exc}")

    def _merge_bedrock(self):
        if len(self.bedrock_files) < 2:
            messagebox.showwarning("Thiếu pack", "Hãy chọn ít nhất 2 pack."); return
        out = filedialog.asksaveasfilename(defaultextension=".mcpack", filetypes=[("Minecraft Pack", "*.mcpack")])
        if not out: return
        try:
            result = merge_bedrock_packs(self.bedrock_files, out)
            self._write(json.dumps(result, ensure_ascii=False))
            messagebox.showinfo("Hoàn tất", f"Đã tạo pack: {out}\nHãy thử trong world mới trước khi sử dụng chính thức.")
        except Exception as exc:
            messagebox.showerror("Không thể gộp", str(exc)); self._write(f"Lỗi: {exc}")

    def _check_conversion(self):
        path = filedialog.askopenfilename(filetypes=[("Mod/Pack", "*.jar *.mcpack *.zip"), ("All files", "*.*")])
        if not path: return
        info = inspect_mod(path)
        advice = conversion_advice(path, self.target.get())
        self.conversion_text.delete("1.0", "end")
        self.conversion_text.insert("end", f"File: {info.filename}\nLoại: {info.kind}\nLoader: {', '.join(info.loaders)}\n\n")
        self.conversion_text.insert("end", "\n".join("• " + item for item in advice))
        self._write(f"Đã phân tích chuyển đổi: {path}")


if __name__ == "__main__":
    ModMergeApp().mainloop()
