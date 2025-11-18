#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script cài đặt requirements - Chạy: python install_requirements.py
"""

import subprocess
import sys
import os

def install_requirements():
    """Cài đặt requirements từ file"""
    print("=" * 50)
    print("Installing Flask requirements...")
    print("=" * 50)
    print()
    
    # Xóa các biến SSL không hợp lệ
    if 'SSL_CERT_FILE' in os.environ:
        ssl_cert = os.environ.get('SSL_CERT_FILE', '')
        if not ssl_cert or not os.path.exists(ssl_cert):
            del os.environ['SSL_CERT_FILE']
            print("✅ Removed invalid SSL_CERT_FILE")
    
    if 'REQUESTS_CA_BUNDLE' in os.environ:
        ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE', '')
        if not ca_bundle or not os.path.exists(ca_bundle):
            del os.environ['REQUESTS_CA_BUNDLE']
            print("✅ Removed invalid REQUESTS_CA_BUNDLE")
    
    # Cài đặt từ file
    print("Installing packages from requirements_flask.txt...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements_flask.txt'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("✅ Installation completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error installing from file: {e}")
        print("\nTrying to install packages individually...")
        
        packages = [
            'flask>=2.3.0',
            'werkzeug>=2.3.0',
            'paddleocr>=2.7.0',
            'deep-translator>=1.11.0',
            'Pillow>=9.0.0',
            'certifi>=2023.0.0',
            'requests>=2.31.0'
        ]
        
        failed = []
        for package in packages:
            try:
                print(f"Installing {package}...")
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    check=True,
                    capture_output=True
                )
                print(f"✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                failed.append(package)
        
        if failed:
            print(f"\n⚠️  Failed to install: {', '.join(failed)}")
            print("Note: System will use simple_translator.py as fallback")
        else:
            print("\n✅ All packages installed successfully!")
        return len(failed) == 0

if __name__ == '__main__':
    try:
        install_requirements()
        print("\n" + "=" * 50)
        print("Done!")
        print("=" * 50)
        print("\nNote: If deep-translator is not installed, system will use simple_translator.py")
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

