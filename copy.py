import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("My OCR")
root.minsize(400,300)

text_box = tk.Text(root,font=("微软雅黑",11),wrap=tk.WORD)
text_box.pack()

def copy():
    content = text_box.get("1.0",tk.END).strip()
    if len(content) == 0:
        messagebox.showerror("无文字")
        return
    root.clipboard_clear()
    root.clipboard_append(content)
    root.update()
    messagebox.showinfo("复制成功")
    copy_botton = tk.Button(root,text = "复制",command=copy())
    copy_botton.pack(pady=5)

def fill_result(str):
    text_box.delete("1.0",tk.END)
    text_box.insert(tk.END,str)

root.mainloop()