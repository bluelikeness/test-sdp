"""
메인 대화식 인터페이스
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from models import list_local_models, list_cloud_models, get_model_info
from utils import (
    get_gpu_info, check_model_compatibility, get_image_files, 
    print_system_info, format_time
)
from local_ocr_improved import LocalOCRProcessor, get_loaded_models_info, clear_all_models, get_memory_info
from cloud_ocr import run_cloud_ocr

class OCRTestInterface:
    def __init__(self):
        self.input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        self.api_key = os.getenv('QWEN_API_KEY')
        
    def show_main_menu(self):
        """메인 메뉴 표시"""
        print("\n" + "="*50)
        print("🔍 OCR 성능 테스트 도구")
        print("="*50)
        
        # 시스템 정보 출력
        print_system_info()
        
        # 입력 이미지 확인
        image_files = get_image_files(self.input_dir)
        print(f"📁 입력 이미지: {len(image_files)}개")
        
        if len(image_files) == 0:
            print("⚠️  input 폴더에 이미지 파일이 없습니다.")
            print(f"   경로: {os.path.abspath(self.input_dir)}")
            print("   지원 형식: jpg, jpeg, png, bmp, tiff, webp")
            return None
        
        # 메뉴 옵션
        print("\n📋 메뉴:")
        print("1. 로컬 모델 사용")
        print("2. Qwen Cloud API 사용") 
        print("3. 설정 확인")
        print("4. 모델 관리 도구")
        print("5. 종료")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-5): ").strip()
                if choice in ['1', '2', '3', '4', '5']:
                    return choice
                else:
                    print("❌ 1-5 사이의 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                return '5'
    
    def show_local_model_menu(self):
        """로컬 모델 선택 메뉴"""
        print("\n" + "="*60)
        print("🖥️  로컬 모델 선택")
        print("="*60)
        
        # GPU 정보 표시
        gpu_name, total_memory, available_memory = get_gpu_info()
        if gpu_name:
            print(f"🎮 GPU: {gpu_name}")
            print(f"💾 GPU 메모리: {total_memory:.1f}GB (사용가능: {available_memory:.1f}GB)")
        else:
            print("⚠️  GPU를 찾을 수 없습니다. CPU 모드로 실행됩니다.")
        
        print()
        
        # 모델 목록 표시
        models = list_local_models()
        model_keys = list(models.keys())
        
        for i, (key, info) in enumerate(models.items(), 1):
            print(f"{i}. {info['name']}")
            print(f"   📊 파라미터: {info['params']}")
            print(f"   💾 최소 GPU 메모리: {info['min_gpu_memory']}GB | 권장: {info['recommended_gpu_memory']}GB")
            
            # 호환성 체크
            compatible, message = check_model_compatibility(info)
            if compatible:
                if "최적" in message:
                    print(f"   ✅ {message}")
                else:
                    print(f"   ⚠️  {message}")
            else:
                print(f"   ❌ {message}")
            
            print(f"   📝 {info['description']}")
            print()
        
        print(f"{len(models) + 1}. 사용자 정의 모델 경로")
        print(f"{len(models) + 2}. CPU 모드로 실행 (느리지만 안전)")
        print(f"{len(models) + 3}. 뒤로 가기")
        
        while True:
            try:
                choice = input(f"\n선택하세요 (1-{len(models) + 3}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(models):
                    selected_key = model_keys[choice_num - 1]
                    return 'model', selected_key
                elif choice_num == len(models) + 1:
                    return 'custom', None
                elif choice_num == len(models) + 2:
                    return 'cpu', None
                elif choice_num == len(models) + 3:
                    return 'back', None
                else:
                    print(f"❌ 1-{len(models) + 3} 사이의 숫자를 입력해주세요.")
                    
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                return 'back', None
    
    def show_cloud_model_menu(self):
        """클라우드 모델 선택 메뉴"""
        print("\n" + "="*60)
        print("☁️  Qwen Cloud API 모델 선택")
        print("="*60)
        
        # API 키 확인
        if not self.api_key or self.api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않았습니다.")
            print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
            input("\n계속하려면 Enter를 누르세요...")
            return 'back', None
        
        print(f"🔑 API 키: {'*' * (len(self.api_key) - 8) + self.api_key[-8:]}")
        print()
        
        # 모델 목록 표시
        models = list_cloud_models()
        model_keys = list(models.keys())
        
        for i, (key, info) in enumerate(models.items(), 1):
            print(f"{i}. {info['name']}")
            print(f"   📝 {info['description']}")
            print()
        
        print(f"{len(models) + 1}. 뒤로 가기")
        
        while True:
            try:
                choice = input(f"\n선택하세요 (1-{len(models) + 1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(models):
                    selected_key = model_keys[choice_num - 1]
                    return 'model', selected_key
                elif choice_num == len(models) + 1:
                    return 'mode_select', None
                elif choice_num == len(models) + 2:
                    return 'back', None
                else:
                    print(f"❌ 1-{len(models) + 2} 사이의 숫자를 입력해주세요.")
                    
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                return 'back', None
    
    def show_ocr_mode_menu(self):
        """추출 모드 선택 메뉴"""
        print("\n" + "="*60)
        print("🎯 OCR 모드 선택")
        print("="*60)
        
        print("1. 손그림 도형 감지 모드")
        print("   - 원, 타원, 사각형 등으로 둘러싸인 텍스트만 추출")
        print("   - 스캔문서에서 특정 영역만 인식하고 싶을 때 사용")
        print("   - 예: 시헗지에서 채점할 문제만 추출")
        print()
        print("2. 하이브리드 모드 (추천!) 🎆")
        print("   - OpenCV로 도형 위치 찾기 + AI로 각 영역 텍스트 추출")
        print("   - 최고 정확도: 12개 도형 모두 인식 가능")
        print("   - 중기 개선: 컴퓨터 비전 + AI 조합")
        print()
        print("3. 일반 텍스트 추출 모드")
        print("   - 이미지의 모든 텍스트를 추출")
        print("   - 좌표값 오류 방지를 위한 개선된 프롬프트 사용")
        print("   - 일반적인 OCR 작업에 사용")
        print()
        print("4. 뒤로 가기")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-4): ").strip()
                
                if choice == '1':
                    return 'shape_detection'
                elif choice == '2':
                    return 'hybrid'
                elif choice == '3':
                    return 'general'
                elif choice == '4':
                    return 'back'
                else:
                    print("❌ 1-4 사이의 숫자를 입력해주세요.")
                    
            except KeyboardInterrupt:
                return 'back'
    
    def show_settings(self):
        """설정 정보 표시"""
        print("\n" + "="*50)
        print("⚙️  현재 설정")
        print("="*50)
        
        # 환경 변수
        print("📁 경로 설정:")
        print(f"   입력 폴더: {os.path.abspath(self.input_dir)}")
        print(f"   출력 폴더: {os.path.abspath(self.output_dir)}")
        
        print("\n🔑 API 설정:")
        if self.api_key and self.api_key != "your_api_key_here":
            print(f"   API 키: {'*' * (len(self.api_key) - 8) + self.api_key[-8:]}")
        else:
            print("   API 키: ❌ 설정되지 않음")
        
        # 시스템 정보
        print_system_info()
        
        # 모델 매니저 정보
        print("\n🧠 모델 매니저:")
        try:
            memory_info = get_memory_info()
            print(f"   로드된 모델: {memory_info['loaded_models']}/{memory_info['max_models']}")
            
            loaded_models = get_loaded_models_info()
            if loaded_models:
                print("   현재 로드된 모델들:")
                for model_info in loaded_models:
                    status = "🔴" if model_info['is_current'] else "⚪"
                    model_name = model_info['model_id'].split('/')[-1]
                    print(f"     {status} {model_name} ({model_info['device']})")
            else:
                print("   로드된 모델 없음")
                
            if 'gpu_memory_allocated' in memory_info:
                print(f"   GPU 메모리 사용량: {memory_info['gpu_memory_allocated']:.2f}GB")
        except Exception as e:
            print(f"   모델 매니저 정보 얻기 실패: {e}")
        
        # 입력 이미지 정보
        image_files = get_image_files(self.input_dir)
        print(f"📊 입력 이미지: {len(image_files)}개")
        if image_files:
            print("   파일 목록:")
            for img in image_files[:5]:  # 최대 5개만 표시
                print(f"   - {os.path.basename(img)}")
            if len(image_files) > 5:
                print(f"   ... 외 {len(image_files) - 5}개")
        
        input("\n계속하려면 Enter를 누르세요...")
    
    def handle_custom_model(self):
        """사용자 정의 모델 경로 처리"""
        print("\n사용자 정의 모델 경로를 입력하세요:")
        print("예: Qwen/Qwen2.5-VL-1.5B-Instruct")
        
        model_path = input("모델 경로: ").strip()
        if not model_path:
            return None
        
        # 사용자 정의 모델 정보 생성
        custom_info = {
            "name": f"Custom: {model_path}",
            "model_id": model_path,
            "params": "Unknown",
            "min_gpu_memory": 0,
            "recommended_gpu_memory": 0,
            "description": "사용자 정의 모델"
        }
        
        return custom_info
    
    def _run_local_with_processor(self, processor, image_files):
        """로컬 모델 프로세서로 직접 실행"""
        try:
            # 모델 로드
            success, load_time = processor.load_model()
            if not success:
                print("❌ 모델 로딩에 실패했습니다.")
                return
            
            print(f"⏱️  모델 로딩 시간: {load_time:.2f}초")
            
            # 이미지 처리
            success = processor.process_images(image_files, self.output_dir)
            
            if success:
                print("\n✅ 로컬 모델 처리가 완료되었습니다!")
            else:
                print("\n❌ 처리 중 오류가 발생했습니다.")
                
        finally:
            # 메모리 정리
            processor.cleanup()
    
    def run_local_processing(self, model_info):
        """로컬 모델 처리 실행 - 개선된 버전"""
        print(f"\n🚀 로컬 모델 처리 시작: {model_info['name']}")
        
        # 이미지 파일 가져오기
        image_files = get_image_files(self.input_dir)
        
        if not image_files:
            print("❌ 처리할 이미지가 없습니다.")
            return
        
        # 확인 메시지
        print(f"📊 처리할 이미지: {len(image_files)}개")
        
        # 모델 매니저 상태 표시
        try:
            memory_info = get_memory_info()
            loaded_models = get_loaded_models_info()
            
            if loaded_models:
                print(f"♾️  현재 로드된 모델: {len(loaded_models)}개")
                for model in loaded_models:
                    status = "🔴 활성" if model['is_current'] else "⚪ 대기"
                    print(f"   {status} {model['model_id'].split('/')[-1]}")
            else:
                print("🆕 로드된 모델 없음 - 새로 로드됨")
        except Exception:
            pass
        
        confirm = input("처리를 시작하시겠습니까? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("처리가 취소되었습니다.")
            return
        
        # OCR 처리 실행 (개선된 버전)
        from local_ocr_improved import run_local_ocr
        success = run_local_ocr(model_info, image_files, self.output_dir)
        
        if success:
            print("\n✅ 로컬 모델 처리가 완료되었습니다!")
            
            # 처리 후 모델 상태 표시
            try:
                updated_models = get_loaded_models_info()
                print(f"🧠 처리 후 로드된 모델: {len(updated_models)}개")
            except Exception:
                pass
        else:
            print("\n❌ 처리 중 오류가 발생했습니다.")
    
    def open_model_management(self):
        """모델 관리 도구 열기"""
        print("\n🛠️  모델 관리 도구를 엽니다...")
        
        try:
            # 모델 관리 도구 실행
            from model_management_tool import main as model_tool_main
            model_tool_main()
        except ImportError:
            print("❌ 모델 관리 도구를 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ 모델 관리 도구 실행 오류: {e}")
    
    def run_cloud_processing(self, model_name, ocr_mode="shape_detection"):
        """클라우드 API 처리 실행 - 모드 지원"""
        print(f"\n🌐 클라우드 API 처리 시작: {model_name}")
        print(f"🎯 OCR 모드: {ocr_mode}")
        
        # 이미지 파일 가져오기
        image_files = get_image_files(self.input_dir)
        
        if not image_files:
            print("❌ 처리할 이미지가 없습니다.")
            return
        
        # 모드별 설명
        if ocr_mode == "shape_detection":
            mode_desc = "손그림 도형으로 둘러싸인 텍스트만 추출"
        elif ocr_mode == "hybrid":
            mode_desc = "하이브리드 모드: OpenCV 도형 감지 + AI 텍스트 추출 (최고 정확도)"
        else:
            mode_desc = "모든 텍스트 추출 (좌표값 오류 방지 프롬프트 적용)"
        
        # 확인 메시지
        print(f"📊 처리할 이미지: {len(image_files)}개")
        print(f"💰 예상 API 호출 수: {len(image_files)}회")
        print(f"🎯 추출 모드: {mode_desc}")
        
        confirm = input("처리를 시작하시겠습니까? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("처리가 취소되었습니다.")
            return
        
        # OCR 처리 실행
        success = run_cloud_ocr(self.api_key, model_name, image_files, self.output_dir, ocr_mode)
        
        if success:
            print("\n✅ 클라우드 API 처리가 완료되었습니다!")
        else:
            print("\n❌ 처리 중 오류가 발생했습니다.")
    
    def run(self):
        """메인 실행 루프"""
        print("🚀 OCR 성능 테스트 도구 시작")
        
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':  # 로컬 모델
                while True:
                    action, data = self.show_local_model_menu()
                    
                    if action == 'back':
                        break
                    elif action == 'model':
                        model_info = get_model_info(data, "local")
                        self.run_local_processing(model_info)
                        break
                    elif action == 'custom':
                        model_info = self.handle_custom_model()
                        if model_info:
                            self.run_local_processing(model_info)
                        break
                    elif action == 'cpu':
                        # CPU 로 실행할 모델 선택
                        print("\n⚠️  CPU 모드 설정")
                        print("⏳ CPU 모드는 매우 느립니다. 그래도 계속하시겠습니까?")
                        confirm = input("계속 (y/N): ").strip().lower()
                        if confirm == 'y':
                            # 기본 3B 모델을 CPU로 실행
                            model_info = get_model_info("qwen2.5-vl-3b", "local")
                            # 디바이스를 CPU로 강제 설정
                            processor = LocalOCRProcessor(model_info["model_id"], device="cpu")
                            image_files = get_image_files(self.input_dir)
                            if image_files:
                                print(f"📊 처리할 이미지: {len(image_files)}개")
                                confirm2 = input("처리를 시작하시겠습니까? (y/N): ").strip().lower()
                                if confirm2 == 'y':
                                    self._run_local_with_processor(processor, image_files)
                        break
            
            elif choice == '2':  # 클라우드 API
                current_mode = "hybrid"  # 기본 모드를 하이브리드로 변경
                
                while True:
                    action, data = self.show_cloud_model_menu()
                    
                    if action == 'back':
                        break
                    elif action == 'model':
                        self.run_cloud_processing(data, current_mode)
                        break
                    elif action == 'mode_select':
                        # 모드 선택 메뉴
                        selected_mode = self.show_ocr_mode_menu()
                        if selected_mode != 'back':
                            current_mode = selected_mode
                            print(f"✅ OCR 모드가 '{current_mode}'로 설정되었습니다.")
                            input("다음으로 계속하려면 Enter를 누르세요...")
            
            elif choice == '3':  # 설정 확인
                self.show_settings()
            
            elif choice == '4':  # 모델 관리 도구
                self.open_model_management()
            
            elif choice == '5':  # 종료
                print("\n👋 프로그램을 종료합니다.")
                break


def main():
    """메인 함수"""
    try:
        interface = OCRTestInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
