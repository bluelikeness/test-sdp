"""
유틸리티 함수들
"""

import os
import psutil
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

def get_gpu_info():
    """GPU 정보 반환"""
    if not GPU_AVAILABLE:
        return None, 0, 0
    
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return None, 0, 0
            
        gpu = gpus[0]  # 첫 번째 GPU 사용
        total_memory = gpu.memoryTotal / 1024  # GB 단위로 변환
        used_memory = gpu.memoryUsed / 1024
        available_memory = total_memory - used_memory
        
        return gpu.name, total_memory, available_memory
    except:
        return None, 0, 0

def check_model_compatibility(model_info):
    """모델과 시스템 호환성 체크"""
    gpu_name, total_memory, available_memory = get_gpu_info()
    
    if not gpu_name:
        return False, "GPU를 찾을 수 없습니다"
    
    min_required = model_info.get("min_gpu_memory", 0)
    recommended = model_info.get("recommended_gpu_memory", 0)
    
    if available_memory < min_required:
        return False, f"GPU 메모리 부족 (필요: {min_required}GB, 사용가능: {available_memory:.1f}GB)"
    elif available_memory < recommended:
        return True, f"실행 가능하지만 권장사양 미달 (권장: {recommended}GB, 사용가능: {available_memory:.1f}GB)"
    else:
        return True, f"최적 환경 (권장: {recommended}GB, 사용가능: {available_memory:.1f}GB)"

def get_image_files(input_dir):
    """입력 폴더에서 이미지 파일 목록 반환"""
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    image_files = []
    
    if not os.path.exists(input_dir):
        return image_files
    
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in supported_formats:
            image_files.append(os.path.join(input_dir, filename))
    
    return sorted(image_files)

def create_output_directory(base_dir, method_name):
    """출력 디렉토리 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, f"{method_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def draw_text_on_image(image_path, detected_text, output_path):
    """이미지에 인식된 텍스트를 오버레이하여 저장"""
    try:
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ 이미지 로드 실패: {image_path}")
            return False
        
        # PIL로 변환 (한글 폰트 지원)
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image_pil)
        
        # 폰트 설정 (시스템에 따라 조정 필요)
        font_size = max(16, min(30, image.shape[1] // 40))  # 이미지 크기에 따라 조정
        try:
            # Linux/WSL의 경우
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            try:
                # Windows의 경우
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    # 대체 폰트
                    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", font_size)
                except:
                    # 기본 폰트 사용
                    font = ImageFont.load_default()
        
        # 텍스트 박스 그리기
        lines = detected_text.split('\n')
        y_offset = 30
        max_width = image.shape[1] - 20  # 이미지 너비 - 여백
        
        for line in lines:
            if line.strip():
                # 긴 텍스트 줄바꿈 처리
                words = line.split()
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    text_width = bbox[2] - bbox[0]
                    
                    if text_width <= max_width:
                        current_line = test_line
                    else:
                        # 현재 줄 그리기
                        if current_line:
                            bbox = draw.textbbox((10, y_offset), current_line, font=font)
                            # 배경 박스
                            draw.rectangle([
                                bbox[0] - 5, bbox[1] - 2, 
                                bbox[2] + 5, bbox[3] + 2
                            ], fill=(0, 0, 0, 180))
                            # 텍스트
                            draw.text((10, y_offset), current_line, fill=(255, 255, 255), font=font)
                            y_offset += font_size + 5
                        
                        current_line = word
                
                # 마지막 줄 그리기
                if current_line:
                    bbox = draw.textbbox((10, y_offset), current_line, font=font)
                    # 배경 박스
                    draw.rectangle([
                        bbox[0] - 5, bbox[1] - 2, 
                        bbox[2] + 5, bbox[3] + 2
                    ], fill=(0, 0, 0, 180))
                    # 텍스트
                    draw.text((10, y_offset), current_line, fill=(255, 255, 255), font=font)
                    y_offset += font_size + 5
        
        # 다시 OpenCV 형식으로 변환하여 저장
        result_image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        success = cv2.imwrite(output_path, result_image)
        if success:
            print(f"✅ 결과 이미지 저장: {os.path.basename(output_path)}")
            return True
        else:
            print(f"❌ 이미지 저장 실패: {output_path}")
            return False
        
    except Exception as e:
        print(f"이미지 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_text_result(text, output_dir, image_filename):
    """텍스트 결과를 파일로 저장"""
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    text_file = os.path.join(output_dir, f"{base_name}_result.txt")
    
    try:
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"=== OCR 결과: {image_filename} ===\n")
            f.write(f"추출 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"텍스트 길이: {len(text)}자\n")
            f.write("-" * 50 + "\n")
            f.write(text)
            
        print(f"✅ 텍스트 파일 저장: {os.path.basename(text_file)}")
        return text_file
    except Exception as e:
        print(f"텍스트 파일 저장 중 오류: {e}")
        return None

def measure_time(func):
    """시간 측정 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        return result, elapsed_time
    return wrapper

def format_time(seconds):
    """시간을 읽기 쉬운 형식으로 변환"""
    if seconds < 60:
        return f"{seconds:.2f}초"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)}분 {seconds:.2f}초"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours)}시간 {int(minutes)}분 {seconds:.2f}초"

def print_system_info():
    """시스템 정보 출력"""
    print("\n=== 시스템 정보 ===")
    
    # CPU 정보
    print(f"CPU: {psutil.cpu_count(logical=False)}코어 {psutil.cpu_count()}스레드")
    print(f"메모리: {psutil.virtual_memory().total // (1024**3)}GB")
    
    # GPU 정보
    gpu_name, total_memory, available_memory = get_gpu_info()
    if gpu_name:
        print(f"GPU: {gpu_name}")
        print(f"GPU 메모리: {total_memory:.1f}GB (사용가능: {available_memory:.1f}GB)")
    else:
        print("GPU: 감지되지 않음")
    
    print()
