"""
Security utilities for Affectra application.
Provides functions for secure communication and data protection.
"""

import os
import base64
import hashlib
import hmac
import time
from cryptography.fernet import Fernet

# Generate a secure API key or use existing one
def get_api_key():
    """Get the API key for secure client-server communication."""
    api_key = os.environ.get('AFFECTRA_API_KEY')
    if not api_key:
        # Default development key (in production, use environment variable)
        api_key = "K8HJ2L3K4J2H3K4J2H3K4J2H3K4J2H3K4"
    return api_key

# Function to generate a secure signature for requests
def generate_signature(data, api_key):
    """
    Generate a HMAC signature for the given data.
    
    Args:
        data: The data to sign (dictionary)
        api_key: The API key to use for signing
        
    Returns:
        String containing the signature
    """
    # Convert data to string and add timestamp
    data_str = str(data) + str(int(time.time()))
    
    # Create signature
    signature = hmac.new(
        api_key.encode(),
        data_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# Function to verify if a request is valid
def verify_signature(data, signature, api_key, max_age=300):
    """
    Verify the signature of a request.
    
    Args:
        data: The data that was signed
        signature: The signature to verify
        api_key: The API key to use for verification
        max_age: Maximum age of the signature in seconds
        
    Returns:
        Boolean indicating if the signature is valid
    """
    # Extract timestamp
    if 'timestamp' not in data:
        return False
    
    # Check if the request is too old
    request_time = data['timestamp']
    current_time = time.time()
    if current_time - request_time > max_age:
        return False
    
    # Generate signature for comparison
    expected_signature = generate_signature(data, api_key)
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

# Simple encryption/decryption for sensitive data
class DataEncryption:
    """Class to handle encryption and decryption of sensitive data."""
    
    def __init__(self):
        """Initialize with encryption key."""
        self._key = self._get_or_create_key()
        self._cipher = Fernet(self._key)
    
    def _get_or_create_key(self):
        """Get existing key or create a new one."""
        # Use a path relative to the server directory
        server_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server")
        storage_dir = os.path.join(server_dir, "storage")
        key_file = os.path.join(storage_dir, "encryption.key")
        
        # Create directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate a new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt(self, data):
        """
        Encrypt the given data.
        
        Args:
            data: String or bytes to encrypt
            
        Returns:
            Encrypted bytes
        """
        if isinstance(data, str):
            data = data.encode()
        return self._cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """
        Decrypt the given data.
        
        Args:
            encrypted_data: Bytes to decrypt
            
        Returns:
            Decrypted bytes
        """
        return self._cipher.decrypt(encrypted_data) 