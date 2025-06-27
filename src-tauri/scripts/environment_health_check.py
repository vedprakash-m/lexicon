#!/usr/bin/env python3
"""
Environment Health Check Script
Validates Python environment and reports system information
"""

import sys
import json
import platform
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check Python version compatibility"""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    is_compatible = version_info >= (3, 8)
    
    return {
        "version": version_str,
        "compatible": is_compatible,
        "full_version": sys.version
    }


def check_required_modules():
    """Check if required modules are available"""
    required_modules = [
        "requests", "beautifulsoup4", "lxml", "nltk", "chardet",
        "tqdm", "click", "pydantic", "loguru"
    ]
    
    module_status = {}
    for module in required_modules:
        try:
            # Try to import or find the module
            if module == "beautifulsoup4":
                import bs4
                module_status[module] = {"available": True, "version": getattr(bs4, "__version__", "unknown")}
            elif module == "PyMuPDF":
                import fitz
                module_status[module] = {"available": True, "version": getattr(fitz, "__version__", "unknown")}
            else:
                spec = importlib.util.find_spec(module)
                if spec is not None:
                    mod = importlib.import_module(module)
                    version = getattr(mod, "__version__", "unknown")
                    module_status[module] = {"available": True, "version": version}
                else:
                    module_status[module] = {"available": False, "version": None}
        except ImportError:
            module_status[module] = {"available": False, "version": None}
    
    return module_status


def check_system_info():
    """Gather system information"""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_executable": sys.executable,
        "python_path": sys.path[:3]  # First 3 paths for brevity
    }


def check_virtual_environment():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    venv_info = {
        "in_virtual_env": in_venv,
        "prefix": sys.prefix,
    }
    
    if in_venv:
        venv_info["base_prefix"] = getattr(sys, 'base_prefix', getattr(sys, 'real_prefix', None))
    
    return venv_info


def check_pip_availability():
    """Check if pip is available and working"""
    try:
        import pip
        pip_available = True
        pip_version = getattr(pip, "__version__", "unknown")
    except ImportError:
        pip_available = False
        pip_version = None
    
    # Alternative check via subprocess
    if not pip_available:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                pip_available = True
                pip_version = result.stdout.strip().split()[1] if "pip" in result.stdout else "unknown"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
    
    return {
        "available": pip_available,
        "version": pip_version
    }


def main():
    """Main health check function"""
    try:
        health_report = {
            "status": "healthy",
            "timestamp": str(sys.version_info),
            "python": check_python_version(),
            "modules": check_required_modules(),
            "system": check_system_info(),
            "virtual_env": check_virtual_environment(),
            "pip": check_pip_availability()
        }
        
        # Determine overall health status
        python_ok = health_report["python"]["compatible"]
        pip_ok = health_report["pip"]["available"]
        
        if not python_ok:
            health_report["status"] = "critical"
            health_report["issues"] = ["Python version incompatible (requires 3.8+)"]
        elif not pip_ok:
            health_report["status"] = "warning"
            health_report["issues"] = ["pip not available - dependency installation may fail"]
        
        # Count missing modules
        missing_modules = [
            name for name, info in health_report["modules"].items() 
            if not info["available"]
        ]
        
        if missing_modules:
            if health_report["status"] == "healthy":
                health_report["status"] = "warning"
                health_report["issues"] = []
            health_report["issues"].extend([f"Missing module: {mod}" for mod in missing_modules])
        
        print(json.dumps(health_report, indent=2))
        
    except Exception as e:
        error_report = {
            "status": "error",
            "error": str(e),
            "python_executable": sys.executable,
            "python_version": sys.version
        }
        print(json.dumps(error_report, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
