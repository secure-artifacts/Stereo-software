import PyInstaller.__main__
import os
import shutil

def build():
    app_name = "StereoGenerator"
    # 清理舊文件
    for d in ['build', 'dist']:
        if os.path.exists(d): shutil.rmtree(d)

    PyInstaller.__main__.run([
        'main.py',
        f'--name={app_name}',
        '--noconsole',
        '--onefile',
        '--collect-all=pedalboard', # 確保包含音頻插件
        '--clean'
    ])

if __name__ == "__main__":
    build()
