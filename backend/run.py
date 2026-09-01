"""
PANAGAH Backend Server Runner.

Usage:
    python run.py [--port 8000] [--host 127.0.0.1] [--no-reload]
"""

import os
import sys
import argparse
import uvicorn

# Ensure the backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set working directory to backend
os.chdir(BASE_DIR)


def main():
    parser = argparse.ArgumentParser(description="Start the Panagah FastAPI backend server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on file changes")
    
    args = parser.parse_args()
    reload = not args.no_reload

    print("\n" + "=" * 60)
    print("  PANAGAH (پناگاہ) API — Humanitarian Shelter Engine")
    print("=" * 60)
    print(f"  > API Server : http://{args.host}:{args.port}")
    print(f"  > Swagger UI : http://{args.host}:{args.port}/docs")
    print(f"  > ReDoc Docs : http://{args.host}:{args.port}/redoc")
    print(f"  > Health Check: http://{args.host}:{args.port}/health")
    print(f"  > Auto-Reload: {'Enabled' if reload else 'Disabled'}")
    print("=" * 60 + "\n")

    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=reload,
            reload_dirs=[BASE_DIR] if reload else None,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n[Panagah] Server shutdown requested by user. Goodbye!\n")


if __name__ == "__main__":
    main()
