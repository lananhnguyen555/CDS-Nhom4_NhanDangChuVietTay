#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask App: Hệ thống OCR và Flashcard
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image

# Fix encoding
if sys.platform == 'win32':
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Tắt OneDNN TRƯỚC KHI import bất kỳ thứ gì
os.environ['FLAGS_use_mkldnn'] = 'False'
os.environ['FLAGS_ir_optim'] = 'False'
os.environ['MKLDNN_ENABLED'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_ir_optim'] = '0'

# Cấu hình để lưu model vào thư mục dự án (ổ D) thay vì C:\Users\...
current_dir = os.path.dirname(os.path.abspath(__file__))
paddleocr_home = os.path.join(current_dir, '.paddleocr')
os.environ['PADDLEOCR_HOME'] = paddleocr_home
os.makedirs(paddleocr_home, exist_ok=True)
print(f"📁 PaddleOCR models will be saved to: {paddleocr_home}")

# Fix SSL
try:
    # Xóa các biến SSL không hợp lệ
    if 'SSL_CERT_FILE' in os.environ:
        ssl_cert = os.environ.get('SSL_CERT_FILE', '')
        if not ssl_cert or not os.path.exists(ssl_cert):
            del os.environ['SSL_CERT_FILE']
    
    if 'REQUESTS_CA_BUNDLE' in os.environ:
        ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE', '')
        if not ca_bundle or not os.path.exists(ca_bundle):
            del os.environ['REQUESTS_CA_BUNDLE']
    
    # Sử dụng certifi nếu có
    try:
        import certifi
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    except:
        pass
except:
    pass

# Tránh conflict
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)

# Import PaddleOCR sau khi đã set environment
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except Exception as e:
    PADDLEOCR_AVAILABLE = False
    print(f"⚠️  PaddleOCR not available: {e}")

# Khởi tạo translator - sẽ khởi tạo lại mỗi lần sử dụng để tránh TKK token issue
translator = None
TRANSLATE_AVAILABLE = False

def get_translator():
    """Lấy translator instance - sử dụng deep-translator để tránh TKK token issue"""
    global translator, TRANSLATE_AVAILABLE
    try:
        # Thử sử dụng deep-translator trước (ổn định hơn, không có TKK token issue)
        try:
            from deep_translator import GoogleTranslator
            # Clear SSL certificate paths để tránh lỗi
            import os
            if 'SSL_CERT_FILE' in os.environ and 'PostgreSQL' in os.environ.get('SSL_CERT_FILE', ''):
                os.environ.pop('SSL_CERT_FILE', None)
            if 'REQUESTS_CA_BUNDLE' in os.environ and 'PostgreSQL' in os.environ.get('REQUESTS_CA_BUNDLE', ''):
                os.environ.pop('REQUESTS_CA_BUNDLE', None)
            # Khởi tạo mới mỗi lần để tránh cache issues
            translator = GoogleTranslator(source='en', target='vi')
            TRANSLATE_AVAILABLE = True
            return translator
        except ImportError:
            print("⚠️  deep-translator not available, trying googletrans...")
        except Exception as e:
            print(f"⚠️  deep-translator error: {e}, trying googletrans...")
        
        # Fallback: sử dụng googletrans nếu deep-translator không có
        try:
            from googletrans import Translator
            # Thử không chỉ định service_urls trước (đơn giản nhất)
            new_translator = Translator()
            translator = new_translator
            TRANSLATE_AVAILABLE = True
            return translator
        except Exception as e:
            print(f"⚠️  googletrans also failed: {e}")
        
        TRANSLATE_AVAILABLE = False
        return None
    except Exception as e:
        translator = None
        TRANSLATE_AVAILABLE = False
        print(f"⚠️  Translation not available: {e}")
        return None

# Không khởi tạo ngay, sẽ khởi tạo khi cần (lazy initialization)
# Điều này giúp tránh lỗi TKK token khi start server
TRANSLATE_AVAILABLE = True  # Giả định có sẵn, sẽ kiểm tra khi thực sự dịch

