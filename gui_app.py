import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pedalboard import Pedalboard, Reverb, Chorus, HighpassFilter
from pedalboard.io import AudioFile

# --- 1. 核心逻辑层：支持动态参数 ---
class AudioProcessor:
    def __init__(self):
        # 默认参数配置
        self.params = {
            "cutoff": 150.0,
            "chorus_mix": 0.3,
            "reverb_room": 0.85,
            "reverb_wet": 0.15
        }

    def _get_board(self):
        """根据当前参数生成 Pedalboard 实例"""
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

            board = self._get_board() # 处理开始前锁定当前参数

            for index, file_path in enumerate(files):
                progress_callback(f"处理中: {file_path.name}", (index / len(files)) * 100)
                target_path = out_path / f"Stereo_{file_path.name}"
                
                with AudioFile(str(file_path)) as f:
                    audio = f.read(f.frames)
                    effected = board(audio, f.samplerate)
                    with AudioFile(str(target_path), 'w', f.samplerate, effected.shape[0]) as o:
                        o.write(effected)

            progress_callback("✅ 处理完成！", 100)
        except Exception as e:
            progress_callback(f"❌ 错误: {str(e)}", 0)

# --- 2. 界面层：增加设置面板 ---
class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("立体声空间生成器 Pro")
        self.root.geometry("600x650")
        self.processor = AudioProcessor()
        self._setup_ui()

    def _setup_ui(self):
        container = tk.Frame(self.root, padx=20, pady=20)
        container.pack(fill='both', expand=True)

        # --- 路径选择区 ---
        self.in_entry = self._create_path_row(container, "输入文件夹:", self.select_input)
        self.out_entry = self._create_path_row(container, "输出文件夹:", self.select_output)

        # --- 参数设置区 (LabelFrame) ---
        settings_frame = tk.LabelFrame(container, text=" 声音效果调节 ", padx=15, pady=15, fg="#2196F3")
        settings_frame.pack(fill='x', pady=20)

        # 高通滤波
        self._create_slider(settings_frame, "高通滤波 (低音切除):", "cutoff", 20, 1000, 150)
        # 合唱效果混合度
        self._create_slider(settings_frame, "合唱强度 (空间感):", "chorus_mix", 0.0, 1.0, 0.3, resolution=0.05)
        # 混响房间大小
        self._create_slider(settings_frame, "混响房间大小 (Room Size):", "reverb_room", 0.0, 1.0, 0.85, resolution=0.05)
        # 混响湿声
        self._create_slider(settings_frame, "混响湿声 (Wet Level):", "reverb_wet", 0.0, 1.0, 0.15, resolution=0.05)

        # --- 操作区 ---
        self.start_btn = tk.Button(container, text="开始批量转换", bg="#4CAF50", fg="white",
                                 font=("Microsoft YaHei", 12, "bold"), height=2, command=self.start_work)
        self.start_btn.pack(fill='x', pady=10)

        self.progress = ttk.Progressbar(container, orient="horizontal", mode="determinate")
        self.progress.pack(fill='x', pady=5)

        self.status_label = tk.Label(container, text="准备就绪", fg="#666")
        self.status_label.pack()

    def _create_slider(self, parent, label, param_key, min_val, max_val, default, resolution=1.0):
        """通用滑块创建函数"""
        frame = tk.Frame(parent)
        frame.pack(fill='x', pady=5)
        tk.Label(frame, text=label, width=20, anchor='w').pack(side='left')
        
        slider = tk.Scale(frame, from_=min_val, to=max_val, orient='horizontal', 
                         resolution=resolution, length=250, 
                         command=lambda v: self.processor.params.update({param_key: float(v)}))
        slider.set(default)
        slider.pack(side='right', fill='x', expand=True)

    def _create_path_row(self, parent, label_text, command):
        tk.Label(parent, text=label_text).pack(anchor='w')
        frame = tk.Frame(parent); frame.pack(fill='x', pady=(0, 10))
        entry = tk.Entry(frame); entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        tk.Button(frame, text="浏览", command=command).pack(side='right')
        return entry

    def select_input(self):
        path = filedialog.askdirectory()
        if path: self.in_entry.delete(0, tk.END); self.in_entry.insert(0, path)

    def select_output(self):
        path = filedialog.askdirectory()
        if path: self.out_entry.delete(0, tk.END); self.out_entry.insert(0, path)

    def update_ui(self, text, val):
        self.status_label.config(text=text)
        self.progress['value'] = val
        if "完成" in text or "错误" in text:
            self.start_btn.config(state='normal', text="开始批量转换")
            if "完成" in text: messagebox.showinfo("成功", "音频处理完毕！")

    def start_work(self):
        in_dir, out_dir = self.in_entry.get(), self.out_entry.get()
        if not in_dir or not out_dir: return messagebox.showwarning("提示", "请选择路径")
        self.start_btn.config(state='disabled', text="正在处理...")
        threading.Thread(target=self.processor.process_files, args=(in_dir, out_dir, self.update_ui), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()