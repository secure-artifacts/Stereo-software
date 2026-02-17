import PyInstaller.__main__
import platform
import shutil
import os

def run_build():
    app_name = "立体声空间生成器"
    entry_point = "main.py"
    
    # 刪除舊的構建文件
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # PyInstaller 參數
    opts = [
        entry_point,
        f'--name={app_name}',
        '--noconsole',          # 不顯示終端
        '--onefile',            # 單個文件
        '--clean',              # 清理緩存
        '--collect-all=pedalboard', # 重要：強制打包 pedalboard 的二進制庫
        '--log-level=INFO',
    ]

    print(f"🚀 開始在 {platform.system()} 上打包 {app_name}...")
    PyInstaller.__main__.run(opts)
    print(f"✅ 打包完成！請查看 dist 夾下的 {app_name}.app")

if __name__ == "__main__":
    run_build()
