import os
import subprocess
from chat_project.settings import REDIS_PORT, MAIN_PORT


def start_server(command):
    try:
        subprocess.Popen(command)
        print(f'Started: {" ".join(command)}')
    except Exception as e:
        print(f'Error starting {" ".join(command)}: {e}')
        

if __name__ == "__main__":
    venv_path = os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe')
    
    redis_command = ["redis-server", "--port", REDIS_PORT]  
    
    uvicorn_command = [
        venv_path,
        "-m",
        "uvicorn",
        "chat_project.asgi:application",
        "--host", "127.0.0.1",
        "--port", MAIN_PORT,
        "--reload",
        "--lifespan", "off",
        #"--log-level", "debug"
    ]
    
    start_server(redis_command)
    start_server(uvicorn_command)