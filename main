import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import history_manager
import time
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
import ocr
from proccessed import import_and_preprocess_image

class OCRApp:
    def __init__(self, window_root):
        self.root = window_root
        self.root.title("智能本地OCR文字识别系统")
        self.root.geometry("1000x620")

        # 核心数据结构：使用列表支持追加与前后切换
        self.image_list = []
        self.current_index = -1
        self.current_tk_image = None

        # 裁剪功能相关变量
        self.start_x, self.start_y = 0, 0
        self.end_x, self.end_y = 0, 0
        self.crop_rect_id = None
        self.crop_box_canvas = None

        # 图片显示映射参数：用于把画布坐标转换成原图坐标
        self.display_ratio = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.display_image_width = 0
        self.display_image_height = 0
        self.original_image_width = 0
        self.original_image_height = 0

        # 记录历史记录窗口实例，防止重复弹窗
        self.history_win = None

        # 界面风格
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 左右分栏布局
        self.left_frame = tk.Frame(self.root, bg="#f5f5f5", width=450)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root, width=500)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # =========================================================================
        # 左侧：图片上传、预览、翻页、删除
        # =========================================================================
        self.btn_upload = ttk.Button(
            self.left_frame,
            text=" 📂 追加上传图片 ",
            command=self.upload_images
        )
        self.btn_upload.pack(pady=10)

        self.canvas_label = tk.Label(
            self.left_frame,
            text="💡 提示：支持拖拽追加图片；按住左键可【拖拽框选】局部识别区",
            font=("微软雅黑", 9),
            fg="#666666",
            bg="#f5f5f5"
        )
        self.canvas_label.pack(anchor="w", padx=5)

        self.image_canvas = tk.Canvas(
            self.left_frame,
            bg="#e0e0e0",
            relief="solid",
            bd=1
        )
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 翻页栏
        self.page_frame = tk.Frame(self.left_frame, bg="#f5f5f5")
        self.page_frame.pack(fill=tk.X, pady=5)

        self.btn_prev = ttk.Button(
            self.page_frame,
            text="◀ 上一张",
            command=self.show_prev_image
        )
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.lbl_page_info = tk.Label(
            self.page_frame,
            text="暂无图片 (0 / 0)",
            font=("微软雅黑", 10, "bold"),
            bg="#f5f5f5",
            fg="#333333"
        )
        self.lbl_page_info.pack(side=tk.LEFT, expand=True)

        self.btn_next = ttk.Button(
            self.page_frame,
            text="下一张 ▶",
            command=self.show_next_image
        )
        self.btn_next.pack(side=tk.RIGHT, padx=10)

        # 删除图片功能栏
        self.delete_frame = tk.Frame(self.left_frame, bg="#f5f5f5")
        self.delete_frame.pack(fill=tk.X, pady=5)

        self.btn_delete_current = ttk.Button(
            self.delete_frame,
            text="❌ 删除当前图片",
            command=self.delete_current_image
        )
        self.btn_delete_current.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_clear_images = ttk.Button(
            self.delete_frame,
            text="🧹 清空识别区图片",
            command=self.clear_image_list
        )
        self.btn_clear_images.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 注册画布支持外部文件拖拽
        self.image_canvas.drop_target_register(DND_FILES)
        self.image_canvas.dnd_bind('<<Drop>>', self.handle_drop)

        # 绑定鼠标框选动作
        self.image_canvas.bind("<Button-1>", self.on_mouse_down)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # =========================================================================
        # 右侧：OCR结果展示和功能按钮
        # =========================================================================
        self.result_label = tk.Label(
            self.right_frame,
            text="📄 OCR 识别结果展示区：",
            font=("微软雅黑", 10, "bold")
        )
        self.result_label.pack(anchor="w", pady=5)

        self.text_scroll = ttk.Scrollbar(self.right_frame)
        self.text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_result = tk.Text(
            self.right_frame,
            wrap=tk.WORD,
            yscrollcommand=self.text_scroll.set,
            font=("Consolas", 11)
        )
        self.text_result.pack(fill=tk.BOTH, expand=True)
        self.text_scroll.config(command=self.text_result.yview)

        self.bottom_frame = tk.Frame(self.right_frame)
        self.bottom_frame.pack(fill=tk.X, pady=10)

        self.btn_ocr = ttk.Button(
            self.bottom_frame,
            text="⚡ 开始识别当前/全部",
            command=self.start_ocr
        )
        self.btn_ocr.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.btn_copy = ttk.Button(
            self.bottom_frame,
            text="📋 复制文本",
            command=self.copy_text
        )
        self.btn_copy.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.btn_clear = ttk.Button(
            self.bottom_frame,
            text="🗑️ 清理文本",
            command=self.clear_text
        )
        self.btn_clear.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.btn_history = ttk.Button(
            self.bottom_frame,
            text="📜 历史记录 (BST)",
            command=self.show_history_window
        )
        self.btn_history.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

    # =========================================================================
    # 图片显示与翻页
    # =========================================================================
    def display_current_image(self):
        """根据 current_index 刷新画布图片与页码标签"""
        if 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]

            try:
                pil_img = Image.open(image_path)

                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()

                if canvas_width < 10:
                    canvas_width, canvas_height = 430, 420

                img_width, img_height = pil_img.size

                self.original_image_width = img_width
                self.original_image_height = img_height

                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                self.display_ratio = ratio
                self.display_image_width = new_width
                self.display_image_height = new_height
                self.display_offset_x = (canvas_width - new_width) // 2
                self.display_offset_y = (canvas_height - new_height) // 2

                pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.current_tk_image = ImageTk.PhotoImage(pil_img)

                self.image_canvas.delete("all")
                self.image_canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    anchor=tk.CENTER,
                    image=self.current_tk_image
                )

                # 切换图片后清空旧裁剪框
                self.crop_rect_id = None
                self.crop_box_canvas = None

                self.lbl_page_info.config(
                    text=f"图片数量: ({self.current_index + 1} / {len(self.image_list)})"
                )

                self.root.title(
                    f"智能OCR文字识别系统 - 当前预览: {os.path.basename(image_path)}"
                )

            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败: {e}")

        else:
            self.image_canvas.delete("all")
            self.lbl_page_info.config(text="暂无图片 (0 / 0)")
            self.root.title("智能本地OCR文字识别系统")

    def show_prev_image(self):
        if len(self.image_list) == 0:
            return

        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()
        else:
            messagebox.showinfo("提示", "已经是第一张图片了哦！")

    def show_next_image(self):
        if len(self.image_list) == 0:
            return

        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.display_current_image()
        else:
            messagebox.showinfo("提示", "已经是最后一张图片了！")

    def handle_drop(self, event):
        """拖拽图片到识别区"""
        file_paths = self.root.tk.splitlist(event.data)

        valid_images = [
            p for p in file_paths
            if p.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))
        ]

        if valid_images:
            old_count = len(self.image_list)
            self.image_list.extend(valid_images)

            if old_count == 0:
                self.current_index = 0
            else:
                self.current_index = old_count

            self.display_current_image()
        else:
            messagebox.showwarning("警告", "拖入的文件不是合法的图片格式！")

    def upload_images(self):
        """追加上传图片"""
        file_paths = filedialog.askopenfilenames(
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")]
        )

        if file_paths:
            old_count = len(self.image_list)
            self.image_list.extend(file_paths)

            if old_count == 0:
                self.current_index = 0
            else:
                self.current_index = old_count

            self.display_current_image()

    # =========================================================================
    # 删除识别区图片功能
    # =========================================================================
    def delete_current_image(self):
        """
        删除当前正在预览的图片。
        只从识别区列表中删除，不会删除电脑本地原文件。
        """
        if not self.image_list:
            messagebox.showwarning("提示", "当前识别区没有图片可删除！")
            return

        current_path = self.image_list[self.current_index]

        confirm = messagebox.askyesno(
            "确认删除",
            f"确定要从识别区删除当前图片吗？\n\n{current_path}\n\n注意：不会删除电脑本地文件。"
        )

        if not confirm:
            return

        self.image_list.pop(self.current_index)

        self.crop_box_canvas = None
        self.crop_rect_id = None
        self.image_canvas.delete("crop_rect")

        if len(self.image_list) == 0:
            self.current_index = -1
            self.current_tk_image = None
            self.image_canvas.delete("all")
            self.lbl_page_info.config(text="暂无图片 (0 / 0)")
            self.root.title("智能本地OCR文字识别系统")
            return

        if self.current_index >= len(self.image_list):
            self.current_index = len(self.image_list) - 1

        self.display_current_image()

    def clear_image_list(self):
        """
        清空识别区所有图片。
        只清空程序中的图片列表，不会删除电脑本地文件。
        """
        if not self.image_list:
            messagebox.showwarning("提示", "当前识别区已经没有图片了！")
            return

        confirm = messagebox.askyesno(
            "确认清空",
            "确定要清空识别区中的所有图片吗？\n\n注意：不会删除电脑本地图片文件。"
        )

        if not confirm:
            return

        self.image_list.clear()
        self.current_index = -1
        self.current_tk_image = None

        self.crop_box_canvas = None
        self.crop_rect_id = None

        self.image_canvas.delete("all")
        self.lbl_page_info.config(text="暂无图片 (0 / 0)")
        self.root.title("智能本地OCR文字识别系统")

    # =========================================================================
    # 裁剪功能
    # =========================================================================
    def clamp_point_to_image_area(self, x, y):
        """限制鼠标坐标只能落在图片显示区域内"""
        left = self.display_offset_x
        top = self.display_offset_y
        right = self.display_offset_x + self.display_image_width
        bottom = self.display_offset_y + self.display_image_height

        x = max(left, min(x, right))
        y = max(top, min(y, bottom))

        return x, y

    def get_crop_source_path(self, original_path):
        """
        如果用户框选了区域，就裁剪原图并返回裁剪图路径；
        如果没有框选，就返回原图路径。
        """
        if self.crop_box_canvas is None:
            return original_path, False

        x1, y1, x2, y2 = self.crop_box_canvas

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            return original_path, False

        original_x1 = int((x1 - self.display_offset_x) / self.display_ratio)
        original_y1 = int((y1 - self.display_offset_y) / self.display_ratio)
        original_x2 = int((x2 - self.display_offset_x) / self.display_ratio)
        original_y2 = int((y2 - self.display_offset_y) / self.display_ratio)

        original_x1 = max(0, min(original_x1, self.original_image_width))
        original_y1 = max(0, min(original_y1, self.original_image_height))
        original_x2 = max(0, min(original_x2, self.original_image_width))
        original_y2 = max(0, min(original_y2, self.original_image_height))

        if original_x2 - original_x1 < 10 or original_y2 - original_y1 < 10:
            return original_path, False

        try:
            pil_img = Image.open(original_path)
            cropped_img = pil_img.crop(
                (original_x1, original_y1, original_x2, original_y2)
            )

            temp_folder = "temp_crop_images"

            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

            crop_file_name = f"crop_{int(time.time() * 1000)}.png"
            crop_path = os.path.join(temp_folder, crop_file_name)

            cropped_img.save(crop_path)

            return os.path.abspath(crop_path), True

        except Exception as e:
            messagebox.showerror("裁剪错误", f"裁剪图片失败：\n\n{e}")
            return original_path, False

    # =========================================================================
    # 历史记录窗口
    # =========================================================================
    def show_history_window(self):
        """查看历史记录，支持多选导出 TXT"""
        if self.history_win is not None and tk.Toplevel.winfo_exists(self.history_win):
            self.history_win.lift()
            self.history_win.focus_force()
            return

        self.history_win = tk.Toplevel(self.root)
        self.history_win.title("📜 历史记录管理器 (BST)")
        self.history_win.geometry("720x450")

        def close_history_window():
            self.history_win.destroy()
            self.history_win = None

        self.history_win.protocol("WM_DELETE_WINDOW", close_history_window)

        search_frame = tk.Frame(self.history_win)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        search_lbl = tk.Label(search_frame, text="输入关键词检索历史(BST树查询):")
        search_lbl.pack(side=tk.LEFT, padx=5)

        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tree = ttk.Treeview(
            self.history_win,
            columns=("时间", "大小", "内容"),
            show="headings",
            selectmode="extended"  # 关键：允许多选
        )

        tree.heading("时间", text="识别时间")
        tree.heading("大小", text="文字数")
        tree.heading("内容", text="文本摘要")

        tree.column("时间", width=180)
        tree.column("大小", width=90)
        tree.column("内容", width=400)

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 记录 Treeview 每一行对应的完整历史记录
        tree_record_map = {}

        def refresh_history(keyword=None):
            tree_record_map.clear()

            for row in tree.get_children():
                tree.delete(row)

            if keyword:
                history_list = history_manager.history_tree.search_by_keyword(keyword)
            else:
                history_list = history_manager.history_tree.get_history()

            if not history_list:
                tree.insert("", tk.END, values=("暂无记录", "-", "当前没有匹配的历史记录"))
                return

            # 最新记录显示在最上面
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

                if len(text) > 35:
                    text_summary = text[:35] + "..."
                else:
                    text_summary = text if text else "未识别到文字"

                row_id = tree.insert(
                    "",
                    tk.END,
                    values=(time_str, f"{text_len} 字", text_summary)
                )

                tree_record_map[row_id] = {
                    "time_point": time_point,
                    "image_path": image_path,
                    "text": text,
                    "text_len": text_len
                }

        def export_selected_records():
            """导出历史记录窗口中选中的多条记录为一个 TXT 文件"""

            selected_items = tree.selection()

            if not selected_items:
                messagebox.showwarning("提示", "请先在历史记录窗口中选中至少一条记录！")
                return

            selected_records = []

            for selected_id in selected_items:
                if selected_id in tree_record_map:
                    selected_records.append(tree_record_map[selected_id])

            if not selected_records:
                messagebox.showwarning("提示", "当前选中的不是有效历史记录！")
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
                        time_point = item["time_point"]
                        image_path = item["image_path"]
                        text = item["text"]
                        text_len = item["text_len"]

                        time_str = time.strftime(
                            "%Y-%m-%d %H:%M:%S",
                            time.localtime(time_point)
                        )

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

        btn_search = ttk.Button(
            search_frame,
            text="🔍 快速查找",
            command=lambda: refresh_history(search_entry.get().strip())
        )
        btn_search.pack(side=tk.RIGHT, padx=5)

        btn_show_all = ttk.Button(
            search_frame,
            text="显示全部",
            command=lambda: refresh_history()
        )
        btn_show_all.pack(side=tk.RIGHT, padx=5)

        history_bottom_frame = tk.Frame(self.history_win)
        history_bottom_frame.pack(fill=tk.X, padx=10, pady=8)

        tip_label = tk.Label(
            history_bottom_frame,
            text="提示：按住 Ctrl 可多选，按住 Shift 可连续多选",
            fg="#666666"
        )
        tip_label.pack(side=tk.LEFT, padx=5)

        btn_export_selected = ttk.Button(
            history_bottom_frame,
            text="💾 导出选中TXT",
            command=export_selected_records
        )
        btn_export_selected.pack(side=tk.RIGHT, padx=5)

        refresh_history()

    # =========================================================================
    # OCR 识别功能：支持当前图片、裁剪区域、多图片识别
    # =========================================================================
    def start_ocr(self):
        if not self.image_list:
            messagebox.showwarning("提示", "当前没有待识别的图片，请先上传！")
            return

        choice = messagebox.askyesnocancel(
            "选择识别模式",
            "是否识别全部图片？\n\n"
            "点击【是】：识别全部图片\n"
            "点击【否】：只识别当前图片/当前框选区域\n"
            "点击【取消】：退出识别"
        )

        if choice is None:
            return

        recognize_all = choice

        self.text_result.delete("1.0", tk.END)

        try:
            # =========================================================
            # 情况一：识别全部图片
            # =========================================================
            if recognize_all:
                final_display_string = ""

                final_display_string += "========================================\n"
                final_display_string += "📚 【识别模式】: 多图片批量识别\n"
                final_display_string += f"🖼️ 【图片总数】: {len(self.image_list)} 张\n"
                final_display_string += "========================================\n\n"

                total_start_time = time.time()

                for index, image_path in enumerate(self.image_list):
                    final_display_string += f"\n\n========== 第 {index + 1} 张图片 ==========\n"
                    final_display_string += f"原始图片路径：{image_path}\n"

                    try:
                        # 第一步：调用 proccessed.py 进行图片预处理
                        processed_path = import_and_preprocess_image(image_path)

                        final_display_string += f"预处理图片路径：{processed_path}\n"

                        # 第二步：把预处理后的图片交给 OCR
                        ocr_result = ocr.run_ocr(processed_path)

                        if not ocr_result["success"]:
                            final_display_string += f"❌ 识别失败：{ocr_result['message']}\n"
                            continue

                        extracted_text_lines = []

                        final_display_string += f"⏱️ 当前图片识别耗时：{ocr_result.get('elapsed', 0):.4f} 秒\n"
                        final_display_string += "📄 识别结果：\n"

                        for text_info in ocr_result["data"]:
                            line_text = text_info["text"]
                            extracted_text_lines.append(line_text)
                            final_display_string += f"{line_text}\n"

                        if not extracted_text_lines:
                            final_display_string += "未识别到明显文字。\n"

                        pure_saved_text = " ".join(extracted_text_lines)
                        history_manager.history_tree.add_history(image_path, pure_saved_text)

                    except Exception as single_error:
                        final_display_string += f"❌ 当前图片处理失败：{single_error}\n"
                        continue

                total_end_time = time.time()

                final_display_string += "\n\n========================================\n"
                final_display_string += "✅ 多图片识别完成\n"
                final_display_string += f"⏱️ 总耗时：{total_end_time - total_start_time:.4f} 秒\n"
                final_display_string += "========================================\n"

                self.text_result.insert(tk.END, final_display_string)

                messagebox.showinfo("成功", "全部图片预处理与识别完成！")

            # =========================================================
            # 情况二：识别当前图片 / 当前框选区域
            # =========================================================
            else:
                current_original_path = self.image_list[self.current_index]

                # 如果用户框选了区域，就先生成裁剪图
                # 如果没有框选，就直接使用原图
                source_path, is_cropped = self.get_crop_source_path(current_original_path)

                # 第一步：调用 proccessed.py 处理原图或裁剪图
                processed_path = import_and_preprocess_image(source_path)

                # 第二步：把处理后的图片交给 OCR
                ocr_result = ocr.run_ocr(processed_path)

                if not ocr_result["success"]:
                    messagebox.showerror("OCR错误", f"算法提取文字失败: {ocr_result['message']}")
                    return

                extracted_text_lines = []
                final_display_string = ""

                final_display_string += "========================================\n"
                final_display_string += f"🖼️ 【识别范围】: {'框选区域' if is_cropped else '整张图片'}\n"
                final_display_string += f"🧪 【预处理图片】: {processed_path}\n"
                final_display_string += f"⏱️ 【识别耗时】: {ocr_result.get('elapsed', 0):.4f} 秒\n"
                final_display_string += "========================================\n\n"
                final_display_string += "📄 【提取出的纯净文字】:\n"

                for text_info in ocr_result["data"]:
                    line_text = text_info["text"]
                    extracted_text_lines.append(line_text)
                    final_display_string += f"{line_text}\n"

                if not extracted_text_lines:
                    final_display_string += "未识别到明显文字。\n"

                self.text_result.insert(tk.END, final_display_string)

                pure_saved_text = " ".join(extracted_text_lines)
                history_manager.history_tree.add_history(current_original_path, pure_saved_text)

                messagebox.showinfo("成功", "当前图片预处理与识别完成！")

        except Exception as e:
            messagebox.showerror(
                "系统联调错误",
                f"图片预处理或 OCR 识别过程中发生错误：\n\n{e}"
            )

    # =========================================================================
    # 文本框功能
    # =========================================================================
    def copy_text(self):
        content = self.text_result.get("1.0", tk.END).strip()

        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("提示", "文本已成功复制到系统剪贴板！")
        else:
            messagebox.showwarning("提示", "当前没有可复制的文本！")

    def clear_text(self):
        if messagebox.askyesno("确认", "确定要清空当前的识别结果吗？"):
            self.text_result.delete("1.0", tk.END)

    # =========================================================================
    # 鼠标框选事件
    # =========================================================================
    def on_mouse_down(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.start_x, self.start_y = x, y
        self.end_x, self.end_y = x, y

        self.crop_box_canvas = None
        self.image_canvas.delete("crop_rect")

    def on_mouse_drag(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.end_x, self.end_y = x, y

        self.image_canvas.delete("crop_rect")
        self.crop_rect_id = self.image_canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="red",
            width=2,
            dash=(4, 4),
            tags="crop_rect"
        )

    def on_mouse_up(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.end_x, self.end_y = x, y

        if abs(self.end_x - self.start_x) < 10 or abs(self.end_y - self.start_y) < 10:
            self.crop_box_canvas = None
            self.image_canvas.delete("crop_rect")
            return

        self.crop_box_canvas = (
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y
        )


if __name__ == "__main__":
    root_window = TkinterDnD.Tk()
    app = OCRApp(root_window)
    root_window.mainloop()
