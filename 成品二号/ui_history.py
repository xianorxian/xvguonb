import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import history_manager


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master, on_close_callback=None):
        super().__init__(master)

        self.master = master
        self.on_close_callback = on_close_callback
        self.tree_record_map = {}

        self.title("历史记录管理器")
        self.geometry("760x500")
        self.minsize(700, 420)

        self.create_widgets()
        self.refresh_history()

        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_frame = ctk.CTkFrame(self, corner_radius=12)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 8))
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.search_label = ctk.CTkLabel(
            self.top_frame,
            text="关键词检索：",
            font=("微软雅黑", 14)
        )
        self.search_label.grid(row=0, column=0, padx=12, pady=12)

        self.search_entry = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="输入关键词检索历史记录",
            height=36
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=12)

        self.btn_search = ctk.CTkButton(
            self.top_frame,
            text="搜索",
            width=90,
            command=self.search_history
        )
        self.btn_search.grid(row=0, column=2, padx=8, pady=12)

        self.btn_show_all = ctk.CTkButton(
            self.top_frame,
            text="显示全部",
            width=90,
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=self.refresh_history
        )
        self.btn_show_all.grid(row=0, column=3, padx=12, pady=12)

        self.table_frame = ctk.CTkFrame(self, corner_radius=12)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=8)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            self.table_frame,
            columns=("时间", "文字数", "内容"),
            show="headings",
            selectmode="extended"
        )

        self.tree.heading("时间", text="识别时间")
        self.tree.heading("文字数", text="文字数")
        self.tree.heading("内容", text="文本摘要")

        self.tree.column("时间", width=180, anchor="center")
        self.tree.column("文字数", width=90, anchor="center")
        self.tree.column("内容", width=430, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.bottom_frame = ctk.CTkFrame(self, corner_radius=12)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 15))
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.tip_label = ctk.CTkLabel(
            self.bottom_frame,
            text="提示：按住 Ctrl 可多选，按住 Shift 可连续多选，然后点击导出。",
            text_color="#6B7280",
            font=("微软雅黑", 12)
        )
        self.tip_label.grid(row=0, column=0, sticky="w", padx=12, pady=12)

        self.btn_export = ctk.CTkButton(
            self.bottom_frame,
            text="导出选中 TXT",
            width=140,
            command=self.export_selected_records
        )
        self.btn_export.grid(row=0, column=1, padx=12, pady=12)

    def refresh_history(self):
        self.tree_record_map.clear()

        for row in self.tree.get_children():
            self.tree.delete(row)

        history_list = history_manager.history_tree.get_history()
        self.insert_history_to_tree(history_list)

    def search_history(self):
        keyword = self.search_entry.get().strip()

        self.tree_record_map.clear()

        for row in self.tree.get_children():
            self.tree.delete(row)

        if keyword:
            history_list = history_manager.history_tree.search_by_keyword(keyword)
        else:
            history_list = history_manager.history_tree.get_history()

        self.insert_history_to_tree(history_list)

    def insert_history_to_tree(self, history_list):
        if not history_list:
            self.tree.insert(
                "",
                tk.END,
                values=("暂无记录", "-", "当前没有匹配的历史记录")
            )
            return

        for item in reversed(history_list):
            time_point = item.get("time_point", item.get("timepoint", 0))
            image_path = item.get("image_path", item.get("img_path", ""))
            text = item.get("text", "")
            text_len = item.get("text_len", len(text))

            time_str = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(time_point)
            )

            text = text.strip()

            if len(text) > 40:
                summary = text[:40] + "..."
            else:
                summary = text if text else "未识别到文字"

            row_id = self.tree.insert(
                "",
                tk.END,
                values=(time_str, f"{text_len} 字", summary)
            )

            self.tree_record_map[row_id] = {
                "time_point": time_point,
                "image_path": image_path,
                "text": text,
                "text_len": text_len
            }

    def export_selected_records(self):
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("提示", "请先选中至少一条历史记录。")
            return

        selected_records = []

        for item_id in selected_items:
            if item_id in self.tree_record_map:
                selected_records.append(self.tree_record_map[item_id])

        if not selected_records:
            messagebox.showwarning("提示", "当前选中的不是有效历史记录。")
            return

        default_name = f"ocr_selected_records_{time.strftime('%Y%m%d_%H%M%S')}.txt"

        save_path = filedialog.asksaveasfilename(
            title="导出选中的历史记录",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )

        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("OCR 多条历史识别记录\n")
                f.write("=" * 70 + "\n")
                f.write(f"导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"导出数量：{len(selected_records)} 条\n")
                f.write("=" * 70 + "\n\n")

                for index, item in enumerate(selected_records, start=1):
                    time_str = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(item["time_point"])
                    )

                    f.write(f"第 {index} 条记录\n")
                    f.write("-" * 70 + "\n")
                    f.write(f"识别时间：{time_str}\n")
                    f.write(f"图片路径：{item['image_path']}\n")
                    f.write(f"文字数量：{item['text_len']} 字\n")
                    f.write("识别内容：\n\n")

                    if item["text"].strip():
                        f.write(item["text"])
                    else:
                        f.write("未识别到文字")

                    f.write("\n\n")

            messagebox.showinfo(
                "导出成功",
                f"已成功导出 {len(selected_records)} 条历史记录：\n\n{save_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "导出失败",
                f"导出 TXT 文件时发生错误：\n\n{e}"
            )

    def close_window(self):
        if self.on_close_callback:
            self.on_close_callback()

        self.destroy()