# Dictionary API
try:
    from dictionary_api import get_word_info
    DICTIONARY_AVAILABLE = True
except:
    DICTIONARY_AVAILABLE = False
    def get_word_info(word):
        return {}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Tất cả lưu vào thư mục dự án (ổ D)
current_dir = Path(__file__).parent.absolute()
app.config['UPLOAD_FOLDER'] = str(current_dir / 'uploads')
app.config['FLASHCARD_FOLDER'] = str(current_dir / 'flashcards')
app.config['MODEL_FOLDER'] = str(current_dir / '.paddleocr')

# Tạo thư mục
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['FLASHCARD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['MODEL_FOLDER']).mkdir(exist_ok=True)

print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
print(f"📚 Flashcard folder: {app.config['FLASHCARD_FOLDER']}")
print(f"🤖 Model folder: {app.config['MODEL_FOLDER']}")

# Khởi tạo OCR (lazy loading)
ocr_instance = None

def get_ocr():
    """Lazy load OCR với inference model để tránh lỗi OneDNN"""
    global ocr_instance
    
    # Đảm bảo OneDNN bị tắt HOÀN TOÀN
    os.environ['FLAGS_use_mkldnn'] = 'False'
    os.environ['FLAGS_ir_optim'] = 'False'
    os.environ['MKLDNN_ENABLED'] = '0'
    os.environ['FLAGS_use_mkldnn'] = '0'
    os.environ['FLAGS_ir_optim'] = '0'
    
    # Đảm bảo model lưu vào thư mục dự án
    if 'PADDLEOCR_HOME' not in os.environ:
        os.environ['PADDLEOCR_HOME'] = app.config['MODEL_FOLDER']
    
    if ocr_instance is None and PADDLEOCR_AVAILABLE:
        try:
            print("🔄 Initializing PaddleOCR với inference model...")
            print(f"   Model folder: {app.config['MODEL_FOLDER']}")
            
            # Sử dụng inference model với tất cả tùy chọn tắt OneDNN
            try:
                # Thử với PP-OCRv4 và inference model
                ocr_instance = PaddleOCR(
                    lang='en',
                    ocr_version='PP-OCRv4',
                    use_textline_orientation=False,  # Tắt để tránh lỗi
                    enable_mkldnn=False,
                    use_gpu=False,
                    # Model sẽ được tải vào app.config['MODEL_FOLDER']
                )
                print("✅ PaddleOCR ready với PP-OCRv4!")
            except Exception as e1:
                print(f"⚠️  Error with PP-OCRv4: {e1}")
                try:
                    # Fallback: không dùng ocr_version, chỉ dùng lang
                    ocr_instance = PaddleOCR(
                        lang='en',
                        use_textline_orientation=False,
                        enable_mkldnn=False,
                        use_gpu=False
                    )
                    print("✅ PaddleOCR ready (fallback 1)!")
                except Exception as e2:
                    print(f"⚠️  Error fallback 1: {e2}")
                    # Fallback cuối cùng: minimal config
                    ocr_instance = PaddleOCR(
                        lang='en',
                        enable_mkldnn=False,
                        use_gpu=False
                    )
                    print("✅ PaddleOCR ready (fallback 2)!")
        except Exception as e:
            print(f"❌ Cannot initialize OCR: {e}")
            import traceback
            traceback.print_exc()
            ocr_instance = False
    elif ocr_instance is False:
        # Nếu đã thử và thất bại, không thử lại
        return None
    
    return ocr_instance

# Load flashcards
def load_flashcards():
    flashcard_file = Path(app.config['FLASHCARD_FOLDER']) / 'flashcards.json'
    if flashcard_file.exists():
        try:
            with open(flashcard_file, 'r', encoding='utf-8') as f:
                flashcards = json.load(f)
                # Loại bỏ duplicate dựa trên ID
                seen_ids = set()
                unique_flashcards = []
                for card in flashcards:
                    if isinstance(card, dict) and 'id' in card:
                        card_id = card['id']
                        if card_id not in seen_ids:
                            seen_ids.add(card_id)
                            unique_flashcards.append(card)
                # Nếu có duplicate, lưu lại file đã làm sạch
                if len(unique_flashcards) < len(flashcards):
                    print(f"⚠️  Phát hiện {len(flashcards) - len(unique_flashcards)} flashcard trùng lặp, đã loại bỏ")
                    save_flashcards(unique_flashcards)
                    return unique_flashcards
                return flashcards
        except Exception as e:
            print(f"❌ Error loading flashcards: {e}")
            return []
    return []

def save_flashcards(flashcards):
    flashcard_file = Path(app.config['FLASHCARD_FOLDER']) / 'flashcards.json'
    with open(flashcard_file, 'w', encoding='utf-8') as f:
        json.dump(flashcards, f, ensure_ascii=False, indent=2)

def get_next_flashcard_id(flashcards):
    """Lấy ID tiếp theo cho flashcard mới - đảm bảo không trùng"""
    if not flashcards:
        return 1
    max_id = max(card.get('id', 0) for card in flashcards if isinstance(card, dict) and 'id' in card)
    return max_id + 1

# Routes
@app.route('/')
def index():
    """Màn hình chính"""
    flashcards = load_flashcards()
    recent = flashcards[-10:] if len(flashcards) > 10 else flashcards
    recent.reverse()
    
    # Daily word - random từ flashcard
    daily_word = None
    if flashcards:
        import random
        daily_word = random.choice(flashcards)
    
    return render_template('index.html', recent_flashcards=recent, daily_word=daily_word)

@app.route('/scan')
def scan():
    """Màn hình Scan/OCR"""
    return render_template('scan.html')

@app.route('/flashcards')
def flashcards():
    """Màn hình Flashcard"""
    try:
        flashcards = load_flashcards()
        card_id = request.args.get('id')
        
        # Đảm bảo flashcards là list
        if not isinstance(flashcards, list):
            print(f"⚠️  Flashcards is not a list: {type(flashcards)}")
            flashcards = []
        
        # Nếu có id, tìm và hiển thị card đó đầu tiên
        if card_id:
            try:
                card_id = int(card_id)
                # Sắp xếp lại để card được chọn ở đầu
                target_card = next((c for c in flashcards if isinstance(c, dict) and c.get('id') == card_id), None)
                if target_card:
                    flashcards.remove(target_card)
                    flashcards.insert(0, target_card)
            except Exception as e:
                print(f"⚠️  Error processing card_id: {e}")
        
        print(f"📚 Rendering flashcards page with {len(flashcards)} cards")
        return render_template('flashcards.html', flashcards=flashcards)
    except Exception as e:
        print(f"❌ Error in flashcards route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('flashcards.html', flashcards=[])

@app.route('/learn')
def learn():
    """Màn hình Học/Ôn tập"""
    flashcards = load_flashcards()
    return render_template('learn.html', flashcards=flashcards)

@app.route('/info')
def info():
    """Trang thông tin hệ thống"""
    return render_template('info.html')

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API Routes
@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload ảnh"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file:
            return jsonify({'error': 'Invalid file'}), 400
        
        # Kiểm tra định dạng file
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        
        # Đảm bảo thư mục tồn tại
        Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
        
        file.save(str(filepath))
        
        # Kiểm tra file đã được lưu
        if not filepath.exists():
            return jsonify({'error': 'Failed to save file'}), 500
        
        # Return both filename and relative path for frontend
        return jsonify({
            'success': True, 
            'filename': filename, 
            'path': str(filepath),
            'url': f'/uploads/{filename}'
        })
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/ocr', methods=['POST'])
def ocr_image():
    """OCR ảnh"""
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    data = request.json
    image_path = data.get('image_path')
    
    if not image_path:
        return jsonify({'error': 'Image path not provided'}), 400
    
    if not Path(image_path).exists():
        return jsonify({'error': 'Image not found'}), 404
    
    # Đảm bảo OneDNN bị tắt trước khi OCR
    os.environ['FLAGS_use_mkldnn'] = 'False'
    os.environ['FLAGS_ir_optim'] = 'False'
    os.environ['MKLDNN_ENABLED'] = '0'
    
    ocr = get_ocr()
    if not ocr:
        return jsonify({'error': 'OCR not available'}), 500
    
    try:
        # OCR - Sử dụng inference model với API 2.x (ổn định hơn)
        # API 2.x sử dụng inference model mặc định và ít gặp lỗi OneDNN hơn
        print(f"🔄 Running OCR on: {image_path}")
        
        # Thử API 2.x trước (ổn định hơn với inference model)
        try:
            result = ocr.ocr(str(image_path), cls=False)  # Tắt cls để tránh lỗi
            print(f"OCR result type: {type(result)}")
            
            if not result or not result[0]:
                return jsonify({'error': 'No text detected'}), 400
            
            # Giữ nguyên từng dòng, không gộp lại
            lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)):
                        text = text_info[0]
                    else:
                        text = text_info
                    lines.append(text.strip())
                    print(f"  Detected line: {text}")
            
            # Trả về cả text gộp và lines riêng lẻ
            text = "\n".join(lines)  # Dùng \n để phân cách dòng
            text_joined = " ".join(lines)  # Text gộp cho dịch
            
        except Exception as e1:
            print(f"⚠️  OCR API 2.x failed: {e1}")
            # Fallback: thử API 3.x
            if hasattr(ocr, 'predict'):
                try:
                    result = ocr.predict(str(image_path), use_textline_orientation=False)
                    lines = []
                    for page in result:
                        for block in page.blocks:
                            for line in block.lines:
                                lines.append(line.text.strip())
                    text = "\n".join(lines)
                    text_joined = " ".join(lines)
                except Exception as e2:
                    print(f"⚠️  OCR API 3.x also failed: {e2}")
                    raise e1  # Raise original error
            else:
                raise e1
        
        if not text:
            return jsonify({'error': 'No text detected'}), 400
        
        # Trả về cả text theo dòng và text gộp
        return jsonify({
            'success': True, 
            'text': text,  # Text với \n phân cách dòng
            'text_lines': lines,  # List các dòng
            'text_joined': text_joined  # Text gộp cho dịch
        })
    
    except Exception as e:
        error_msg = str(e)
        # Kiểm tra nếu là lỗi OneDNN
        if 'OneDnnContext' in error_msg or 'onednn' in error_msg.lower():
            return jsonify({
                'error': 'OneDNN error. Please try again or contact support.',
                'details': error_msg
            }), 500
        return jsonify({'error': error_msg}), 500

