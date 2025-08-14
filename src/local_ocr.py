"""
로컬 모델을 사용한 OCR 처리 (개선된 버전)
"""

import torch
try:
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
except ImportError:
    from transformers import AutoModelForCausalLM as Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import os
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

from utils import create_output_directory, draw_text_on_image, save_text_result, measure_time

class LocalOCRProcessor:
    def __init__(self, model_id, device="auto"):
        self.model_id = model_id
        self.device = self._get_device(device)
        self.model = None
        self.processor = None
        
    def _get_device(self, device):
        """디바이스 설정"""
        if device == "auto":
            if torch.cuda.is_available():
                try:
                    # GPU 메모리 테스트
                    torch.cuda.empty_cache()
                    test_tensor = torch.tensor([1.0]).cuda()
                    del test_tensor
                    torch.cuda.empty_cache()
                    print("✅ GPU 사용 가능")
                    return "cuda"
                except Exception as e:
                    print(f"⚠️  GPU 사용 불가 ({e}), CPU로 대체")
                    return "cpu"
            else:
                print("⚠️  CUDA를 사용할 수 없음, CPU로 실행")
                return "cpu"
        return device
    
    @measure_time
    def load_model(self):
        """모델 로드"""
        print(f"모델 로딩 중: {self.model_id}")
        print(f"디바이스: {self.device}")
        
        if self.device == "cpu":
            print("⚠️  CPU 모드로 실행됩니다. 매우 느릴 수 있습니다.")
            print("⏳ 모델 로딩에 몇 분이 걸릴 수 있습니다...")
        
        try:
            # 프로세서 먼저 로드
            print("📦 프로세서 로딩 중...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            # 모델 로드
            print("🧠 모델 로딩 중...")
            
            # 디바이스별 설정
            if self.device == "cpu":
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float32,
                    device_map=None,
                    trust_remote_code=True
                )
                self.model = self.model.to("cpu")
            else:
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            
            print("✅ 모델 로딩 완료")
            return True
            
        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            
            # CPU 모드로 재시도
            if self.device == "cuda":
                print("♾️ CPU 모드로 재시도...")
                self.device = "cpu"
                return self.load_model()
            
            return False
    
    @measure_time 
    def process_image(self, image_path):
        """단일 이미지 OCR 처리"""
        try:
            if self.device == "cpu":
                print(f"⏳ CPU 모드로 처리 중: {os.path.basename(image_path)} (느릴 수 있음)")
            
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
            if self.device == "cuda":
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
            
            if self.device == "cpu":
                print(f"✅ CPU 처리 완료: {len(result)}자 추출")
            
            return result
            
        except Exception as e:
            error_msg = f"이미지 처리 중 오류: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def process_images(self, image_files, output_base_dir):
        """여러 이미지 배치 처리"""
        if not self.model:
            print("❌ 모델이 로드되지 않았습니다.")
            return False
        
        # 출력 디렉토리 생성
        model_name = self.model_id.split('/')[-1]
        output_dir = create_output_directory(output_base_dir, f"local_{model_name}")
        
        print(f"\n📁 결과 저장 폴더: {output_dir}")
        print(f"📊 처리할 이미지 수: {len(image_files)}")
        
        total_time = 0
        successful_count = 0
        results = []
        
        # 진행률 표시
        with tqdm(total=len(image_files), desc="이미지 처리중") as pbar:
            for i, image_path in enumerate(image_files):
                filename = os.path.basename(image_path)
                pbar.set_postfix({"현재": filename})
                
                try:
                    # OCR 처리
                    result_text, process_time = self.process_image(image_path)
                    total_time += process_time
                    
                    # 결과 저장
                    if result_text and not result_text.startswith("처리 실패"):
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
                        
                        print(f"✅ {filename}: {len(result_text)}자 추출")
                        
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
            f.write(f"=== 처리 결과 요약 ===\n")
            f.write(f"성공: {successful_count}/{len(image_files)} 이미지\n")
            f.write(f"총 처리 시간: {total_time:.2f}초\n")
            f.write(f"평균 처리 시간: {total_time/len(image_files):.2f}초/이미지\n\n")
            
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
        
        return True
    
    def cleanup(self):
        """메모리 정리"""
        if self.model:
            del self.model
            self.model = None
        if self.processor:
            del self.processor 
            self.processor = None
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("🧹 메모리 정리 완료")


def run_local_ocr(model_info, image_files, output_dir):
    """로컬 OCR 실행 함수"""
    processor = LocalOCRProcessor(model_info["model_id"])
    
    try:
        # 모델 로드
        success, load_time = processor.load_model()
        if not success:
            return False
        
        print(f"⏱️  모델 로딩 시간: {load_time:.2f}초")
        
        # 이미지 처리
        success = processor.process_images(image_files, output_dir)
        return success
        
    finally:
        # 메모리 정리
        processor.cleanup()
