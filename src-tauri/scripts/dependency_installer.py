#!/usr/bin/env python3
"""
Dependency Installer Script
Manages Python package installation with error handling and progress reporting
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path


def install_packages(packages, requirements_file=None, upgrade=False, user_install=False):
    """
    Install Python packages using pip
    
    Args:
        packages: List of package names to install
        requirements_file: Path to requirements.txt file
        upgrade: Whether to upgrade existing packages
        user_install: Whether to install in user directory
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        
        if user_install:
            cmd.append("--user")
        
        # Add progress and verbosity flags
        cmd.extend(["--progress-bar", "off", "-v"])
        
        if requirements_file:
            cmd.extend(["-r", requirements_file])
        else:
            cmd.extend(packages)
        
        # Run installation
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Installation timed out after 5 minutes",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(cmd) if 'cmd' in locals() else "unknown"
        }


def check_package_installation(packages):
    """Check if packages are properly installed"""
    import importlib.util
    
    results = {}
    for package in packages:
        try:
            # Handle package name mappings
            import_name = package
            if package == "beautifulsoup4":
                import_name = "bs4"
            elif package == "PyMuPDF":
                import_name = "fitz"
            elif package == "python-dateutil":
                import_name = "dateutil"
            
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                mod = importlib.import_module(import_name)
                version = getattr(mod, "__version__", "unknown")
                results[package] = {"installed": True, "version": version}
            else:
                results[package] = {"installed": False, "version": None}
        except ImportError:
            results[package] = {"installed": False, "version": None}
    
    return results


def create_requirements_content():
    """Create requirements.txt content for Lexicon"""
    requirements = [
        "requests==2.32.3",
        "beautifulsoup4==4.12.3",
        "lxml==5.2.2",
        "nltk==3.8.1",
        "chardet==5.2.0",
        "tqdm==4.66.4",
        "click==8.1.7",
        "pydantic==2.8.2",
        "loguru==0.7.2",
        "PyMuPDF==1.24.5",
        "pdfplumber==0.11.1",
        "python-dateutil==2.9.0",
        "ftfy==6.2.0",
        "langdetect==1.0.9"
    ]
    return "\n".join(requirements)


def main():
    """Main installation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Install Python dependencies for Lexicon")
    parser.add_argument("--packages", nargs="*", help="Specific packages to install")
    parser.add_argument("--requirements", help="Path to requirements file")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade existing packages")
    parser.add_argument("--user", action="store_true", help="Install in user directory")
    parser.add_argument("--check-only", action="store_true", help="Only check installation status")
    parser.add_argument("--install-core", action="store_true", help="Install core Lexicon dependencies")
    
    args = parser.parse_args()
    
    try:
        if args.check_only:
            packages_to_check = args.packages or [
                "requests", "beautifulsoup4", "lxml", "nltk", "chardet",
                "tqdm", "click", "pydantic", "loguru", "PyMuPDF"
            ]
            results = check_package_installation(packages_to_check)
            print(json.dumps({"status": "checked", "packages": results}, indent=2))
            return
        
        if args.install_core:
            # Create temporary requirements file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(create_requirements_content())
                temp_requirements = f.name
            
            try:
                result = install_packages([], requirements_file=temp_requirements, 
                                        upgrade=args.upgrade, user_install=args.user)
                
                if result["success"]:
                    # Verify installation
                    core_packages = [
                        "requests", "beautifulsoup4", "lxml", "nltk", "chardet",
                        "tqdm", "click", "pydantic", "loguru", "PyMuPDF"
                    ]
                    verification = check_package_installation(core_packages)
                    result["verification"] = verification
                
                print(json.dumps(result, indent=2))
                
            finally:
                # Clean up temporary file
                Path(temp_requirements).unlink(missing_ok=True)
        
        elif args.packages:
            result = install_packages(args.packages, requirements_file=args.requirements,
                                    upgrade=args.upgrade, user_install=args.user)
            
            if result["success"] and args.packages:
                verification = check_package_installation(args.packages)
                result["verification"] = verification
            
            print(json.dumps(result, indent=2))
        
        else:
            print(json.dumps({
                "error": "No packages specified. Use --packages, --requirements, or --install-core"
            }, indent=2))
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Installation script failed: {str(e)}"
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
