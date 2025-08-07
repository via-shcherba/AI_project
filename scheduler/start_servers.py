# import subprocess
# import os
# from project.settings import MAIN_PORT

# def start_server(command):
#     try:
#         process = subprocess.Popen(command)
#         print(f'Started: {" ".join(command)}')
#         return process
#     except Exception as e:
#         print(f'Error starting {" ".join(command)}: {e}')
#         return None
    

# if __name__ == "__main__":
#     venv_path = os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe') 
#     celery_worker_command = [venv_path, "-m", "celery", "-A", "project", "worker", "--pool=solo"] 
#     celery_beat_command = [venv_path, "-m", "celery", "-A", "project", "beat"]
    
#     scheduler_command = [
#         venv_path,
#         "manage.py",
#         "runserver",
#         MAIN_PORT  
#     ]
    
#     start_server(scheduler_command)
#     start_server(celery_worker_command)
#     start_server(celery_beat_command)

import subprocess
import os
import socket
from project.settings import MAIN_PORT

def start_server(command):
    try:
        process = subprocess.Popen(command)
        print(f'Started: {" ".join(command)}')
        return process
    except Exception as e:
        print(f'Error starting {" ".join(command)}: {e}')
        return None
    

if __name__ == "__main__":
    venv_path = os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe')
    
    hostname = socket.gethostname()  
    worker_name = f"worker1@{hostname}"
    
    celery_worker_command = [
        venv_path,
        "-m", "celery",
        "-A", "project",
        "worker",
        "--pool=solo",
        "-n", worker_name
    ]
    
    celery_beat_command = [
        venv_path,
        "-m", "celery",
        "-A", "project",
        "beat"
    ]
    
    scheduler_command = [
        venv_path,
        "manage.py",
        "runserver",
        MAIN_PORT  
    ]
    
    start_server(scheduler_command)
    start_server(celery_worker_command)
    start_server(celery_beat_command)