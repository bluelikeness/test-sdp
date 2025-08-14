"""
개선된 로컬 모델 OCR 처리 - 모델 재사용
"""

import torch
from PIL import Image
import os
import time
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

from utils import create_output_directory, draw_text_on_image, save_text_result, measure_time
from model_manager import get_model_manager

class LocalOCRProcessor:
    def __init__(self, model_id, device="auto"):
        self.model_id = model_id
        self.device = device
        self.model_manager = get_model_manager()
        self.model = None
        self.processor = None
        self.actual_device = None
        
    def ensure_model_loaded(self):
        """모델이 로드되어 있는지 확인하고, 없으면 로드"""
        try:
            self.model, self.processor, self.actual_device = self.model_manager.get_model(
                self.model_id, 
                self.device
            )
            return True
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            return False
    
    def process_image(self, image_path):
        """단일 이미지 OCR 처리"""
        if not self.ensure_model_loaded():
            return "모델 로드 실패"
        
        try:
            if self.actual_device == "cpu":
                print(f"⏳ CPU 모드로 처리 중: {os.path.basename(image_path)}")
            
            # 이미지 로드
            image = Image.open(image_path).convert('RGB')
            
            # 간단한 프롬프트
            prompt = "Find all text that has been manually circled with oval/elliptical pen marks and extract only those text items. Output only the results without any explanation or additional text."

            # Qwen2-VL 전용 입력 형식
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # 프로세서로 입력 처리
            text = self.processor.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            inputs = self.processor(
                text=[text],
                images=[image], 
                padding=True,
                return_tensors="pt"
            )
            
            # 디바이스로 이동
            if self.actual_device == "cuda":
                inputs = inputs.to("cuda")
            
            # 추론 실행
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=False,
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
            
            # 결과 디코딩
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0]
            
            result = output_text.strip()
            
            if self.actual_device == "cpu":
                print(f"✅ CPU 처리 완료: {len(result)}자 추출")
            
            return result
            
        except Exception as e:
            error_msg = f"이미지 처리 중 오류: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    @measure_time
    def process_images(self, image_files, output_base_dir):
        """여러 이미지 배치 처리 - 모델 재사용"""
        if not self.ensure_model_loaded():
            print("❌ 모델이 로드되지 않았습니다.")
            return False
        
        # 출력 디렉토리 생성
        model_name = self.model_id.split('/')[-1]
        output_dir = create_output_directory(output_base_dir, f"local_{model_name}")
        
        print(f"\n📁 결과 저장 폴더: {output_dir}")
        print(f"📊 처리할 이미지 수: {len(image_files)}")
        print(f"🧠 사용 모델: {self.model_id}")
        print(f"💾 디바이스: {self.actual_device}")
        
        # 메모리 사용량 표시
        memory_info = self.model_manager.get_memory_usage()
        print(f"📈 현재 로드된 모델 수: {memory_info['loaded_models']}/{memory_info['max_models']}")
        
        total_time = 0
        successful_count = 0
        results = []
        
        # 진행률 표시
        with tqdm(total=len(image_files), desc="이미지 처리중") as pbar:
            for i, image_path in enumerate(image_files):
                filename = os.path.basename(image_path)
                pbar.set_postfix({"현재": filename})
                
                try:
                    # OCR 처리 (시간 측정)
                    start_time = time.time()
                    result_text = self.process_image(image_path)
                    process_time = time.time() - start_time
                    total_time += process_time
                    
                    # 결과 저장
                    if result_text and not result_text.startswith("모델 로드 실패") and not result_text.startswith("이미지 처리 중 오류"):
                        successful_count += 1
                        
                        # 텍스트 파일 저장
                        text_file = save_text_result(result_text, output_dir, filename)
                        
                        # 결과 이미지 생성
                        base_name = os.path.splitext(filename)[0]
                        output_image_path = os.path.join(output_dir, f"{base_name}_result.png")
                        success = draw_text_on_image(image_path, result_text, output_image_path)
                        
                        # 텍스트 좌표 매핑 이미지 생성
                        try:
                            from text_coordinate_mapping import create_text_coordinate_mapping
                            coord_success = create_text_coordinate_mapping(
                                image_path, result_text, output_dir, method="auto"
                            )
                            if coord_success:
                                print(f"🎯 좌표 매핑 이미지 생성 완료")
                        except Exception as coord_error:
                            print(f"⚠️  좌표 매핑 오류: {coord_error}")
                        
                        results.append({
                            'file': filename,
                            'success': True,
                            'text_length': len(result_text),
                            'time': process_time
                        })
                        
                        print(f"✅ {filename}: {len(result_text)}자 추출 ({process_time:.2f}초)")
                        
                    else:
                        print(f"⚠️  실패: {filename} - {result_text}")
                        results.append({
                            'file': filename,
                            'success': False,
                            'error': result_text,
                            'time': process_time
                        })
                
                except Exception as e:
                    print(f"❌ 오류: {filename} - {str(e)}")
                    results.append({
                        'file': filename,
                        'success': False,
                        'error': str(e),
                        'time': 0
                    })
                
                pbar.update(1)
        
        # 결과 요약 저장
        summary_path = os.path.join(output_dir, "summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 로컬 모델 처리 결과 요약 ===\n")
            f.write(f"모델: {self.model_id}\n")
            f.write(f"디바이스: {self.actual_device}\n")
            f.write(f"성공: {successful_count}/{len(image_files)} 이미지\n")
            f.write(f"총 처리 시간: {total_time:.2f}초\n")
            f.write(f"평균 처리 시간: {total_time/len(image_files):.2f}초/이미지\n\n")
            
            # 메모리 정보
            f.write(f"=== 메모리 사용 정보 ===\n")
            memory_info = self.model_manager.get_memory_usage()
            for key, value in memory_info.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            for result in results:
                f.write(f"파일: {result['file']}\n")
                f.write(f"성공: {'예' if result['success'] else '아니오'}\n")
                if result['success']:
                    f.write(f"추출 텍스트 길이: {result['text_length']}자\n")
                else:
                    f.write(f"오류: {result.get('error', 'Unknown')}\n")
                f.write(f"처리 시간: {result['time']:.2f}초\n")
                f.write("-" * 30 + "\n")
        
        # 결과 요약
        print(f"\n=== 처리 완료 ===")
        print(f"성공: {successful_count}/{len(image_files)} 이미지")
        print(f"총 처리 시간: {total_time:.2f}초")
        print(f"평균 처리 시간: {total_time/len(image_files):.2f}초/이미지")
        print(f"결과 저장 위치: {output_dir}")
        
        # 모델 재사용 상태 표시
        loaded_models = self.model_manager.list_loaded_models()
        print(f"🔄 모델 상태: {len(loaded_models)}개 모델이 메모리에 로드됨")
        
        return True
    
    def cleanup(self):
        """모델은 매니저가 관리하므로 여기서는 참조만 정리"""
        self.model = None
        self.processor = None
        self.actual_device = None
        print("🔗 모델 참조 정리 완료 (모델은 매니저가 유지)")


