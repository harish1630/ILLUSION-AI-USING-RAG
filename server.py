#!/usr/bin/env python
"""
illusion AI - Unified Server Runner
Runs both Frontend (Next.js) and Backend (FastAPI) or allows standalone execution.

Usage:
    python server.py                 # Runs both Frontend & Backend
    python server.py --backend-only  # Runs only the FastAPI backend (Port 8000)
    python server.py --frontend-only # Runs only the Next.js frontend (Port 3000)
"""

import os
import sys
import time
import signal
import subprocess
import argparse

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Add Node to PATH if on Windows standard location
node_path = r"C:\Program Files\nodejs"
if os.path.exists(node_path) and node_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{node_path};" + os.environ.get("PATH", "")


def run_backend(host="127.0.0.1", port=8000, reload=False):
    """Runs FastAPI backend using uvicorn."""
    import importlib.util
    import uvicorn

    app_module_path = os.path.join(BACKEND_DIR, "app", "main.py")
    if not os.path.exists(app_module_path):
        raise FileNotFoundError(f"Could not locate backend app at: {app_module_path}")

    spec = importlib.util.spec_from_file_location("illusion_app_main", app_module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load backend app from {app_module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = module.app

    print(f"\n=======================================================")
    print(f"  ILLUSION AI - Backend Server Starting")
    print(f"  API Docs (Swagger): http://localhost:{port}/docs")
    print(f"  Health Check:       http://localhost:{port}/health")
    print(f"=======================================================\n")

    if reload:
        uvicorn.run("app.main:app", host=host, port=port, reload=True, app_dir=BACKEND_DIR)
    else:
        uvicorn.run(app, host=host, port=port)


def run_frontend():
    """Runs Next.js frontend development server."""
    print(f"\n=======================================================")
    print(f"  ILLUSION AI - Next.js Frontend Starting")
    print(f"  Web Interface:      http://localhost:3000")
    print(f"=======================================================\n")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    subprocess.run([npm_cmd, "run", "dev"], cwd=FRONTEND_DIR, shell=True)


def run_full_stack():
    """Orchestrates both Backend and Frontend concurrently."""
    print("\n" + "=" * 65)
    print("      ILLUSION AI - Starting Full Stack Platform")
    print("=" * 65)
    print("  • Frontend URL:    http://localhost:3000")
    print("  • Backend API:     http://localhost:8000")
    print("  • Interactive Docs: http://localhost:8000/docs")
    print("  • Health Check:    http://localhost:8000/health")
    print("=" * 65 + "\n")

    python_exe = sys.executable
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Start Backend subprocess
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]
    print("[Launcher] Starting Backend API on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=BASE_DIR)

    # Wait 2 seconds for backend to start up
    time.sleep(2)

    # Start Frontend subprocess
    frontend_cmd = [npm_cmd, "run", "dev"]
    print("[Launcher] Starting Next.js Frontend on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, shell=True)

    print("\n>>> Platform running! Press Ctrl+C to terminate both servers <<<\n")

    try:
        while True:
            time.sleep(1)
            # Check if any process terminated unexpectedly
            if backend_proc.poll() is not None:
                print("[Error] Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[Error] Frontend process terminated unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down illusion AI servers...")
    finally:
        # Graceful cleanup
        if backend_proc.poll() is None:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend_proc.kill()

        if frontend_proc.poll() is None:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)],
                    capture_output=True,
                )
            else:
                frontend_proc.terminate()
        print("[Launcher] All servers stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(description="illusion AI Unified Server")
    parser.add_argument("--backend-only", action="store_true", help="Run only the FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the Next.js frontend")
    parser.add_argument("--port", type=int, default=8000, help="Port for backend server (default: 8000)")
    args = parser.parse_args()

    if args.backend_only:
        run_backend(port=args.port)
    elif args.frontend_only:
        run_frontend()
    else:
        run_full_stack()


if __name__ == "__main__":
    main()