@app.route('/api/translate', methods=['POST'])
def translate():
    """Dịch văn bản - dịch từng dòng riêng biệt"""
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    data = request.json
    text = data.get('text', '').strip()
    lines = data.get('lines', [])  # Nhận danh sách các dòng nếu có
    
    if not text and not lines:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Khởi tạo lại translator mỗi lần để tránh TKK token issue
        current_translator = get_translator()
        if not current_translator:
            return jsonify({'error': 'Translation not available. Google Translate không thể kết nối. Vui lòng thử lại sau.'}), 500
        
        # Nếu có danh sách dòng, dịch từng dòng riêng biệt
        if lines and len(lines) > 0:
            print(f"🔄 Translating {len(lines)} lines individually...")
            translated_lines = []
            import time
            
            # Khởi tạo translator một lần trước vòng lặp
            current_translator = get_translator()
            if not current_translator:
                print("❌ Cannot initialize translator at start")
                return jsonify({'error': 'Translation not available. Google Translate không thể kết nối. Vui lòng thử lại sau.'}), 500
            
            for i, line in enumerate(lines):
                if not line.strip():
                    translated_lines.append('')
                    continue
                
                line_text = line.strip()
                translated_text = None
                max_retries = 3
                retry_count = 0
                
                # Thêm delay nhỏ giữa các request để tránh rate limit
                if i > 0:
                    time.sleep(0.3)  # Tăng delay lên 300ms
                
                while retry_count < max_retries and not translated_text:
                    try:
                        # Khởi tạo lại translator cho mỗi lần thử để tránh TKK token issue
                        current_translator = get_translator()
                        if not current_translator:
                            raise Exception("Cannot get translator instance")
                        
                        print(f"  🔄 [{i+1}/{len(lines)}] Translating: {line_text[:40]}...")
                        
                        # Kiểm tra xem là deep-translator hay googletrans
                        # deep-translator: translate() trả về string trực tiếp
                        # googletrans: translate() trả về object có .text
                        try:
                            # Thử gọi như deep-translator (không có src/dest trong translate method)
                            translated_text = current_translator.translate(line_text)
                            if not isinstance(translated_text, str):
                                # Nếu không phải string, có thể là googletrans
                                raise AttributeError("Not deep-translator")
                        except (TypeError, AttributeError):
                            # Nếu lỗi, thử googletrans
                            result = current_translator.translate(line_text, src='en', dest='vi', timeout=15)
                            translated_text = result.text if result and hasattr(result, 'text') else None
                        
                        if translated_text:
                            translated_text = translated_text.strip()
                            print(f"  ✅ [{i+1}/{len(lines)}] Success: {line_text[:30]}... → {translated_text[:30]}...")
                            break
                        else:
                            raise Exception("Empty translation result")
                            
                    except Exception as retry_error:
                        error_msg = str(retry_error)
                        retry_count += 1
                        
                        # Kiểm tra các lỗi cụ thể
                        if '429' in error_msg or 'Too Many Requests' in error_msg:
                            print(f"  ⚠️  Rate limit for line {i+1}, waiting 3 seconds...")
                            time.sleep(3)
                        elif 'TKK' in error_msg or 'token' in error_msg.lower():
                            print(f"  ⚠️  TKK token issue for line {i+1}, resetting translator...")
                            translator = None  # Reset global translator
                            time.sleep(1)
                        elif 'timeout' in error_msg.lower():
                            print(f"  ⚠️  Timeout for line {i+1}, retrying...")
                            time.sleep(1)
                        else:
                            print(f"  ⚠️  Error for line {i+1} (attempt {retry_count}/{max_retries}): {error_msg[:100]}")
                            time.sleep(0.5 * retry_count)  # Exponential backoff
                        
                        if retry_count >= max_retries:
                            print(f"  ❌ Failed after {max_retries} attempts for line {i+1}: {line_text}")
                            break
                
                # Thêm kết quả vào danh sách
                if translated_text:
                    translated_lines.append(translated_text)
                else:
                    # Nếu vẫn lỗi, thử một lần cuối với translator mới hoàn toàn
                    try:
                        translator = None  # Reset hoàn toàn
                        time.sleep(1)
                        final_translator = get_translator()
                        if final_translator:
                            # Kiểm tra xem là deep-translator hay googletrans
                            try:
                                # Thử deep-translator trước
                                final_result = final_translator.translate(line_text)
                                if not isinstance(final_result, str):
                                    raise AttributeError("Not deep-translator")
                            except (TypeError, AttributeError):
                                # Nếu lỗi, thử googletrans
                                result = final_translator.translate(line_text, src='en', dest='vi', timeout=20)
                                final_result = result.text if result and hasattr(result, 'text') else None
                            
                            if final_result:
                                translated_lines.append(final_result.strip())
                                print(f"  ✅ [{i+1}/{len(lines)}] Final retry successful!")
                            else:
                                translated_lines.append(f"[Lỗi dịch: {line_text}]")
                        else:
                            translated_lines.append(f"[Lỗi dịch: {line_text}]")
                    except Exception as final_error:
                        print(f"  ❌ Final retry also failed: {final_error}")
                        translated_lines.append(f"[Lỗi dịch: {line_text}]")
            
            return jsonify({
                'success': True, 
                'translated': '\n'.join(translated_lines),  # Text gộp
                'translated_lines': translated_lines  # List các dòng đã dịch
            })
        else:
            # Fallback: dịch toàn bộ text
            print(f"🔄 Translating text: {text[:100]}...")
            try:
                # Retry mechanism
                max_retries = 3
                retry_count = 0
                translated = None
                import time
                
                while retry_count < max_retries and not translated:
                    try:
                        # Khởi tạo lại translator cho mỗi request
                        current_translator = get_translator()
                        if not current_translator:
                            raise Exception("Cannot get translator instance")
                        
                        # Kiểm tra xem là deep-translator hay googletrans
                        try:
                            # Thử deep-translator trước
                            translated = current_translator.translate(text)
                            if not isinstance(translated, str):
                                raise AttributeError("Not deep-translator")
                        except (TypeError, AttributeError):
                            # Nếu lỗi, thử googletrans
                            result = current_translator.translate(text, src='en', dest='vi', timeout=10)
                            translated = result.text if result and hasattr(result, 'text') else None
                        
                        if translated:
                            break
                    except Exception as retry_error:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"  ⚠️  Retry {retry_count}/{max_retries}: {retry_error}")
                            # Khởi tạo lại translator khi retry
                            translator = None
                            time.sleep(0.5 * retry_count)
                        else:
                            raise retry_error
                
                if translated:
                    print(f"✅ Translated: {translated[:100]}...")
                    return jsonify({'success': True, 'translated': translated, 'translated_lines': [translated]})
                else:
                    return jsonify({'error': 'Invalid translation result'}), 500
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Translation error: {error_msg}")
                # Kiểm tra nếu là lỗi bị chặn
                if '429' in error_msg or 'Too Many Requests' in error_msg or 'blocked' in error_msg.lower():
                    return jsonify({'error': 'Google Translate bị giới hạn. Vui lòng đợi vài phút rồi thử lại.'}), 429
                return jsonify({'error': f'Translation failed: {error_msg}'}), 500
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Translation error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Kiểm tra các lỗi phổ biến
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return jsonify({'error': 'Google Translate bị giới hạn. Vui lòng đợi vài phút rồi thử lại.'}), 429
        elif 'blocked' in error_msg.lower() or 'captcha' in error_msg.lower():
            return jsonify({'error': 'Google Translate bị chặn tạm thời. Vui lòng thử lại sau.'}), 503
        elif 'timeout' in error_msg.lower():
            return jsonify({'error': 'Kết nối quá lâu. Vui lòng kiểm tra internet và thử lại.'}), 504
        else:
            return jsonify({'error': f'Translation failed: {error_msg}'}), 500

