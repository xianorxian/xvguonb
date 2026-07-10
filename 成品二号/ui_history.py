import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import customtkinter as ctk
from PIL import Image

import history_manager


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master, on_close_callback=None):
        super().__init__(master)

        self.master = master
        self.on_close_callback = on_close_callback

        # Treeview 中每一行对应的完整历史记录
        self.tree_record_map = {}

        self.title("历史记录管理器")
        self.geometry("820x520")
        self.minsize(760, 460)

        # 让历史窗口依附主窗口，并显示在主窗口前面
        self.transient(master)
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        self.create_widgets()
        self.refresh_history()

        self.protocol("WM_DELETE_WINDOW", self.close_window)

    # =========================================================
    # 创建界面
    # =========================================================
    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 顶部搜索区域
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

        # 中间表格区域
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

        self.tree.column("时间", width=190, anchor="center")
        self.tree.column("文字数", width=100, anchor="center")
        self.tree.column("内容", width=470, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # 双击查看详情
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # 底部操作区域
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=12)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 15))
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.tip_label = ctk.CTkLabel(
            self.bottom_frame,
            text="提示：双击记录可查看图片和完整文字；按住 Ctrl / Shift 可多选导出。",
            text_color="#6B7280",
            font=("微软雅黑", 12)
        )
        self.tip_label.grid(row=0, column=0, sticky="w", padx=12, pady=12)

        self.btn_view = ctk.CTkButton(
            self.bottom_frame,
            text="查看选中记录",
            width=130,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.view_selected_record
        )
        self.btn_view.grid(row=0, column=1, padx=8, pady=12)

        self.btn_export = ctk.CTkButton(
            self.bottom_frame,
            text="导出选中 TXT",
            width=130,
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=self.export_selected_records
        )
        self.btn_export.grid(row=0, column=2, padx=12, pady=12)

    # =========================================================
    # 刷新和搜索历史记录
    # =========================================================
    def refresh_history(self):
        """
        显示全部历史记录
        """
        self.tree_record_map.clear()

        for row in self.tree.get_children():
            self.tree.delete(row)

        history_list = history_manager.history_tree.get_history()
        self.insert_history_to_tree(history_list)

    def search_history(self):
        """
        按关键词搜索历史记录
        """
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
        """
        将历史记录插入表格
        """
        if not history_list:
            self.tree.insert(
                "",
                tk.END,
                values=("暂无记录", "-", "当前没有匹配的历史记录")
            )
            return

        # 最新记录显示在最上面
        for item in reversed(history_list):
            time_point = item.get("time_point", 0)
            image_path = item.get("image_path", "")
            text = item.get("text", "")
            text_len = item.get("text_len", len(text))

            time_str = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(time_point)
            )

            clean_text = text.strip()

            if len(clean_text) > 45:
                summary = clean_text[:45] + "..."
            else:
                summary = clean_text if clean_text else "未识别到文字"

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

    # =========================================================
    # 查看历史详情
    # =========================================================
    def on_tree_double_click(self, event):
        """
        双击历史记录时查看详情
        """
        self.view_selected_record()

    def view_selected_record(self):
        """
        查看选中的一条历史记录。
        如果选中了多条，默认查看第一条。
        """
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("提示", "请先选中一条历史记录。")
            return

        selected_id = selected_items[0]

        if selected_id not in self.tree_record_map:
            messagebox.showwarning("提示", "当前选中的不是有效历史记录。")
            return

        record = self.tree_record_map[selected_id]

        # 优先使用你新 history_manager.py 里的 get_record_by_tp()
        # 这样可以从 BST 中按 time_point 精确取出完整记录
        time_point = record["time_point"]

        if hasattr(history_manager.history_tree, "get_record_by_tp"):
            full_record = history_manager.history_tree.get_record_by_tp(time_point)
            if full_record is not None:
                record = full_record

        self.show_record_detail(record)

    def show_record_detail(self, record):
        """
        弹出详情窗口，显示图片和完整文字
        """
        detail_win = ctk.CTkToplevel(self)
        detail_win.title("历史记录详情")
        detail_win.geometry("920x600")
        detail_win.minsize(820, 520)

        # 让详情窗口显示在历史窗口前面
        detail_win.transient(self)
        detail_win.lift()
        detail_win.focus_force()
        detail_win.attributes("-topmost", True)
        detail_win.after(200, lambda: detail_win.attributes("-topmost", False))

        detail_win.grid_columnconfigure(0, weight=4)
        detail_win.grid_columnconfigure(1, weight=5)
        detail_win.grid_rowconfigure(0, weight=1)

        image_path = record.get("image_path", "")
        text = record.get("text", "")
        text_len = record.get("text_len", len(text))
        time_point = record.get("time_point", 0)

        time_str = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(time_point)
        )

        # 左侧图片区域
        image_frame = ctk.CTkFrame(detail_win, corner_radius=14)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)
        image_frame.grid_columnconfigure(0, weight=1)
        image_frame.grid_rowconfigure(1, weight=1)

        image_title = ctk.CTkLabel(
            image_frame,
            text="识别图片",
            font=("微软雅黑", 16, "bold")
        )
        image_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 8))

        image_box = ctk.CTkFrame(image_frame, corner_radius=12, fg_color="#F5F6F8")
        image_box.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        image_box.grid_columnconfigure(0, weight=1)
        image_box.grid_rowconfigure(0, weight=1)

        if image_path and os.path.exists(image_path):
            try:
                pil_img = Image.open(image_path)

                max_width = 360
                max_height = 420

                img_width, img_height = pil_img.size
                ratio = min(max_width / img_width, max_height / img_height, 1)

                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                ctk_image = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(new_width, new_height)
                )

                image_label = ctk.CTkLabel(
                    image_box,
                    text="",
                    image=ctk_image
                )
                image_label.image = ctk_image
                image_label.grid(row=0, column=0, padx=10, pady=10)

            except Exception as e:
                error_label = ctk.CTkLabel(
                    image_box,
                    text=f"图片加载失败：\n{e}",
                    text_color="#DC2626",
                    wraplength=330
                )
                error_label.grid(row=0, column=0, padx=15, pady=15)
        else:
            missing_label = ctk.CTkLabel(
                image_box,
                text=f"图片文件不存在或路径失效：\n{image_path}",
                text_color="#DC2626",
                wraplength=330
            )
            missing_label.grid(row=0, column=0, padx=15, pady=15)

        # 右侧文字区域
        text_frame = ctk.CTkFrame(detail_win, corner_radius=14)
        text_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(2, weight=1)

        text_title = ctk.CTkLabel(
            text_frame,
            text="识别文字详情",
            font=("微软雅黑", 16, "bold")
        )
        text_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 8))

        info_text = (
            f"识别时间：{time_str}\n"
            f"文字数量：{text_len} 字\n"
            f"图片路径：{image_path}"
        )

        info_label = ctk.CTkLabel(
            text_frame,
            text=info_text,
            font=("微软雅黑", 12),
            text_color="#6B7280",
            justify="left",
            anchor="w",
            wraplength=430
        )
        info_label.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 8))

        text_box = ctk.CTkTextbox(
            text_frame,
            font=("微软雅黑", 14),
            corner_radius=12,
            wrap="word"
        )
        text_box.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        if text.strip():
            text_box.insert("1.0", text)
        else:
            text_box.insert("1.0", "未识别到文字")

        text_box.configure(state="disabled")

    # =========================================================
    # 导出选中历史记录
    # =========================================================
    def export_selected_records(self):
        """
        导出选中的多条历史记录为 TXT 文件
        """
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("提示", "请先选中至少一条历史记录。")
            return

        selected_records = []

        for item_id in selected_items:
            if item_id in self.tree_record_map:
                record = self.tree_record_map[item_id]

                time_point = record["time_point"]

                if hasattr(history_manager.history_tree, "get_record_by_tp"):
                    full_record = history_manager.history_tree.get_record_by_tp(time_point)
                    if full_record is not None:
                        record = full_record

                selected_records.append(record)

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
                f.write("OCR 历史识别记录\n")
                f.write("=" * 70 + "\n")
                f.write(f"导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"导出数量：{len(selected_records)} 条\n")
                f.write("=" * 70 + "\n\n")

                for index, item in enumerate(selected_records, start=1):
                    time_str = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(item["time_point"])
                    )

                    image_path = item.get("image_path", "")
                    text = item.get("text", "")
                    text_len = item.get("text_len", len(text))

                    f.write(f"第 {index} 条记录\n")
                    f.write("-" * 70 + "\n")
                    f.write(f"识别时间：{time_str}\n")
                    f.write(f"图片路径：{image_path}\n")
                    f.write(f"文字数量：{text_len} 字\n")
                    f.write("识别内容：\n\n")

                    if text.strip():
                        f.write(text)
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

    # =========================================================
    # 关闭窗口
    # =========================================================
    def close_window(self):
        if self.on_close_callback:
            self.on_close_callback()

        self.destroy()
