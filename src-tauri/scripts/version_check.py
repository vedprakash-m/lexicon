#!/usr/bin/env python3
"""
Version Check Script
Simple version checking and validation
"""

import sys
import json
import platform


def check_python_version():
    """Check Python version and compatibility"""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    # Check if version meets minimum requirements (3.8+)
    is_compatible = version_info >= (3, 8)
    
    return {
        "version": version_str,
        "major": version_info.major,
        "minor": version_info.minor,
        "micro": version_info.micro,
        "compatible": is_compatible,
        "minimum_required": "3.8.0",
        "full_version": sys.version,
        "executable": sys.executable
    }


def check_platform_info():
    """Get platform information"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform()
    }


def main():
    """Main version check function"""
    try:
        version_info = {
            "python": check_python_version(),
            "platform": check_platform_info(),
            "timestamp": str(sys.version_info)
        }
        
        print(json.dumps(version_info, indent=2))
        
        # Exit with error code if Python version is incompatible
        if not version_info["python"]["compatible"]:
            sys.exit(1)
            
    except Exception as e:
        error_info = {
            "error": str(e),
            "python_executable": sys.executable
        }
        print(json.dumps(error_info, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
