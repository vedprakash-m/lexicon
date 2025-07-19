"""
Production deployment preparation script for Lexicon RAG Dataset Preparation Tool.

This script handles:
- Environment validation
- Dependency checks  
- Configuration validation
- Security setup
- Performance optimization
- Deployment package creation
- Health checks
- Rollback preparation

Run with: python deploy_prep.py
"""

import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import logging
import hashlib
import tarfile
import zipfile
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentError(Exception):
    """Custom exception for deployment errors."""
    pass

class EnvironmentValidator:
    """Validates deployment environment."""
    
    def __init__(self):
        """Initialize environment validator."""
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
    
    def check_system_requirements(self) -> bool:
        """Check system requirements."""
        logger.info("Checking system requirements...")
        
        # Check OS
        supported_os = ['Darwin', 'Linux', 'Windows']  # macOS, Linux, Windows
        current_os = platform.system()
        
        if current_os not in supported_os:
            logger.error(f"Unsupported operating system: {current_os}")
            self.checks_failed += 1
            return False
        
        logger.info(f"✓ Operating system: {current_os}")
        self.checks_passed += 1
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 9):
            logger.error(f"Python 3.9+ required, found {python_version.major}.{python_version.minor}")
            self.checks_failed += 1
            return False
        
        logger.info(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        self.checks_passed += 1
        
        # Check available memory
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if memory_gb < 4:
                logger.warning(f"Low memory: {memory_gb:.1f}GB (recommended: 8GB+)")
                self.warnings.append("Low system memory")
            else:
                logger.info(f"✓ System memory: {memory_gb:.1f}GB")
                self.checks_passed += 1
        except ImportError:
            logger.warning("Could not check system memory (psutil not installed)")
            self.warnings.append("Memory check skipped")
        
        # Check disk space
        try:
            disk_usage = shutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 10:
                logger.error(f"Insufficient disk space: {free_gb:.1f}GB (minimum: 10GB)")
                self.checks_failed += 1
                return False
            else:
                logger.info(f"✓ Available disk space: {free_gb:.1f}GB")
                self.checks_passed += 1
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            self.warnings.append("Disk space check failed")
        
        return True
    
    def check_dependencies(self, requirements_file: str) -> bool:
        """Check Python dependencies."""
        logger.info("Checking Python dependencies...")
        
        requirements_path = Path(requirements_file)
        if not requirements_path.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            self.checks_failed += 1
            return False
        
        # Check if pip is available (try both pip and pip3)
        pip_commands = ['pip', 'pip3']
        pip_found = False
        
        for pip_cmd in pip_commands:
            try:
                result = subprocess.run([pip_cmd, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✓ {pip_cmd} available: {result.stdout.strip()}")
                    self.checks_passed += 1
                    pip_found = True
                    break
            except FileNotFoundError:
                continue
        
        if not pip_found:
            # Try virtual environment pip
            venv_pip = str(Path.cwd() / '.venv' / 'bin' / 'pip')
            try:
                result = subprocess.run([venv_pip, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✓ Virtual environment pip available: {result.stdout.strip()}")
                    self.checks_passed += 1
                    pip_found = True
            except (FileNotFoundError, subprocess.SubprocessError):
                pass
        
        if not pip_found:
            logger.error("pip not available")
            self.checks_failed += 1
            return False
        
        # Check requirements
        try:
            result = subprocess.run(
                ['pip', 'check'], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("Dependency conflicts detected:")
                logger.warning(result.stdout)
                self.warnings.append("Dependency conflicts")
            else:
                logger.info("✓ No dependency conflicts")
                self.checks_passed += 1
                
        except Exception as e:
            logger.warning(f"Could not check dependencies: {e}")
            self.warnings.append("Dependency check failed")
        
        return True
    
    def check_rust_toolchain(self) -> bool:
        """Check Rust toolchain for Tauri."""
        logger.info("Checking Rust toolchain...")
        
        # Check Rust
        try:
            result = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Rust compiler not available")
                self.checks_failed += 1
                return False
            
            logger.info(f"✓ Rust compiler: {result.stdout.strip()}")
            self.checks_passed += 1
        except FileNotFoundError:
            logger.error("Rust not found in PATH")
            self.checks_failed += 1
            return False
        
        # Check Cargo
        try:
            result = subprocess.run(['cargo', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Cargo not available")
                self.checks_failed += 1
                return False
            
            logger.info(f"✓ Cargo: {result.stdout.strip()}")
            self.checks_passed += 1
        except FileNotFoundError:
            logger.error("Cargo not found in PATH")
            self.checks_failed += 1
            return False
        
        return True
    
    def check_nodejs(self) -> bool:
        """Check Node.js for frontend build."""
        logger.info("Checking Node.js environment...")
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Node.js not available")
                self.checks_failed += 1
                return False
            
            version = result.stdout.strip()
            logger.info(f"✓ Node.js: {version}")
            self.checks_passed += 1
        except FileNotFoundError:
            logger.error("Node.js not found in PATH")
            self.checks_failed += 1
            return False
        
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("npm not available")
                self.checks_failed += 1
                return False
            
            version = result.stdout.strip()
            logger.info(f"✓ npm: {version}")
            self.checks_passed += 1
        except FileNotFoundError:
            logger.error("npm not found in PATH")
            self.checks_failed += 1
            return False
        
        return True
    
    def validate_environment(self, requirements_file: str) -> bool:
        """Run all environment validations."""
        logger.info("Starting environment validation...")
        
        all_passed = True
        
        all_passed &= self.check_system_requirements()
        all_passed &= self.check_dependencies(requirements_file)
        all_passed &= self.check_rust_toolchain()
        all_passed &= self.check_nodejs()
        
        # Summary
        logger.info(f"Environment validation complete:")
        logger.info(f"  Checks passed: {self.checks_passed}")
        logger.info(f"  Checks failed: {self.checks_failed}")
        logger.info(f"  Warnings: {len(self.warnings)}")
        
        if self.warnings:
            logger.warning("Warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        return all_passed

class ConfigurationValidator:
    """Validates deployment configuration."""
    
    def __init__(self, project_root: Path):
        """Initialize configuration validator."""
        self.project_root = project_root
        self.required_files = [
            'package.json',
            'src-tauri/Cargo.toml',
            'src-tauri/tauri.conf.json',
            'python-engine/requirements.txt'
        ]
    
    def check_required_files(self) -> bool:
        """Check if all required files exist."""
        logger.info("Checking required configuration files...")
        
        all_exist = True
        
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.error(f"Required file missing: {file_path}")
                all_exist = False
            else:
                logger.info(f"✓ Found: {file_path}")
        
        return all_exist
    
    def validate_tauri_config(self) -> bool:
        """Validate Tauri configuration."""
        logger.info("Validating Tauri configuration...")
        
        config_path = self.project_root / 'src-tauri' / 'tauri.conf.json'
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required fields
            required_fields = ['productName', 'version', 'identifier']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field in tauri.conf.json: {field}")
                    return False
            
            # Check bundle configuration
            if 'bundle' not in config:
                logger.error("Missing bundle configuration in tauri.conf.json")
                return False
            
            # Bundle identifier is optional in newer Tauri versions
            logger.info("✓ Tauri configuration valid")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Tauri config: {e}")
            return False
    
    def validate_package_json(self) -> bool:
        """Validate package.json."""
        logger.info("Validating package.json...")
        
        package_path = self.project_root / 'package.json'
        
        try:
            with open(package_path, 'r') as f:
                package_json = json.load(f)
            
            # Check required fields
            required_fields = ['name', 'version', 'scripts']
            for field in required_fields:
                if field not in package_json:
                    logger.error(f"Missing required field in package.json: {field}")
                    return False
            
            # Check required scripts
            scripts = package_json.get('scripts', {})
            required_scripts = ['build', 'tauri']
            for script in required_scripts:
                if script not in scripts:
                    logger.error(f"Missing required script in package.json: {script}")
                    return False
            
            logger.info("✓ package.json valid")
            return True
            
        except Exception as e:
            logger.error(f"Error validating package.json: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """Run all configuration validations."""
        logger.info("Starting configuration validation...")
        
        all_valid = True
        
        all_valid &= self.check_required_files()
        all_valid &= self.validate_tauri_config()
        all_valid &= self.validate_package_json()
        
        return all_valid

class SecuritySetup:
    """Handles security setup for production."""
    
    def __init__(self, project_root: Path):
        """Initialize security setup."""
        self.project_root = project_root
    
    def setup_environment_variables(self) -> bool:
        """Setup production environment variables."""
        logger.info("Setting up production environment variables...")
        
        env_template = {
            'LEXICON_ENV': 'production',
            'LEXICON_LOG_LEVEL': 'info',
            'LEXICON_SECURITY_ENABLED': 'true',
            'LEXICON_ENCRYPTION_KEY': 'generate_strong_key_here',
            'LEXICON_SESSION_SECRET': 'generate_session_secret_here',
            'LEXICON_BACKUP_ENABLED': 'true',
            'LEXICON_TELEMETRY_ENABLED': 'true'
        }
        
        env_file = self.project_root / '.env.production'
        
        if not env_file.exists():
            env_content = '\n'.join([f'{key}={value}' for key, value in env_template.items()])
            env_file.write_text(env_content)
            logger.info(f"✓ Created production environment template: {env_file}")
        else:
            logger.info(f"✓ Production environment file exists: {env_file}")
        
        # Create example file
        env_example = self.project_root / '.env.production.example'
        if not env_example.exists():
            env_content = '\n'.join([f'{key}={value}' for key, value in env_template.items()])
            env_example.write_text(env_content)
        
        return True
    
    def generate_security_keys(self) -> Dict[str, str]:
        """Generate security keys for production."""
        logger.info("Generating security keys...")
        
        import secrets
        import string
        
        # Generate encryption key (32 bytes, base64 encoded)
        encryption_key = secrets.token_urlsafe(32)
        
        # Generate session secret (64 characters)
        session_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
        
        # Generate API key (32 characters)
        api_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        keys = {
            'encryption_key': encryption_key,
            'session_secret': session_secret,
            'api_key': api_key
        }
        
        logger.info("✓ Security keys generated")
        return keys
    
    def create_security_config(self) -> bool:
        """Create security configuration file."""
        logger.info("Creating security configuration...")
        
        security_config = {
            'encryption': {
                'algorithm': 'AES-256-GCM',
                'key_derivation': 'PBKDF2',
                'iterations': 100000
            },
            'authentication': {
                'session_timeout': 3600,  # 1 hour
                'max_login_attempts': 5,
                'lockout_duration': 900  # 15 minutes
            },
            'access_control': {
                'default_permissions': ['read'],
                'admin_permissions': ['read', 'write', 'delete', 'admin'],
                'user_permissions': ['read', 'write']
            },
            'audit': {
                'log_file': 'logs/audit.log',
                'max_size_mb': 100,
                'backup_count': 5
            }
        }
        
        config_file = self.project_root / 'security_config.json'
        config_file.write_text(json.dumps(security_config, indent=2))
        
        logger.info(f"✓ Security configuration created: {config_file}")
        return True

class PerformanceOptimizer:
    """Handles performance optimization for production."""
    
    def __init__(self, project_root: Path):
        """Initialize performance optimizer."""
        self.project_root = project_root
    
    def optimize_python_dependencies(self) -> bool:
        """Optimize Python dependencies."""
        logger.info("Optimizing Python dependencies...")
        
        # Create optimized requirements
        requirements_file = self.project_root / 'python-engine' / 'requirements.txt'
        optimized_file = self.project_root / 'python-engine' / 'requirements.prod.txt'
        
        if requirements_file.exists():
            # Read current requirements
            requirements = requirements_file.read_text().splitlines()
            
            # Add production-specific packages
            prod_packages = [
                'gunicorn>=20.1.0',  # Production WSGI server
                'psutil>=5.8.0',     # System monitoring
                'prometheus-client>=0.14.0'  # Metrics
            ]
            
            # Combine and deduplicate
            all_requirements = list(set(requirements + prod_packages))
            
            optimized_file.write_text('\n'.join(sorted(all_requirements)))
            logger.info(f"✓ Created optimized requirements: {optimized_file}")
        
        return True
    
    def optimize_frontend_build(self) -> bool:
        """Optimize frontend build configuration."""
        logger.info("Optimizing frontend build...")
        
        # Check if vite.config.ts exists
        vite_config = self.project_root / 'vite.config.ts'
        if not vite_config.exists():
            logger.warning("vite.config.ts not found, skipping frontend optimization")
            return True
        
        # Read current config
        config_content = vite_config.read_text()
        
        # Check if build optimization is already present
        if 'build:' in config_content and 'minify:' in config_content:
            logger.info("✓ Frontend build already optimized")
            return True
        
        # Add optimization suggestions to a separate file
        optimization_notes = self.project_root / 'OPTIMIZATION_NOTES.md'
        notes_content = """# Production Optimization Notes

## Frontend Build Optimization
Add the following to your vite.config.ts:

```typescript
export default defineConfig({
  build: {
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['lodash', 'date-fns']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  define: {
    __DEV__: JSON.stringify(false)
  }
})
```

## Tauri Bundle Optimization
Consider enabling these in tauri.conf.json:

```json
{
  "bundle": {
    "resources": ["resources/*"],
    "externalBin": [],
    "copyright": "",
    "category": "Productivity",
    "shortDescription": "",
    "longDescription": "",
    "deb": {
      "depends": []
    },
    "macOS": {
      "frameworks": [],
      "minimumSystemVersion": "10.13",
      "exceptionDomain": ""
    },
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  }
}
```
"""
        
        optimization_notes.write_text(notes_content)
        logger.info(f"✓ Created optimization notes: {optimization_notes}")
        
        return True

class DeploymentPackager:
    """Creates deployment packages."""
    
    def __init__(self, project_root: Path):
        """Initialize deployment packager."""
        self.project_root = project_root
        self.build_dir = project_root / 'dist'
        self.package_dir = project_root / 'deployment-packages'
    
    def clean_build_directory(self) -> bool:
        """Clean build directory."""
        logger.info("Cleaning build directory...")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        self.build_dir.mkdir(exist_ok=True)
        logger.info(f"✓ Build directory cleaned: {self.build_dir}")
        
        return True
    
    def build_application(self) -> bool:
        """Build the application."""
        logger.info("Building application...")
        
        # Install dependencies
        logger.info("Installing npm dependencies...")
        result = subprocess.run(['npm', 'install'], cwd=self.project_root, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"npm install failed: {result.stderr}")
            return False
        
        # Build frontend
        logger.info("Building frontend...")
        result = subprocess.run(['npm', 'run', 'build'], cwd=self.project_root, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Frontend build failed: {result.stderr}")
            return False
        
        # Build Tauri application
        logger.info("Building Tauri application...")
        result = subprocess.run(['npm', 'run', 'tauri', 'build'], cwd=self.project_root, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Tauri build failed: {result.stderr}")
            return False
        
        logger.info("✓ Application built successfully")
        return True
    
    def create_deployment_package(self) -> str:
        """Create deployment package."""
        logger.info("Creating deployment package...")
        
        self.package_dir.mkdir(exist_ok=True)
        
        # Create package name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        package_name = f"lexicon_deployment_{timestamp}"
        
        # Determine package format based on platform
        current_os = platform.system()
        if current_os == 'Windows':
            package_file = self.package_dir / f"{package_name}.zip"
            self.create_zip_package(package_file)
        else:
            package_file = self.package_dir / f"{package_name}.tar.gz"
            self.create_tar_package(package_file)
        
        logger.info(f"✓ Deployment package created: {package_file}")
        return str(package_file)
    
    def create_zip_package(self, package_file: Path):
        """Create ZIP deployment package."""
        with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            self.add_files_to_archive(zf.write)
    
    def create_tar_package(self, package_file: Path):
        """Create TAR.GZ deployment package."""
        with tarfile.open(package_file, 'w:gz') as tf:
            self.add_files_to_archive(lambda src, dst: tf.add(src, arcname=dst))
    
    def add_files_to_archive(self, add_func):
        """Add files to archive using the provided function."""
        # Add built application
        src_tauri_target = self.project_root / 'src-tauri' / 'target' / 'release'
        if src_tauri_target.exists():
            for item in src_tauri_target.iterdir():
                if item.is_file() and not item.name.endswith('.pdb'):
                    add_func(str(item), f"bin/{item.name}")
        
        # Add Python engine
        python_engine = self.project_root / 'python-engine'
        if python_engine.exists():
            for item in python_engine.rglob('*'):
                if item.is_file() and not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(self.project_root)
                    add_func(str(item), str(rel_path))
        
        # Add configuration files
        config_files = [
            '.env.production.example',
            'security_config.json',
            'OPTIMIZATION_NOTES.md'
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                add_func(str(file_path), config_file)
    
    def generate_checksum(self, package_file: str) -> str:
        """Generate checksum for package file."""
        logger.info("Generating package checksum...")
        
        sha256_hash = hashlib.sha256()
        with open(package_file, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        checksum = sha256_hash.hexdigest()
        
        # Save checksum to file
        checksum_file = Path(package_file).with_suffix('.sha256')
        checksum_file.write_text(f"{checksum}  {Path(package_file).name}\n")
        
        logger.info(f"✓ Checksum generated: {checksum}")
        return checksum

class HealthChecker:
    """Performs health checks on the deployed application."""
    
    def __init__(self, project_root: Path):
        """Initialize health checker."""
        self.project_root = project_root
    
    def check_file_integrity(self) -> bool:
        """Check integrity of critical files."""
        logger.info("Checking file integrity...")
        
        critical_files = [
            'package.json',
            'src-tauri/Cargo.toml',
            'src-tauri/tauri.conf.json'
        ]
        
        all_good = True
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                logger.error(f"Critical file missing: {file_path}")
                all_good = False
            else:
                # Check if file is readable
                try:
                    content = full_path.read_text()
                    if not content.strip():
                        logger.error(f"Critical file is empty: {file_path}")
                        all_good = False
                    else:
                        logger.info(f"✓ {file_path}")
                except Exception as e:
                    logger.error(f"Cannot read critical file {file_path}: {e}")
                    all_good = False
        
        return all_good
    
    def run_smoke_tests(self) -> bool:
        """Run smoke tests."""
        logger.info("Running smoke tests...")
        
        # Test Python imports
        python_tests = [
            "import json",
            "import sys",
            "import pathlib",
            "import logging"
        ]
        
        all_passed = True
        
        for test in python_tests:
            try:
                exec(test)
                logger.info(f"✓ Python test passed: {test}")
            except Exception as e:
                logger.error(f"Python test failed: {test} - {e}")
                all_passed = False
        
        return all_passed

class DeploymentPreparation:
    """Main deployment preparation coordinator."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize deployment preparation."""
        self.project_root = project_root or Path.cwd()
        
        # Initialize components
        self.env_validator = EnvironmentValidator()
        self.config_validator = ConfigurationValidator(self.project_root)
        self.security_setup = SecuritySetup(self.project_root)
        self.optimizer = PerformanceOptimizer(self.project_root)
        self.packager = DeploymentPackager(self.project_root)
        self.health_checker = HealthChecker(self.project_root)
        
        logger.info(f"Deployment preparation initialized for: {self.project_root}")
    
    def prepare_for_deployment(self) -> Dict[str, Any]:
        """Run complete deployment preparation."""
        logger.info("Starting deployment preparation...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'steps': {},
            'success': True,
            'errors': [],
            'warnings': []
        }
        
        steps = [
            ('environment_validation', self.validate_environment),
            ('configuration_validation', self.validate_configuration),
            ('security_setup', self.setup_security),
            ('performance_optimization', self.optimize_performance),
            ('health_checks', self.run_health_checks)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Running step: {step_name}")
            
            try:
                step_result = step_func()
                results['steps'][step_name] = {
                    'success': step_result,
                    'timestamp': datetime.now().isoformat()
                }
                
                if not step_result:
                    results['success'] = False
                    results['errors'].append(f"Step failed: {step_name}")
                    
            except Exception as e:
                logger.error(f"Step {step_name} failed with exception: {e}")
                results['steps'][step_name] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['success'] = False
                results['errors'].append(f"Step {step_name} failed: {e}")
        
        # Add warnings from environment validator
        if self.env_validator.warnings:
            results['warnings'].extend(self.env_validator.warnings)
        
        # Save results
        results_file = self.project_root / 'deployment_preparation_results.json'
        results_file.write_text(json.dumps(results, indent=2))
        
        # Generate summary
        self.generate_deployment_summary(results)
        
        logger.info(f"Deployment preparation completed. Success: {results['success']}")
        return results
    
    def validate_environment(self) -> bool:
        """Validate deployment environment."""
        requirements_file = str(self.project_root / 'python-engine' / 'requirements.txt')
        return self.env_validator.validate_environment(requirements_file)
    
    def validate_configuration(self) -> bool:
        """Validate deployment configuration."""
        return self.config_validator.validate_configuration()
    
    def setup_security(self) -> bool:
        """Setup security for production."""
        all_success = True
        
        all_success &= self.security_setup.setup_environment_variables()
        all_success &= self.security_setup.create_security_config()
        
        # Generate and display security keys
        keys = self.security_setup.generate_security_keys()
        logger.info("Generated security keys (store securely):")
        for key_name, key_value in keys.items():
            logger.info(f"  {key_name}: {key_value[:8]}...{key_value[-8:]}")
        
        return all_success
    
    def optimize_performance(self) -> bool:
        """Optimize performance for production."""
        all_success = True
        
        all_success &= self.optimizer.optimize_python_dependencies()
        all_success &= self.optimizer.optimize_frontend_build()
        
        return all_success
    
    def run_health_checks(self) -> bool:
        """Run health checks."""
        all_success = True
        
        all_success &= self.health_checker.check_file_integrity()
        all_success &= self.health_checker.run_smoke_tests()
        
        return all_success
    
    def create_deployment_package(self) -> Optional[str]:
        """Create deployment package."""
        logger.info("Creating deployment package...")
        
        try:
            # Clean and build
            if not self.packager.clean_build_directory():
                return None
            
            if not self.packager.build_application():
                return None
            
            # Create package
            package_file = self.packager.create_deployment_package()
            
            # Generate checksum
            checksum = self.packager.generate_checksum(package_file)
            
            logger.info(f"Deployment package created: {package_file}")
            logger.info(f"Package checksum: {checksum}")
            
            return package_file
            
        except Exception as e:
            logger.error(f"Failed to create deployment package: {e}")
            return None
    
    def generate_deployment_summary(self, results: Dict[str, Any]):
        """Generate deployment summary report."""
        summary_lines = []
        summary_lines.append("LEXICON DEPLOYMENT PREPARATION SUMMARY")
        summary_lines.append("=" * 50)
        summary_lines.append("")
        
        summary_lines.append(f"Preparation Time: {results['timestamp']}")
        summary_lines.append(f"Project Root: {results['project_root']}")
        summary_lines.append(f"Overall Success: {results['success']}")
        summary_lines.append("")
        
        summary_lines.append("STEP RESULTS:")
        for step_name, step_result in results['steps'].items():
            status = "✓ PASS" if step_result['success'] else "✗ FAIL"
            summary_lines.append(f"  {step_name}: {status}")
        
        if results['errors']:
            summary_lines.append("")
            summary_lines.append("ERRORS:")
            for error in results['errors']:
                summary_lines.append(f"  - {error}")
        
        if results['warnings']:
            summary_lines.append("")
            summary_lines.append("WARNINGS:")
            for warning in results['warnings']:
                summary_lines.append(f"  - {warning}")
        
        summary_lines.append("")
        summary_lines.append("NEXT STEPS:")
        if results['success']:
            summary_lines.append("  1. Review generated configuration files")
            summary_lines.append("  2. Update security keys in production environment")
            summary_lines.append("  3. Run deployment package creation")
            summary_lines.append("  4. Deploy to production environment")
            summary_lines.append("  5. Run post-deployment health checks")
        else:
            summary_lines.append("  1. Fix all errors listed above")
            summary_lines.append("  2. Re-run deployment preparation")
            summary_lines.append("  3. Address any warnings if needed")
        
        summary_lines.append("")
        summary_lines.append("=" * 50)
        
        summary_content = "\n".join(summary_lines)
        
        # Save summary
        summary_file = self.project_root / 'DEPLOYMENT_SUMMARY.md'
        summary_file.write_text(summary_content)
        
        # Print to console
        print(summary_content)
        
        logger.info(f"Deployment summary saved to: {summary_file}")

def main():
    """Main function to run deployment preparation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lexicon Deployment Preparation')
    parser.add_argument('--project-root', type=str, help='Project root directory')
    parser.add_argument('--create-package', action='store_true', help='Create deployment package')
    parser.add_argument('--skip-build', action='store_true', help='Skip build step')
    
    args = parser.parse_args()
    
    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path.cwd()
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    # Initialize deployment preparation
    deployment_prep = DeploymentPreparation(project_root)
    
    try:
        # Run preparation
        results = deployment_prep.prepare_for_deployment()
        
        # Create deployment package if requested and preparation was successful
        if args.create_package and results['success'] and not args.skip_build:
            package_file = deployment_prep.create_deployment_package()
            if package_file:
                print(f"\nDeployment package created: {package_file}")
            else:
                print("\nFailed to create deployment package")
                sys.exit(1)
        
        # Exit with appropriate code
        if results['success']:
            print("\n✓ Deployment preparation completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Deployment preparation failed. Check errors above.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Deployment preparation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
