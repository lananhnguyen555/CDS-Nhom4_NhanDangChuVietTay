<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
   XÂY DỰNG HỆ THỐNG CHUYỂN ĐỔI TÀI LIỆU VIẾT TAY THÀNH VĂN BẢN SỐ
</h2>
<div align="center">
    <p align="center">
        <img src="logo/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="logo/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="logo/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>


![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![PaddleOCR](https://img.shields.io/badge/PaddleOCR-2.7.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)



## 🎯 Giới thiệu

Dự án này là một hệ thống OCR (Optical Character Recognition) chuyên dụng cho việc nhận dạng chữ viết tay tiếng Việt và chữ in tiếng Anh. Hệ thống tích hợp nhiều công nghệ OCR hiện đại và cung cấp thêm tính năng học từ vựng thông qua flashcard.

Hệ thống sử dụng:
- **PaddleOCR**: Công cụ OCR mã nguồn mở của Baidu, hỗ trợ nhiều ngôn ngữ
- **Google Translate API**: Dịch văn bản tự động
- **Dictionary API**: Tra cứu từ điển và tạo flashcard

## ✨ Tính năng

### OCR (Nhận dạng văn bản)
- ✅ Nhận dạng chữ viết tay tiếng Việt với độ chính xác cao
- ✅ Nhận dạng chữ in tiếng Anh
- ✅ Hỗ trợ PaddleOCR với inference model sẵn có
- ✅ Xử lý văn bản nhiều dòng
- ✅ Hiển thị kết quả theo từng dòng để dễ đọc và chỉnh sửa

### Học từ vựng (Flashcard)
- ✅ Tự động tạo flashcard từ văn bản đã nhận dạng
- ✅ Dịch văn bản tiếng Anh sang tiếng Việt
- ✅ Tra cứu từ điển với đầy đủ thông tin (phát âm, nghĩa, ví dụ, từ đồng nghĩa)
- ✅ Quản lý flashcard: thêm, sửa, xóa, tìm kiếm
- ✅ Ôn tập flashcard với thống kê kết quả
- ✅ Đánh dấu yêu thích và theo dõi tiến độ học tập

### Giao diện Web
- ✅ Giao diện web thân thiện với Flask
- ✅ Upload và nhận dạng ảnh trực tiếp trên trình duyệt
- ✅ Xem kết quả với confidence score
- ✅ Tạo flashcard ngay sau khi nhận dạng
- ✅ Quản lý và ôn tập flashcard

## 💻 Yêu cầu hệ thống

- **Python**: 3.8 trở lên
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **GPU**: Không bắt buộc (hỗ trợ GPU để tăng tốc độ xử lý)
- **Disk**: Tối thiểu 5GB trống (cho model và dependencies)
- **OS**: Windows, Linux, hoặc macOS

## 📦 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd NhanDangChuVietTay
```

### 2. Tạo virtual environment (khuyến nghị)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies

**Cài đặt dependencies cơ bản:**
```bash
pip install -r requirements.txt
```

**Cài đặt dependencies cho Flask app:**
```bash
pip install -r requirements_flask.txt
```

**Hoặc sử dụng script tự động:**
```bash
# Windows
install_requirements.bat

# PowerShell
install_requirements.ps1

# Python
python install_requirements.py
```

**Lưu ý**: 
- Cài đặt PaddleOCR có thể mất vài phút
- Model PaddleOCR sẽ được tải tự động vào thư mục `.paddleocr` khi chạy lần đầu

## 🚀 Sử dụng

### 1. Sử dụng qua Web Interface (Khuyến nghị)

#### Khởi động server:

```bash
python app.py
```

Sau đó mở trình duyệt và truy cập: `http://127.0.0.1:5000`

#### Các trang chính:
- **`/`**: Trang chủ - Dashboard với flashcard gần đây
- **`/scan`**: Upload và nhận dạng ảnh OCR
- **`/flashcards`**: Quản lý flashcard
- **`/learn`**: Ôn tập flashcard
- **`/info`**: Thông tin về hệ thống

#### Tính năng web interface:
- Upload ảnh và nhận dạng ngay lập tức
- Xem kết quả với confidence score
- Dịch văn bản tiếng Anh sang tiếng Việt
- Tạo flashcard tự động từ văn bản đã nhận dạng
- Quản lý flashcard: thêm, sửa, xóa, tìm kiếm
- Ôn tập flashcard với thống kê

### 2. Sử dụng qua Python API

#### Sử dụng PaddleOCR:

```python
from app import get_ocr

# Lấy OCR instance
ocr = get_ocr()

# Nhận dạng ảnh
result = ocr.ocr('path/to/image.jpg', cls=False)
if result and result[0]:
    for line in result[0]:
        text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
        print(text)
```

### 3. API Endpoints

#### POST `/api/upload`
Upload ảnh lên server.

**Request:**
- `image`: File ảnh (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "filename": "image.jpg",
  "url": "/uploads/image.jpg"
}
```

#### POST `/api/ocr`
Nhận dạng văn bản từ ảnh.

**Request:**
```json
{
  "image_path": "/uploads/image.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "text": "Văn bản đã nhận dạng",
  "text_lines": ["Dòng 1", "Dòng 2"],
  "text_joined": "Dòng 1 Dòng 2"
}
```

#### POST `/api/translate`
Dịch văn bản từ tiếng Anh sang tiếng Việt.

**Request:**
```json
{
  "text": "Hello world",
  "lines": ["Hello", "world"]
}
```

**Response:**
```json
{
  "success": true,
  "translated": "Xin chào thế giới",
  "translated_lines": ["Xin chào", "thế giới"]
}
```

#### POST `/api/flashcard`
Tạo flashcard mới.

**Request:**
```json
{
  "original": "Hello",
  "translated": "Xin chào",
  "image_path": "/uploads/image.jpg",
  "original_lines": ["Hello", "world"],
  "translated_lines": ["Xin chào", "thế giới"]
}
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "flashcards": [...]
}
```

#### GET `/api/flashcards`
Lấy danh sách flashcard.

**Query parameters:**
- `category`: Lọc theo danh mục
- `favorite`: Lọc flashcard yêu thích (`true`/`false`)

#### GET `/api/stats`
Lấy thống kê flashcard.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total": 100,
    "reviewed": 50,
    "favorites": 10,
    "accuracy": 85.5,
    "total_correct": 200,
    "total_wrong": 30
  }
}
```

## 📁 Cấu trúc dự án

```
NhanDangChuVietTay/
│
├── app.py                      # Flask app chính (OCR + Flashcard)
├── dictionary_api.py           # API tra cứu từ điển
│
├── AnhTT/                      # Thư mục ảnh mẫu
│   ├── *.jpg                   # Ảnh mẫu
│   └── *.txt                   # Ground truth tương ứng
│
├── templates/                   # HTML templates cho web interface
│   ├── base.html
│   ├── index.html              # Trang chủ
│   ├── scan.html               # Trang OCR
│   ├── flashcards.html         # Trang quản lý flashcard
│   ├── learn.html              # Trang ôn tập
│   └── info.html              # Trang thông tin
│
├── static/                      # Static files (CSS, JS)
│   ├── css/
│   └── js/
│
├── uploads/                     # Thư mục lưu ảnh đã upload
├── flashcards/                 # Thư mục lưu flashcard
│   └── flashcards.json
│
├── paddleocr/                   # PaddleOCR package
├── ppocr/                       # PaddleOCR core
├── ppstructure/                 # PaddleOCR structure analysis
│
├── configs/                     # Cấu hình OCR
│   ├── det/                    # Detection configs
│   ├── rec/                    # Recognition configs
│   ├── cls/                    # Classification configs
│   └── ...
│
├── requirements.txt             # Python dependencies cơ bản
├── requirements_flask.txt       # Dependencies cho Flask app
├── install_requirements.bat    # Script cài đặt (Windows)
├── install_requirements.ps1    # Script cài đặt (PowerShell)
└── README.md                    # File này
```

## 🔧 Cấu hình

### Cấu hình PaddleOCR

Model PaddleOCR sẽ được tải tự động vào thư mục `.paddleocr` trong thư mục dự án. Bạn có thể cấu hình trong `app.py`:

```python
ocr_instance = PaddleOCR(
    lang='en',  # hoặc 'vi' cho tiếng Việt
    ocr_version='PP-OCRv4',
    use_gpu=False,  # True nếu có GPU
    enable_mkldnn=False
)
```

### Cấu hình Translation

Hệ thống sử dụng Google Translate API thông qua `deep-translator` hoặc `googletrans`. Cấu hình trong `app.py`:

```python
from deep_translator import GoogleTranslator
translator = GoogleTranslator(source='en', target='vi')
```

## 📊 Kết quả

- **Accuracy trên test set**: ~85-97% (tùy thuộc vào chất lượng ảnh và phương thức OCR)
- **Inference time**: 
  - PaddleOCR: ~0.5-1 giây/ảnh (CPU), ~0.1-0.2 giây/ảnh (GPU)
- **Model size**: 
  - PaddleOCR: ~100-200 MB (tải tự động)

## 🔧 Troubleshooting

### Lỗi khi load PaddleOCR

```bash
# Kiểm tra cài đặt
pip install --upgrade paddlepaddle paddleocr

# Xóa cache và tải lại
rm -rf .paddleocr
```

### Lỗi OneDNN

Nếu gặp lỗi OneDNN, hệ thống đã tự động tắt OneDNN trong code. Nếu vẫn lỗi:

```bash
# Set environment variables
export FLAGS_use_mkldnn=False
export FLAGS_ir_optim=False
```

### Lỗi Translation API

Nếu Google Translate bị chặn hoặc rate limit:
- Đợi vài phút rồi thử lại
- Kiểm tra kết nối internet
- Hệ thống sẽ tự động retry với delay

## 📝 Ghi chú

- Hệ thống tự động lưu model PaddleOCR vào thư mục `.paddleocr` trong dự án
- Flashcard được lưu trong `flashcards/flashcards.json`
- Ảnh upload được lưu trong `uploads/`
- Hệ thống hoạt động offline cho OCR (không cần internet)
- Dịch tự động yêu cầu kết nối internet

## 🙏 Acknowledgments

- **PaddleOCR**: Baidu PaddlePaddle team - [GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- **Flask**: Pallets Projects - [Website](https://flask.palletsprojects.com/)
- **Google Translate**: Google Cloud Translation API
- **Free Dictionary API**: [dictionaryapi.dev](https://dictionaryapi.dev/)

## 📧 Tác giả

**Nguyễn Thị Lan Anh**  
📧 nguyenthilananh24022004@gmail.com

---

<div align="center">
    <p>Được phát triển bởi Khoa Công nghệ Thông tin - Đại học Đại Nam</p>
    <p>© 2024 - All rights reserved</p>
</div>