@app.route('/api/flashcard', methods=['POST'])
def create_flashcard():
    """Tạo flashcard - AI Auto Generator với đầy đủ thông tin"""
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    data = request.json
    original = data.get('original', '').strip()
    translated = data.get('translated', '').strip()
    image_path = data.get('image_path', '')
    category = data.get('category', 'vocabulary')
    notes = data.get('notes', '')
    
    # Nhận danh sách các dòng để tạo nhiều flashcard
    original_lines = data.get('original_lines', [])
    translated_lines = data.get('translated_lines', [])
    
    if not original and not original_lines:
        return jsonify({'error': 'Original text required'}), 400
    
    flashcards = load_flashcards()
    created_flashcards = []
    
    # Nếu có danh sách dòng, tạo 1 flashcard cho mỗi dòng (chỉ dùng Google Translate - cách ban đầu)
    # KHÔNG dịch ví dụ để tránh rate limit và timeout
    if original_lines and len(original_lines) > 0:
        print(f"🔄 Creating {len(original_lines)} flashcards (using Google Translate only, no example translation)...")
        import time
        for i, orig_line in enumerate(original_lines):
            if not orig_line.strip():
                continue
            
            word = orig_line.strip()
            print(f"  🔄 Processing word {i+1}/{len(original_lines)}: {word}")
            
            # Lấy nghĩa tương ứng (từ Google Translate - cách ban đầu)
            trans_line = translated_lines[i] if i < len(translated_lines) else translated
            
            # Khôi phục cách tra nghĩa ban đầu: Chỉ dùng Google Translate, KHÔNG dịch ví dụ
            # Tạo flashcard đơn giản với nghĩa từ Google Translate (đã dịch ở bước trước)
            flashcard = {
                'id': get_next_flashcard_id(flashcards) + len(created_flashcards),
                'original': word,
                'translated': trans_line.strip() if trans_line else '',
                'pronunciation': '',
                'part_of_speech': '',
                'example': '',  # Không có ví dụ
                'example_translated': '',  # KHÔNG dịch ví dụ để tránh rate limit
                'synonyms': [],
                'antonyms': [],
                'collocations': [],
                'audio': '',
                'image': image_path,
                'category': category,
                'notes': notes,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'review_count': 0,
                'last_reviewed': None,
                'difficulty': 'medium',
                'favorite': False,
                'learned': False,
                'not_learned': False,
                'correct_count': 0,
                'wrong_count': 0
            }
            
            flashcards.append(flashcard)
            created_flashcards.append(flashcard)
            print(f"    ✅ Created flashcard: {word} → {trans_line.strip() if trans_line else 'N/A'}")
            
            # Delay nhỏ giữa các card để tránh quá tải
            if i < len(original_lines) - 1:
                time.sleep(0.05)  # 50ms delay giữa các card
        
        save_flashcards(flashcards)
        return jsonify({
            'success': True, 
            'count': len(created_flashcards),
            'flashcards': created_flashcards
        })
    
    # Fallback: tạo 1 flashcard cho toàn bộ text
    else:
        # Khôi phục cách tra nghĩa ban đầu: Chỉ dùng Google Translate
        flashcard = {
            'id': get_next_flashcard_id(flashcards),
            'original': original,
            'translated': translated,
            'pronunciation': '',
            'part_of_speech': '',
            'example': '',
            'example_translated': '',
            'synonyms': [],
            'antonyms': [],
            'collocations': [],
            'audio': '',
            'image': image_path,
            'category': category,
            'notes': notes,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'review_count': 0,
            'last_reviewed': None,
            'difficulty': 'medium',
            'favorite': False,
            'learned': False,
            'not_learned': False,
            'correct_count': 0,
            'wrong_count': 0
        }
        
        flashcards.append(flashcard)
        save_flashcards(flashcards)
        
        return jsonify({'success': True, 'count': 1, 'flashcards': [flashcard]})

