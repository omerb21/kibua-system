import subprocess
import os
import threading

def run_flask():
    os.system("python run.py")

def run_react():
    os.chdir("client-ui")
    # נוודא שהפרויקט כבר עשה npm install
    os.system("npm run dev")

if __name__ == "__main__":
    # Flask runs in a thread so the script doesn't block
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_react()  # Will run in main thread
