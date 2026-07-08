from tkinter import filedialog,messagebox
def export_txt(text_):
    content = text_.get("1.0","end").strip()
    if len(content) == 0:
        messagebox.showerror("无文字")
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if save_path == "":
        return
    try:
        with open(save_path,"w",encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("成功导出")
    except Exception as err:
        messagebox.showerror("导出失败")