@app.route('/api/flashcard/<int:card_id>', methods=['GET', 'PUT', 'DELETE'])
def flashcard_detail(card_id):
    """Lấy/Sửa/Xóa flashcard"""
    flashcards = load_flashcards()
    card = next((c for c in flashcards if c['id'] == card_id), None)
    
    if not card:
        return jsonify({'error': 'Flashcard not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'success': True, 'flashcard': card})
    
    elif request.method == 'PUT':
        if not request.json:
            return jsonify({'error': 'No JSON data provided'}), 400
        data = request.json
        
        # Đảm bảo không cho phép thay đổi ID
        if 'id' in data:
            del data['id']
        
        # Cập nhật các trường được gửi lên (chỉ cập nhật, không tạo mới)
        for key, value in data.items():
            if key != 'id':  # Không cho phép thay đổi ID
                card[key] = value
        
        save_flashcards(flashcards)
        return jsonify({'success': True, 'flashcard': card})
    
    elif request.method == 'DELETE':
        flashcards.remove(card)
        save_flashcards(flashcards)
        return jsonify({'success': True})

@app.route('/api/flashcards', methods=['GET', 'DELETE'])
def get_flashcards():
    """Lấy danh sách flashcard hoặc xóa tất cả"""
    if request.method == 'DELETE':
        # Xóa toàn bộ flashcard
        try:
            save_flashcards([])
            print("🗑️  Đã xóa toàn bộ flashcard")
            return jsonify({'success': True, 'message': 'Đã xóa toàn bộ flashcard', 'count': 0})
        except Exception as e:
            print(f"❌ Error deleting all flashcards: {e}")
            return jsonify({'error': f'Lỗi khi xóa: {str(e)}'}), 500
    
    # GET: Lấy danh sách flashcard
    flashcards = load_flashcards()
    category = request.args.get('category')
    favorite = request.args.get('favorite')
    
    if category:
        flashcards = [c for c in flashcards if c.get('category') == category]
    if favorite == 'true':
        flashcards = [c for c in flashcards if c.get('favorite')]
    
    return jsonify({'success': True, 'flashcards': flashcards, 'count': len(flashcards)})

@app.route('/api/search', methods=['GET'])
def search():
    """Tìm kiếm flashcard"""
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({'success': True, 'flashcards': []})
    
    flashcards = load_flashcards()
    results = []
    for card in flashcards:
        if query in card.get('original', '').lower() or query in card.get('translated', '').lower():
            results.append(card)
    
    return jsonify({'success': True, 'flashcards': results, 'count': len(results)})

@app.route('/api/review', methods=['POST'])
def review_flashcard():
    """Cập nhật kết quả ôn tập"""
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    data = request.json
    card_id = data.get('card_id')
    is_correct = data.get('is_correct', False)
    
    flashcards = load_flashcards()
    card = next((c for c in flashcards if c['id'] == card_id), None)
    
    if not card:
        return jsonify({'error': 'Flashcard not found'}), 404
    
    card['review_count'] = card.get('review_count', 0) + 1
    card['last_reviewed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if is_correct:
        card['correct_count'] = card.get('correct_count', 0) + 1
    else:
        card['wrong_count'] = card.get('wrong_count', 0) + 1
    
    save_flashcards(flashcards)
    return jsonify({'success': True, 'flashcard': card})

@app.route('/api/stats', methods=['GET'])
def stats():
    """Thống kê"""
    flashcards = load_flashcards()
    
    total = len(flashcards)
    reviewed = len([c for c in flashcards if c.get('review_count', 0) > 0])
    favorites = len([c for c in flashcards if c.get('favorite')])
    
    total_correct = sum(c.get('correct_count', 0) for c in flashcards)
    total_wrong = sum(c.get('wrong_count', 0) for c in flashcards)
    accuracy = (total_correct / (total_correct + total_wrong) * 100) if (total_correct + total_wrong) > 0 else 0
    
    return jsonify({
        'success': True,
        'stats': {
            'total': total,
            'reviewed': reviewed,
            'favorites': favorites,
            'accuracy': round(accuracy, 2),
            'total_correct': total_correct,
            'total_wrong': total_wrong
        }
    })

if __name__ == '__main__':
    print("="*80)
    print("🚀 Starting Flask App...")
    print("="*80)
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📚 Flashcard folder: {app.config['FLASHCARD_FOLDER']}")
    print(f"🔍 OCR Available: {PADDLEOCR_AVAILABLE}")
    print(f"🌐 Translation Available: {TRANSLATE_AVAILABLE}")
    print("="*80)
    print("🌐 Open: http://127.0.0.1:5000")
    print("="*80)
    
    app.run(debug=True, host='127.0.0.1', port=5000)