def run_local_ocr(model_info, image_files, output_dir):
    """로컬 OCR 실행 함수 - 개선된 버전"""
    processor = LocalOCRProcessor(model_info["model_id"])
    
    try:
        # 모델 로드 (매니저를 통해)
        if not processor.ensure_model_loaded():
            return False
        
        print(f"♻️  모델 준비 완료: {model_info['name']}")
        
        # 이미지 처리
        success, process_time = processor.process_images(image_files, output_dir)
        
        print(f"⏱️  전체 처리 시간: {process_time:.2f}초")
        
        return success
        
    finally:
        # 모델은 매니저가 관리하므로 참조만 정리
        processor.cleanup()

if __name__ == "__main__":
    # 테스트
    print("🧪 개선된 로컬 OCR 테스트")
    
    # 메모리 정보 확인
    print("메모리 정보:", get_memory_info())
    
    # 로드된 모델 확인
    print("로드된 모델들:", get_loaded_models_info())


# 메모리 관리를 위한 추가 함수들
def get_loaded_models_info():
    """현재 로드된 모델 정보 반환"""
    manager = get_model_manager()
    return manager.list_loaded_models()

def clear_all_models():
    """모든 모델을 메모리에서 정리"""
    manager = get_model_manager()
    manager.clear_all_models()

def get_memory_info():
    """메모리 사용량 정보 반환"""
    manager = get_model_manager()
    return manager.get_memory_usage()

def run_local_ocr(model_info, image_files, output_dir):
    """로컬 OCR 실행 함수 - 개선된 버전"""
    processor = LocalOCRProcessor(model_info["model_id"])
    
    try:
        # 모델 로드 (매니저를 통해)
        if not processor.ensure_model_loaded():
            return False
        
        print(f"♾️  모델 준비 완료: {model_info['name']}")
        
        # 이미지 처리
        success, process_time = processor.process_images(image_files, output_dir)
        
        print(f"⏱️  전체 처리 시간: {process_time:.2f}초")
        
        return success
        
    finally:
        # 모델은 매니저가 관리하므로 참조만 정리
        processor.cleanup()
