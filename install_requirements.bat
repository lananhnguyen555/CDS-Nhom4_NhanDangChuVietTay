@echo off
chcp 65001 >nul
echo ========================================
echo Installing Flask requirements...
echo ========================================
echo.

REM Xoa cac bien SSL khong hop le
set SSL_CERT_FILE=
set REQUESTS_CA_BUNDLE=

REM Cai dat requirements
echo Installing packages from requirements_flask.txt...
pip install -r requirements_flask.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️  Co loi khi cai dat. Thu cai dat tung package...
    echo.
    pip install flask>=2.3.0
    pip install werkzeug>=2.3.0
    pip install paddleocr>=2.7.0
    pip install deep-translator>=1.11.0
    pip install Pillow>=9.0.0
    pip install certifi>=2023.0.0
    pip install requests>=2.31.0
)

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Note: Neu khong cai duoc deep-translator, he thong se tu dong su dung simple_translator.py
pause

