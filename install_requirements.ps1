# PowerShell script to install requirements
# Chạy: powershell -ExecutionPolicy Bypass -File install_requirements.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Flask requirements..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Xóa các biến SSL không hợp lệ
$env:SSL_CERT_FILE = $null
$env:REQUESTS_CA_BUNDLE = $null

# Cài đặt requirements
Write-Host "Installing packages from requirements_flask.txt..." -ForegroundColor Yellow
pip install -r requirements_flask.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Có lỗi khi cài đặt. Thử cài đặt từng package..." -ForegroundColor Yellow
    Write-Host ""
    pip install flask>=2.3.0
    pip install werkzeug>=2.3.0
    pip install paddleocr>=2.7.0
    pip install deep-translator>=1.11.0
    pip install Pillow>=9.0.0
    pip install certifi>=2023.0.0
    pip install requests>=2.31.0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Nếu không cài được deep-translator, hệ thống sẽ tự động sử dụng simple_translator.py" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

