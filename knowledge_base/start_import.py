import os
import subprocess

CURRENT_DIR = os.path.dirname(__file__)
VENV_SCRIPT = os.path.abspath(os.path.join(CURRENT_DIR, 'env', 'Scripts', 'activate.bat'))
os.chdir(CURRENT_DIR)

def run():
    try:
        subprocess.Popen(f'cmd /c "{VENV_SCRIPT} && python manage.py"', shell=True)
    except Exception as e:
        print(f"An error occurred: {e}")