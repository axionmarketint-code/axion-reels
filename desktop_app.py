"""AXION Alert Video Generator - desktop app (Tkinter). Needs: Pillow. Uses bundled ffmpeg (imageio-ffmpeg) or system ffmpeg."""
import os, shutil, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import alert_template as A, breaking_template as B

def ffmpeg_path():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: return shutil.which("ffmpeg")

LBL=dict(header="Header",symbol="Symbol",title="Title",subtitle="Subtitle",pips="Move (e.g. +423.5)",unit="Unit",from_price="From price",
 to_price="To price",range_text="Range line",chart_label="Chart label",watch_title="Watch title",watch1="Watch line 1",watch2="Watch line 2",
 warn="Warning line",advice="Advice line",cta="Button text",footer="Footer")

NLBL=dict(tag="Tab label",headline="Headline",body="Body text",stat1="Box 1 (LABEL|value)",stat2="Box 2 (LABEL|value)",stat3="Box 3 (optional)",stamp="Time stamp (optional)")

class App(tk.Tk):
    def __init__(s):
        super().__init__(); s.title("AXION Alert Video Generator"); s.geometry("900x820")
        left=ttk.Frame(s); left.pack(side="left",fill="both",expand=True,padx=10,pady=10)
        ttk.Label(left,text="Paste Telegram post:").pack(anchor="w")
        s.tpl=tk.StringVar(value="Market Alert"); cb=ttk.Combobox(left,textvariable=s.tpl,values=["Market Alert","Breaking News"],state="readonly"); cb.pack(fill="x",pady=(0,6)); cb.bind("<<ComboboxSelected>>",lambda e:s.rebuild())
        s.paste=tk.Text(left,height=5); s.paste.pack(fill="x")
        ttk.Button(left,text="Auto-fill from text",command=s.fill).pack(fill="x",pady=4)
        s.form=ttk.Frame(left); s.form.pack(fill="x"); s.v={}; s.rebuild(first=True)
        s.btn=ttk.Button(left,text="Export MP4",command=s.export); s.btn.pack(fill="x",pady=8)
        s.msg=ttk.Label(left,text=""); s.msg.pack()
        s.pv=ttk.Label(s); s.pv.pack(side="right",padx=10,pady=10); s.preview()
    def news(s): return s.tpl.get()=="Breaking News"
    def rebuild(s,first=False):
        for w in s.form.winfo_children(): w.destroy()
        s.v={}; labels,defs=(NLBL,{**B.DEFAULTS,"stat1":"ACTUAL|3.4%","stat2":"FORECAST|3.2%","stat3":"PREVIOUS|3.1%"}) if s.news() else (LBL,A.DEFAULTS)
        for k,l in labels.items():
            r=ttk.Frame(s.form); r.pack(fill="x",pady=1); ttk.Label(r,text=l,width=22).pack(side="left")
            s.v[k]=tk.StringVar(value=str(defs.get(k,""))); ttk.Entry(r,textvariable=s.v[k]).pack(side="left",fill="x",expand=True)
            s.v[k].trace_add("write",lambda *a:s.preview())
        if not first: s.preview()
    def fields(s):
        f={k:v.get() for k,v in s.v.items()}
        if s.news(): f["stats"]=[f.pop(k) for k in ("stat1","stat2","stat3") if f.get(k)]; f={k:v for k,v in f.items() if not k.startswith("stat") or k=="stats"}
        return f
    def _fields_old(s): return {k:v.get() for k,v in s.v.items()}
    def preview(s):
        from PIL import ImageTk
        im=(B.render_frame({**B.DEFAULTS,**s.fields()},B.DUR-.5) if s.news() else A.render_frame({**A.DEFAULTS,**s.fields()},14.9)).resize((360,640)); s.ph=ImageTk.PhotoImage(im); s.pv.configure(image=s.ph)
    def fill(s):
        o=B.parse_news(s.paste.get("1.0","end")) if s.news() else A.parse_alert(s.paste.get("1.0","end"))
        if s.news():
            st=o.pop("stats",[]); o.update({f"stat{i+1}":(st[i] if i<len(st) else "") for i in range(3)})
        for k,v in o.items():
            if k in s.v: s.v[k].set(v)
        s.msg.config(text="Filled: "+", ".join(o) if o else "Nothing recognised, edit by hand.")
    def export(s):
        ff=ffmpeg_path()
        if not ff: return messagebox.showerror("ffmpeg missing","Install ffmpeg or use the packaged app.")
        out=filedialog.asksaveasfilename(defaultextension=".mp4",initialfile="axion-alert.mp4")
        if not out: return
        A.FFMPEG=ff; B.FFMPEG=ff; s.btn.state(["disabled"]); s.msg.config(text="Rendering (about 15 s)...")
        def run():
            try: (B if s.news() else A).render_video(s.fields(),out); r="Saved: "+out
            except Exception as e: r="Failed: "+str(e)
            s.after(0,lambda:(s.msg.config(text=r),s.btn.state(["!disabled"])))
        threading.Thread(target=run,daemon=True).start()

if __name__=="__main__": App().mainloop()
