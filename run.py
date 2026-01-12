import uvicorn
import os
import threading
import time
import sys

# Add the current directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_fastapi():
    print("Starting FastAPI Backend on port 8000...")
    # Note: reload=True can be unstable when run in a background thread.
    uvicorn.run("app.backend.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

def run_flask():
    print("Starting Flask Frontend on port 5000...")
    # Delay slightly to let FastAPI start
    time.sleep(2)
    from app.frontend import create_app
    app = create_app()
    # debug=True enables auto-refresh for templates and css
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    # Create threads for both services
    api_thread = threading.Thread(target=run_fastapi)
    flask_thread = threading.Thread(target=run_flask)
    
    api_thread.start()
    flask_thread.start()
    
    api_thread.join()
    flask_thread.join()
