import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk

import ocr
import history_manager
from ui_history import HistoryWindow
from processed import import_and_preprocess_image


class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


SUPPORTED_IMAGE_TYPES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def is_supported_image(file_path):
    return file_path.lower().endswith(SUPPORTED_IMAGE_TYPES)


def ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


class OCRApp(CTkDnD):
    def __init__(self):
        super().__init__()

        # 简洁浅色风格
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(1.05)

        # 全局配色：少颜色、简洁、清爽
        self.COLOR_BG = "#F5F6F8"
        self.COLOR_CARD = "#FFFFFF"
        self.COLOR_BORDER = "#DDE1E6"
        self.COLOR_TEXT = "#1F2937"
        self.COLOR_SUBTEXT = "#6B7280"
        self.COLOR_PRIMARY = "#2563EB"
        self.COLOR_PRIMARY_HOVER = "#1D4ED8"
        self.COLOR_GRAY = "#6B7280"
        self.COLOR_GRAY_HOVER = "#4B5563"

        self.init_window()
        self.init_variables()
        self.create_layout()
        self.bind_events()

    # =========================================================================
    # 初始化窗口与变量
    # =========================================================================
    def init_window(self):
        self.title("智能本地 OCR 文字识别系统")
        self.geometry("1280x760")
        self.minsize(1180, 700)
        self.configure(fg_color=self.COLOR_BG)

    def init_variables(self):
        self.image_list = []
        self.current_index = -1
        self.current_tk_image = None

        # 裁剪相关变量
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.crop_rect_id = None
        self.crop_box_canvas = None

        # 画布图片坐标映射变量
        self.display_ratio = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        self.display_image_width = 0
        self.display_image_height = 0
        self.original_image_width = 0
        self.original_image_height = 0

        self.history_win = None

        self.status_var = tk.StringVar()
        self.status_var.set("状态：等待上传图片")

    # =========================================================================
    # 界面布局
    # =========================================================================
    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_top_bar()
        self.create_main_area()

    def create_top_bar(self):
        self.top_bar = ctk.CTkFrame(
            self,
            height=64,
            corner_radius=0,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="智能本地 OCR 文字识别系统",
            font=("微软雅黑", 24, "bold"),
            text_color=self.COLOR_TEXT
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=28, pady=16)

        self.status_label = ctk.CTkLabel(
            self.top_bar,
            textvariable=self.status_var,
            font=("微软雅黑", 13),
            text_color=self.COLOR_SUBTEXT
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=28, pady=16)

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=self.COLOR_BG
        )
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=22, pady=22)

        self.main_frame.grid_columnconfigure(0, weight=5)
        self.main_frame.grid_columnconfigure(1, weight=6)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        self.left_panel = ctk.CTkFrame(
            self.main_frame,
            corner_radius=18,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 11))
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(2, weight=1)

        self.left_title = ctk.CTkLabel(
            self.left_panel,
            text="图片管理区",
            font=("微软雅黑", 18, "bold"),
            text_color=self.COLOR_TEXT
        )
        self.left_title.grid(row=0, column=0, sticky="w", padx=22, pady=(20, 8))

        self.upload_frame = ctk.CTkFrame(
            self.left_panel,
            fg_color="transparent"
        )
        self.upload_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 12))
        self.upload_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_upload = ctk.CTkButton(
            self.upload_frame,
            text="上传图片",
            height=38,
            fg_color=self.COLOR_PRIMARY,
            hover_color=self.COLOR_PRIMARY_HOVER,
            command=self.upload_images
        )
        self.btn_upload.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_delete_current = ctk.CTkButton(
            self.upload_frame,
            text="删除当前",
            height=38,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.delete_current_image
        )
        self.btn_delete_current.grid(row=0, column=1, sticky="ew", padx=8)

        self.btn_clear_images = ctk.CTkButton(
            self.upload_frame,
            text="清空识别区",
            height=38,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.clear_image_list
        )
        self.btn_clear_images.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.canvas_container = ctk.CTkFrame(
            self.left_panel,
            corner_radius=14,
            fg_color="#FAFAFA",
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.canvas_container.grid(row=2, column=0, sticky="nsew", padx=22, pady=8)
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        self.image_canvas = tk.Canvas(
            self.canvas_container,
            bg="#FAFAFA",
            highlightthickness=0,
            relief="flat"
        )
        self.image_canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tip_label = ctk.CTkLabel(
            self.left_panel,
            text="拖拽图片到预览区；按住左键拖拽可框选局部识别区域。",
            font=("微软雅黑", 12),
            text_color=self.COLOR_SUBTEXT
        )
        self.tip_label.grid(row=3, column=0, sticky="w", padx=22, pady=(6, 4))

        self.page_frame = ctk.CTkFrame(
            self.left_panel,
            fg_color="transparent"
        )
        self.page_frame.grid(row=4, column=0, sticky="ew", padx=22, pady=(8, 20))
        self.page_frame.grid_columnconfigure(1, weight=1)

        self.btn_prev = ctk.CTkButton(
            self.page_frame,
            text="上一张",
            width=96,
            height=34,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.show_prev_image
        )
        self.btn_prev.grid(row=0, column=0, sticky="w")

        self.page_label = ctk.CTkLabel(
            self.page_frame,
            text="暂无图片 (0 / 0)",
            font=("微软雅黑", 14),
            text_color=self.COLOR_TEXT
        )
        self.page_label.grid(row=0, column=1)

        self.btn_next = ctk.CTkButton(
            self.page_frame,
            text="下一张",
            width=96,
            height=34,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.show_next_image
        )
        self.btn_next.grid(row=0, column=2, sticky="e")

    def create_right_panel(self):
        self.right_panel = ctk.CTkFrame(
            self.main_frame,
            corner_radius=18,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(11, 0))
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        self.right_title = ctk.CTkLabel(
            self.right_panel,
            text="OCR 识别结果",
            font=("微软雅黑", 18, "bold"),
            text_color=self.COLOR_TEXT
        )
        self.right_title.grid(row=0, column=0, sticky="w", padx=22, pady=(20, 8))

        self.text_result = ctk.CTkTextbox(
            self.right_panel,
            font=("微软雅黑", 14),
            corner_radius=14,
            fg_color="#FAFAFA",
            text_color=self.COLOR_TEXT,
            border_width=1,
            border_color=self.COLOR_BORDER,
            wrap="word"
        )
        self.text_result.grid(row=1, column=0, sticky="nsew", padx=22, pady=8)

        self.progress = ctk.CTkProgressBar(
            self.right_panel,
            height=10,
            progress_color=self.COLOR_PRIMARY
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 4))
        self.progress.set(0)

        self.action_frame = ctk.CTkFrame(
            self.right_panel,
            fg_color="transparent"
        )
        self.action_frame.grid(row=3, column=0, sticky="ew", padx=22, pady=(12, 20))
        self.action_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_ocr = ctk.CTkButton(
            self.action_frame,
            text="开始识别",
            height=38,
            fg_color=self.COLOR_PRIMARY,
            hover_color=self.COLOR_PRIMARY_HOVER,
            command=self.start_ocr
        )
        self.btn_ocr.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_copy = ctk.CTkButton(
            self.action_frame,
            text="复制文本",
            height=38,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.copy_text
        )
        self.btn_copy.grid(row=0, column=1, sticky="ew", padx=8)

        self.btn_clear_text = ctk.CTkButton(
            self.action_frame,
            text="清空文本",
            height=38,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.clear_text
        )
        self.btn_clear_text.grid(row=0, column=2, sticky="ew", padx=8)

        self.btn_history = ctk.CTkButton(
            self.action_frame,
            text="历史记录",
            height=38,
            fg_color=self.COLOR_GRAY,
            hover_color=self.COLOR_GRAY_HOVER,
            command=self.show_history_window
        )
        self.btn_history.grid(row=0, column=3, sticky="ew", padx=(8, 0))

    # =========================================================================
    # 事件绑定
    # =========================================================================
    def bind_events(self):
        self.image_canvas.drop_target_register(DND_FILES)
        self.image_canvas.dnd_bind("<<Drop>>", self.handle_drop)

        self.image_canvas.bind("<Button-1>", self.on_mouse_down)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    # =========================================================================
    # 图片上传与显示
    # =========================================================================
    def upload_images(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")]
        )

        if not file_paths:
            return

        valid_images = [p for p in file_paths if is_supported_image(p)]

        if not valid_images:
            messagebox.showwarning("警告", "未选择合法图片文件。")
            return

        old_count = len(self.image_list)
        self.image_list.extend(valid_images)

        if old_count == 0:
            self.current_index = 0
        else:
            self.current_index = old_count

        self.display_current_image()
        self.status_var.set(f"状态：已上传 {len(valid_images)} 张图片，当前共 {len(self.image_list)} 张")

    def handle_drop(self, event):
        file_paths = self.tk.splitlist(event.data)
        valid_images = [p for p in file_paths if is_supported_image(p)]

        if not valid_images:
            messagebox.showwarning("警告", "拖入的文件不是合法图片格式。")
            return

        old_count = len(self.image_list)
        self.image_list.extend(valid_images)

        if old_count == 0:
            self.current_index = 0
        else:
            self.current_index = old_count

        self.display_current_image()
        self.status_var.set(f"状态：拖拽导入 {len(valid_images)} 张图片，当前共 {len(self.image_list)} 张")

    def display_current_image(self):
        if 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]

            try:
                pil_img = Image.open(image_path)

                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()

                if canvas_width < 10:
                    canvas_width = 540
                    canvas_height = 520

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

                self.crop_rect_id = None
                self.crop_box_canvas = None

                self.page_label.configure(
                    text=f"图片数量：{self.current_index + 1} / {len(self.image_list)}"
                )

                self.title(f"智能本地 OCR 文字识别系统 - {os.path.basename(image_path)}")

            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败：\n\n{e}")

        else:
            self.image_canvas.delete("all")
            self.page_label.configure(text="暂无图片 (0 / 0)")
            self.title("智能本地 OCR 文字识别系统")

    def show_prev_image(self):
        if not self.image_list:
            return

        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()
        else:
            messagebox.showinfo("提示", "已经是第一张图片。")

    def show_next_image(self):
        if not self.image_list:
            return

        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.display_current_image()
        else:
            messagebox.showinfo("提示", "已经是最后一张图片。")

    def delete_current_image(self):
        if not self.image_list:
            messagebox.showwarning("提示", "当前识别区没有图片可删除。")
            return

        current_path = self.image_list[self.current_index]

        confirm = messagebox.askyesno(
            "确认删除",
            f"确定从识别区删除当前图片吗？\n\n{current_path}\n\n注意：不会删除电脑本地文件。"
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
            self.page_label.configure(text="暂无图片 (0 / 0)")
            self.status_var.set("状态：识别区已清空")
            self.title("智能本地 OCR 文字识别系统")
            return

        if self.current_index >= len(self.image_list):
            self.current_index = len(self.image_list) - 1

        self.display_current_image()
        self.status_var.set(f"状态：已删除当前图片，剩余 {len(self.image_list)} 张")

    def clear_image_list(self):
        if not self.image_list:
            messagebox.showwarning("提示", "当前识别区已经没有图片。")
            return

        confirm = messagebox.askyesno(
            "确认清空",
            "确定清空识别区所有图片吗？\n\n注意：不会删除电脑本地文件。"
        )

        if not confirm:
            return

        self.image_list.clear()
        self.current_index = -1
        self.current_tk_image = None

        self.crop_box_canvas = None
        self.crop_rect_id = None

        self.image_canvas.delete("all")
        self.page_label.configure(text="暂无图片 (0 / 0)")
        self.progress.set(0)

        self.status_var.set("状态：识别区图片已清空")
        self.title("智能本地 OCR 文字识别系统")

    # =========================================================================
    # 裁剪功能
    # =========================================================================
    def clamp_point_to_image_area(self, x, y):
        left = self.display_offset_x
        top = self.display_offset_y
        right = self.display_offset_x + self.display_image_width
        bottom = self.display_offset_y + self.display_image_height

        x = max(left, min(x, right))
        y = max(top, min(y, bottom))

        return x, y

    def get_crop_source_path(self, original_path):
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
            ensure_folder(temp_folder)

            crop_file_name = f"crop_{int(time.time() * 1000)}.png"
            crop_path = os.path.join(temp_folder, crop_file_name)

            cropped_img.save(crop_path)

            return os.path.abspath(crop_path), True

        except Exception as e:
            messagebox.showerror("裁剪错误", f"裁剪图片失败：\n\n{e}")
            return original_path, False

    def on_mouse_down(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.start_x = x
        self.start_y = y
        self.end_x = x
        self.end_y = y

        self.crop_box_canvas = None
        self.image_canvas.delete("crop_rect")

    def on_mouse_drag(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.end_x = x
        self.end_y = y

        self.image_canvas.delete("crop_rect")

        self.crop_rect_id = self.image_canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline=self.COLOR_PRIMARY,
            width=2,
            dash=(4, 4),
            tags="crop_rect"
        )

    def on_mouse_up(self, event):
        if not self.image_list:
            return

        x, y = self.clamp_point_to_image_area(event.x, event.y)

        self.end_x = x
        self.end_y = y

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

        self.status_var.set("状态：已选择局部识别区域")

    # =========================================================================
    # OCR 识别
    # =========================================================================
    def start_ocr(self):
        if not self.image_list:
            messagebox.showwarning("提示", "当前没有待识别图片，请先上传。")
            return

        choice = messagebox.askyesnocancel(
            "选择识别模式",
            "是否识别全部图片？\n\n"
            "点击【是】：识别全部图片\n"
            "点击【否】：只识别当前图片或当前框选区域\n"
            "点击【取消】：退出识别"
        )

        if choice is None:
            return

        self.text_result.delete("1.0", "end")
        self.progress.set(0)

        try:
            if choice:
                self.recognize_all_images()
            else:
                self.recognize_current_image()

        except Exception as e:
            messagebox.showerror(
                "系统错误",
                f"OCR 识别过程中发生错误：\n\n{e}"
            )
            self.status_var.set("状态：识别失败")

    def recognize_all_images(self):
        final_display = ""

        final_display += "========================================\n"
        final_display += "识别模式：多图片批量识别\n"
        final_display += f"图片总数：{len(self.image_list)} 张\n"
        final_display += "========================================\n\n"

        total_start_time = time.time()
        total_count = len(self.image_list)

        for index, image_path in enumerate(self.image_list):
            self.status_var.set(f"状态：正在识别第 {index + 1} / {total_count} 张")
            self.progress.set((index + 1) / total_count)
            self.update_idletasks()

            final_display += f"\n\n========== 第 {index + 1} 张图片 ==========\n"
            final_display += f"原图路径：{image_path}\n"

            try:
                processed_path = import_and_preprocess_image(image_path)
                final_display += f"预处理图路径：{processed_path}\n"

                ocr_result = ocr.run_ocr(processed_path)

                if not ocr_result["success"]:
                    final_display += f"识别失败：{ocr_result['message']}\n"
                    continue

                extracted_text_lines = []

                final_display += f"识别耗时：{ocr_result.get('elapsed', 0):.4f} 秒\n"
                final_display += "识别结果：\n"

                for text_info in ocr_result["data"]:
                    line_text = text_info["text"]
                    extracted_text_lines.append(line_text)
                    final_display += f"{line_text}\n"

                if not extracted_text_lines:
                    final_display += "未识别到明显文字。\n"

                pure_text = " ".join(extracted_text_lines)
                history_manager.history_tree.add_history(image_path, pure_text)

            except Exception as single_error:
                final_display += f"当前图片处理失败：{single_error}\n"
                continue

        total_end_time = time.time()

        final_display += "\n\n========================================\n"
        final_display += "多图片识别完成\n"
        final_display += f"总耗时：{total_end_time - total_start_time:.4f} 秒\n"
        final_display += "========================================\n"

        self.text_result.insert("end", final_display)
        self.status_var.set("状态：全部图片识别完成")
        self.progress.set(1)

        messagebox.showinfo("成功", "全部图片识别完成。")

    def recognize_current_image(self):
        current_original_path = self.image_list[self.current_index]

        source_path, is_cropped = self.get_crop_source_path(current_original_path)

        self.status_var.set("状态：正在进行图片预处理")
        self.update_idletasks()

        processed_path = import_and_preprocess_image(source_path)

        self.status_var.set("状态：正在进行 OCR 识别")
        self.update_idletasks()

        ocr_result = ocr.run_ocr(processed_path)

        if not ocr_result["success"]:
            messagebox.showerror("OCR错误", f"识别失败：{ocr_result['message']}")
            self.status_var.set("状态：识别失败")
            return

        extracted_text_lines = []

        final_display = ""
        final_display += "========================================\n"
        final_display += f"识别范围：{'框选区域' if is_cropped else '整张图片'}\n"
        final_display += f"预处理图路径：{processed_path}\n"
        final_display += f"识别耗时：{ocr_result.get('elapsed', 0):.4f} 秒\n"
        final_display += "========================================\n\n"
        final_display += "识别结果：\n"

        for text_info in ocr_result["data"]:
            line_text = text_info["text"]
            extracted_text_lines.append(line_text)
            final_display += f"{line_text}\n"

        if not extracted_text_lines:
            final_display += "未识别到明显文字。\n"

        self.text_result.insert("end", final_display)

        pure_text = " ".join(extracted_text_lines)
        history_manager.history_tree.add_history(current_original_path, pure_text)

        self.progress.set(1)
        self.status_var.set("状态：当前图片识别完成")

        messagebox.showinfo("成功", "当前图片识别完成。")

    # =========================================================================
    # 文本操作与历史记录
    # =========================================================================
    def copy_text(self):
        content = self.text_result.get("1.0", "end").strip()

        if not content:
            messagebox.showwarning("提示", "当前没有可复制的文本。")
            return

        self.clipboard_clear()
        self.clipboard_append(content)

        self.status_var.set("状态：文本已复制到剪贴板")
        messagebox.showinfo("提示", "文本已复制到剪贴板。")

    def clear_text(self):
        confirm = messagebox.askyesno("确认", "确定要清空当前识别结果吗？")

        if not confirm:
            return

        self.text_result.delete("1.0", "end")
        self.status_var.set("状态：识别结果已清空")

    def show_history_window(self):
        if self.history_win is not None and self.history_win.winfo_exists():
            self.history_win.lift()
            self.history_win.focus_force()
            return

        def on_close():
            self.history_win = None

        self.history_win = HistoryWindow(self, on_close_callback=on_close)
        self.history_win.lift()
        self.history_win.focus_force()
