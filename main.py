import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pedalboard import Pedalboard, Reverb, Chorus, HighpassFilter
from pedalboard.io import AudioFile

class AudioProcessor:
    def __init__(self):
        self.params = {
            "cutoff": 150.0,
            "chorus_mix": 0.3,
            "reverb_room": 0.85,
            "reverb_wet": 0.15
        }

    def _get_board(self):
        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=self.params["cutoff"]),
            Chorus(rate_hz=0.5, depth=0.15, centre_delay_ms=8.0, feedback=0.0, mix=self.params["chorus_mix"]),
            Reverb(room_size=self.params["reverb_room"], damping=0.6, 
                   wet_level=self.params["reverb_wet"], dry_level=1.0, width=1.0)
        ])

    def process_files(self, input_dir, output_dir, progress_callback):
        try:
            in_path, out_path = Path(input_dir), Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            files = [f for f in in_path.iterdir() if f.suffix.lower() in {'.wav', '.mp3', '.flac', '.m4a'}]
            
            if not files:
                progress_callback("❌ 文件夹为空！", 100); return

            board = self._get_board()
            for index, file_path in enumerate(files):
                progress_callback(f"处理中: {file_path.name}", (index / len(files)) * 100)
                target_path = out_path / f"Stereo_{file_path.name}"
                with AudioFile(str(file_path)) as f:
                    audio = f.read(f.frames)
                    effected = board(audio, f.samplerate)
                    with AudioFile(str(target_path), 'w', f.samplerate, effected.shape[0]) as o:
                        o.write(effected)
            progress_callback("✅ 全部处理完成！", 100)
        except Exception as e:
            progress_callback(f"❌ 错误: {str(e)}", 0)

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("立体声空间生成器 Pro")
        self.root.geometry("600x600")
        self.processor = AudioProcessor()
        self._setup_ui()

    def _setup_ui(self):
        container = tk.Frame(self.root, padx=20, pady=20)
        container.pack(fill='both', expand=True)

        self.in_entry = self._create_path_row(container, "输入文件夹:", self.select_input)
        self.out_entry = self._create_path_row(container, "输出文件夹:", self.select_output)

        settings_frame = tk.LabelFrame(container, text=" 声音效果调节 ", padx=15, pady=15)
        settings_frame.pack(fill='x', pady=20)

        self._create_slider(settings_frame, "高通滤波:", "cutoff", 20, 1000, 150)
        self._create_slider(settings_frame, "合唱强度:", "chorus_mix", 0.0, 1.0, 0.3, 0.05)
        self._create_slider(settings_frame, "混响房间:", "reverb_room", 0.0, 1.0, 0.85, 0.05)
        self._create_slider(settings_frame, "混响湿声:", "reverb_wet", 0.0, 1.0, 0.15, 0.05)

        self.start_btn = tk.Button(container, text="开始批量转换", bg="#4CAF50", fg="white",
                                 font=("Arial", 12, "bold"), height=2, command=self.start_work)
        self.start_btn.pack(fill='x', pady=10)

        self.progress = ttk.Progressbar(container, orient="horizontal", mode="determinate")
        self.progress.pack(fill='x', pady=5)
        self.status_label = tk.Label(container, text="准备就绪", fg="gray")
        self.status_label.pack()

    def _create_slider(self, parent, label, key, min_v, max_v, default, res=1.0):
        f = tk.Frame(parent); f.pack(fill='x', pady=2)
        tk.Label(f, text=label, width=15, anchor='w').pack(side='left')
        s = tk.Scale(f, from_=min_v, to=max_v, orient='horizontal', resolution=res,
                     command=lambda v: self.processor.params.update({key: float(v)}))
        s.set(default); s.pack(side='right', fill='x', expand=True)

    def _create_path_row(self, parent, text, cmd):
        tk.Label(parent, text=text).pack(anchor='w')
        f = tk.Frame(parent); f.pack(fill='x', pady=(0, 10))
        e = tk.Entry(f); e.pack(side='left', fill='x', expand=True, padx=(0, 5))
        tk.Button(f, text="浏览", command=cmd).pack(side='right')
        return e

    def select_input(self):
        p = filedialog.askdirectory()
        if p: self.in_entry.delete(0, tk.END); self.in_entry.insert(0, p)

    def select_output(self):
        p = filedialog.askdirectory()
        if p: self.out_entry.delete(0, tk.END); self.out_entry.insert(0, p)

    def update_ui(self, text, val):
        self.status_label.config(text=text)
        self.progress['value'] = val
        if "完成" in text or "错误" in text:
            self.start_btn.config(state='normal', text="开始批量转换")
            if "完成" in text: messagebox.showinfo("成功", "處理完畢！")

    def start_work(self):
        if not self.in_entry.get() or not self.out_entry.get():
            return messagebox.showwarning("提示", "請選擇路徑")
        self.start_btn.config(state='disabled', text="處理中...")
        threading.Thread(target=self.processor.process_files, 
                         args=(self.in_entry.get(), self.out_entry.get(), self.update_ui), 
                         daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
