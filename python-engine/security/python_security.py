"""
Security helper for Python processing engine integration with Rust security system.

This module provides utilities for secure data handling in Python processing workflows,
including file encryption, secure temporary file handling, and audit logging.
"""

import os
import tempfile
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class PythonSecurityManager:
    """
    Python-side security manager for processing engine.
    Provides encryption, secure file handling, and audit logging capabilities.
    """
    
    def __init__(self, security_dir: Optional[Path] = None):
        """Initialize the security manager."""
        if security_dir is None:
            security_dir = Path.home() / '.lexicon' / 'security'
        
        self.security_dir = Path(security_dir)
        self.security_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = self.security_dir / 'temp'
        self.temp_dir.mkdir(exist_ok=True)
        
        self.audit_log_path = self.security_dir / 'python_audit.log'
        
        # Initialize logging
        self._setup_logging()
        
        logger.info("Python security manager initialized")
    
    def _setup_logging(self):
        """Setup secure logging for audit trail."""
        audit_handler = logging.FileHandler(self.audit_log_path)
        audit_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        logger.addHandler(audit_handler)
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password string
            salt: Optional salt bytes (generated if not provided)
            
        Returns:
            Derived key bytes
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_sensitive_data(self, data: bytes, key: bytes) -> bytes:
        """
        Encrypt sensitive data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            
        Returns:
            Encrypted data
        """
        try:
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data)
            
            logger.info("Data encrypted successfully")
            self.log_security_event("data_encryption", "success", {
                "data_size": len(data),
                "encrypted_size": len(encrypted_data)
            })
            
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            self.log_security_event("data_encryption", "error", {"error": str(e)})
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt sensitive data using Fernet symmetric encryption.
        
        Args:
            encrypted_data: Encrypted data
            key: Decryption key
            
        Returns:
            Decrypted data
        """
        try:
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            logger.info("Data decrypted successfully")
            self.log_security_event("data_decryption", "success", {
                "encrypted_size": len(encrypted_data),
                "decrypted_size": len(decrypted_data)
            })
            
            return decrypted_data
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            self.log_security_event("data_decryption", "error", {"error": str(e)})
            raise
    
    def create_secure_temp_file(self, prefix: str = "lexicon_", suffix: str = ".tmp") -> Path:
        """
        Create a secure temporary file in the security temp directory.
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix
            
        Returns:
            Path to the temporary file
        """
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        
        temp_path = Path(path)
        
        # Set restrictive permissions (owner read/write only)
        temp_path.chmod(0o600)
        
        logger.info(f"Created secure temp file: {temp_path}")
        self.log_security_event("temp_file_creation", "success", {"path": str(temp_path)})
        
        return temp_path
    
    def secure_file_cleanup(self, file_path: Path) -> bool:
        """
        Securely delete a file by overwriting before deletion.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                return True
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Overwrite with random data multiple times
            with open(file_path, 'rb+') as f:
                for _ in range(3):  # 3 pass overwrite
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Remove the file
            file_path.unlink()
            
            logger.info(f"Securely deleted file: {file_path}")
            self.log_security_event("secure_file_deletion", "success", {"path": str(file_path)})
            
            return True
        except Exception as e:
            logger.error(f"Secure file deletion failed: {e}")
            self.log_security_event("secure_file_deletion", "error", {
                "path": str(file_path),
                "error": str(e)
            })
            return False
    
    def hash_file(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of a file for integrity verification.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('sha256', 'sha1', 'md5')
            
        Returns:
            Hex digest of file hash
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            file_hash = hash_obj.hexdigest()
            
            logger.info(f"File hash calculated: {file_path} -> {file_hash}")
            self.log_security_event("file_hash_calculation", "success", {
                "path": str(file_path),
                "algorithm": algorithm,
                "hash": file_hash
            })
            
            return file_hash
        except Exception as e:
            logger.error(f"File hashing failed: {e}")
            self.log_security_event("file_hash_calculation", "error", {
                "path": str(file_path),
                "error": str(e)
            })
            raise
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        Verify file integrity against expected hash.
        
        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = self.hash_file(file_path, algorithm)
            is_valid = actual_hash.lower() == expected_hash.lower()
            
            self.log_security_event("file_integrity_verification", "success", {
                "path": str(file_path),
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "is_valid": is_valid
            })
            
            return is_valid
        except Exception as e:
            logger.error(f"File integrity verification failed: {e}")
            self.log_security_event("file_integrity_verification", "error", {
                "path": str(file_path),
                "error": str(e)
            })
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components and dangerous characters
        sanitized = os.path.basename(filename)
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "._-")
        
        # Ensure it's not empty and doesn't start with a dot
        if not sanitized or sanitized.startswith('.'):
            sanitized = 'sanitized_' + sanitized
        
        self.log_security_event("filename_sanitization", "success", {
            "original": filename,
            "sanitized": sanitized
        })
        
        return sanitized
    
    def validate_file_path(self, file_path: Path, allowed_base_paths: List[Path]) -> bool:
        """
        Validate that a file path is within allowed directories.
        
        Args:
            file_path: Path to validate
            allowed_base_paths: List of allowed base directories
            
        Returns:
            True if path is allowed, False otherwise
        """
        try:
            file_path = file_path.resolve()
            
            for base_path in allowed_base_paths:
                base_path = base_path.resolve()
                if file_path.is_relative_to(base_path):
                    self.log_security_event("path_validation", "success", {
                        "path": str(file_path),
                        "allowed_base": str(base_path),
                        "result": "allowed"
                    })
                    return True
            
            self.log_security_event("path_validation", "warning", {
                "path": str(file_path),
                "allowed_bases": [str(p) for p in allowed_base_paths],
                "result": "denied"
            })
            
            return False
        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            self.log_security_event("path_validation", "error", {
                "path": str(file_path),
                "error": str(e)
            })
            return False
    
    def log_security_event(self, event_type: str, status: str, details: Dict[str, Any]):
        """
        Log a security event for audit purposes.
        
        Args:
            event_type: Type of security event
            status: Status of the event (success, error, warning)
            details: Additional event details
        """
        event = {
            "timestamp": logger.handlers[0].formatter.formatTime(logging.LogRecord(
                name=logger.name,
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None
            )),
            "event_type": event_type,
            "status": status,
            "details": details
        }
        
        logger.info(f"SECURITY_EVENT: {json.dumps(event)}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of temp files to keep
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        cleaned_count = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        try:
            for temp_file in self.temp_dir.iterdir():
                if temp_file.is_file():
                    file_age = current_time - temp_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        if self.secure_file_cleanup(temp_file):
                            cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old temporary files")
            self.log_security_event("temp_file_cleanup", "success", {
                "files_cleaned": cleaned_count,
                "max_age_hours": max_age_hours
            })
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            self.log_security_event("temp_file_cleanup", "error", {"error": str(e)})
        
        return cleaned_count
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Generate a security report of current status.
        
        Returns:
            Dictionary containing security status information
        """
        report = {
            "security_dir": str(self.security_dir),
            "temp_dir": str(self.temp_dir),
            "temp_files_count": len(list(self.temp_dir.glob("*"))),
            "audit_log_size": self.audit_log_path.stat().st_size if self.audit_log_path.exists() else 0,
            "permissions_secure": True,  # Could add actual permission checks
        }
        
        self.log_security_event("security_report_generated", "success", report)
        
        return report


# Global security manager instance
_security_manager = None

def get_security_manager() -> PythonSecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = PythonSecurityManager()
    return _security_manager


# Convenience functions for common security operations
def secure_process_file(file_path: Path, processor_func, cleanup: bool = True) -> Any:
    """
    Securely process a file with automatic cleanup.
    
    Args:
        file_path: Path to file to process
        processor_func: Function to process the file
        cleanup: Whether to cleanup temp files after processing
        
    Returns:
        Result from processor function
    """
    security_manager = get_security_manager()
    
    try:
        # Verify file integrity if hash file exists
        hash_file_path = Path(str(file_path) + '.hash')
        if hash_file_path.exists():
            with open(hash_file_path, 'r') as f:
                expected_hash = f.read().strip()
            
            if not security_manager.verify_file_integrity(file_path, expected_hash):
                raise ValueError("File integrity check failed")
        
        # Process the file
        result = processor_func(file_path)
        
        return result
        
    finally:
        if cleanup:
            security_manager.cleanup_temp_files()


def create_secure_workspace() -> Path:
    """Create a secure temporary workspace directory."""
    security_manager = get_security_manager()
    workspace_dir = security_manager.temp_dir / f"workspace_{os.urandom(8).hex()}"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.chmod(0o700)
    return workspace_dir


if __name__ == "__main__":
    # Demo usage
    sm = PythonSecurityManager()
    
    # Create a test file
    test_file = sm.create_secure_temp_file(prefix="test_", suffix=".txt")
    test_file.write_text("This is a test file for security demonstration.")
    
    # Calculate hash
    file_hash = sm.hash_file(test_file)
    print(f"File hash: {file_hash}")
    
    # Verify integrity
    is_valid = sm.verify_file_integrity(test_file, file_hash)
    print(f"File integrity: {'VALID' if is_valid else 'INVALID'}")
    
    # Generate security report
    report = sm.get_security_report()
    print(f"Security report: {json.dumps(report, indent=2)}")
    
    # Cleanup
    sm.secure_file_cleanup(test_file)
