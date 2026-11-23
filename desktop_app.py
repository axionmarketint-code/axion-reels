"""AXION Alert Video Generator - desktop app (Tkinter). Needs: Pillow. Uses bundled ffmpeg (imageio-ffmpeg) or system ffmpeg."""
import os, shutil, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import alert_template as A

def ffmpeg_path():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: return shutil.which("ffmpeg")

LBL=dict(header="Header",symbol="Symbol",title="Title",subtitle="Subtitle",pips="Move (e.g. +423.5)",unit="Unit",from_price="From price",
 to_price="To price",range_text="Range line",chart_label="Chart label",watch_title="Watch title",watch1="Watch line 1",watch2="Watch line 2",
 warn="Warning line",advice="Advice line",cta="Button text",footer="Footer")

class App(tk.Tk):
    def __init__(s):
        super().__init__(); s.title("AXION Alert Video Generator"); s.geometry("900x820")
        left=ttk.Frame(s); left.pack(side="left",fill="both",expand=True,padx=10,pady=10)
        ttk.Label(left,text="Paste Telegram post:").pack(anchor="w")
        s.paste=tk.Text(left,height=5); s.paste.pack(fill="x")
        ttk.Button(left,text="Auto-fill from text",command=s.fill).pack(fill="x",pady=4)
        s.v={}
        for k,l in LBL.items():
            r=ttk.Frame(left); r.pack(fill="x",pady=1); ttk.Label(r,text=l,width=18).pack(side="left")
            s.v[k]=tk.StringVar(value=A.DEFAULTS[k]); e=ttk.Entry(r,textvariable=s.v[k]); e.pack(side="left",fill="x",expand=True)
            s.v[k].trace_add("write",lambda *a:s.preview())
        s.btn=ttk.Button(left,text="Export MP4",command=s.export); s.btn.pack(fill="x",pady=8)
        s.msg=ttk.Label(left,text=""); s.msg.pack()
        s.pv=ttk.Label(s); s.pv.pack(side="right",padx=10,pady=10); s.preview()
    def fields(s): return {k:v.get() for k,v in s.v.items()}
    def preview(s):
        from PIL import ImageTk
        im=A.render_frame({**A.DEFAULTS,**s.fields()},14.9).resize((360,640)); s.ph=ImageTk.PhotoImage(im); s.pv.configure(image=s.ph)
    def fill(s):
        o=A.parse_alert(s.paste.get("1.0","end"))
        for k,v in o.items(): s.v[k].set(v)
        s.msg.config(text="Filled: "+", ".join(o) if o else "Nothing recognised, edit by hand.")
    def export(s):
        ff=ffmpeg_path()
        if not ff: return messagebox.showerror("ffmpeg missing","Install ffmpeg or use the packaged app.")
        out=filedialog.asksaveasfilename(defaultextension=".mp4",initialfile="axion-alert.mp4")
        if not out: return
        A.FFMPEG=ff; s.btn.state(["disabled"]); s.msg.config(text="Rendering (about 15 s)...")
        def run():
            try: A.render_video(s.fields(),out); r="Saved: "+out
            except Exception as e: r="Failed: "+str(e)
            s.after(0,lambda:(s.msg.config(text=r),s.btn.state(["!disabled"])))
        threading.Thread(target=run,daemon=True).start()

if __name__=="__main__": App().mainloop()
