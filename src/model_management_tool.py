#!/usr/bin/env python3
"""
모델 관리 도구 - 로드된 모델 확인, 정리, 성능 모니터링
"""

import os
import sys
import time
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

def show_model_status():
    """현재 모델 상태 표시"""
    print("📊 모델 매니저 상태")
    print("=" * 40)
    
    try:
        from model_manager import get_model_manager
        
        manager = get_model_manager()
        
        # 메모리 사용량
        memory_info = manager.get_memory_usage()
        print(f"🧠 메모리 사용량:")
        print(f"   로드된 모델 수: {memory_info['loaded_models']}/{memory_info['max_models']}")
        print(f"   현재 활성 모델: {memory_info.get('current_model', 'None')}")
        
        if 'gpu_memory_allocated' in memory_info:
            print(f"   GPU 메모리 할당: {memory_info['gpu_memory_allocated']:.2f}GB")
            print(f"   GPU 메모리 예약: {memory_info['gpu_memory_reserved']:.2f}GB")
        
        # 로드된 모델 목록
        loaded_models = manager.list_loaded_models()
        if loaded_models:
            print(f"\n📋 로드된 모델 목록:")
            for i, model_info in enumerate(loaded_models, 1):
                status = "🟢 활성" if model_info['is_current'] else "⚪ 대기"
                print(f"   {i}. {status} {model_info['model_id']}")
                print(f"      디바이스: {model_info['device']}")
                print(f"      마지막 사용: {time.strftime('%H:%M:%S', time.localtime(model_info['last_used']))}")
                print()
        else:
            print("\n📝 로드된 모델이 없습니다.")
            
    except Exception as e:
        print(f"❌ 모델 상태 확인 실패: {e}")

def clear_models():
    """모델 정리"""
    print("🧹 모델 정리")
    print("=" * 20)
    
    try:
        from model_manager import get_model_manager
        
        manager = get_model_manager()
        loaded_models = manager.list_loaded_models()
        
        if not loaded_models:
            print("📝 정리할 모델이 없습니다.")
            return
        
        print(f"현재 {len(loaded_models)}개의 모델이 로드되어 있습니다.")
        confirm = input("모든 모델을 정리하시겠습니까? (y/N): ").strip().lower()
        
        if confirm == 'y':
            manager.clear_all_models()
            print("✅ 모든 모델이 정리되었습니다.")
        else:
            print("취소되었습니다.")
            
    except Exception as e:
        print(f"❌ 모델 정리 실패: {e}")

def test_model_loading():
    """모델 로딩 테스트"""
    print("🧪 모델 로딩 테스트")
    print("=" * 30)
    
    from models import list_local_models
    from model_manager import get_model_manager
    
    # 사용 가능한 모델 목록
    models = list_local_models()
    print("사용 가능한 모델:")
    for i, (key, info) in enumerate(models.items(), 1):
        print(f"  {i}. {info['name']} ({info['params']})")
    
    # 모델 선택
    while True:
        try:
            choice = input(f"\n테스트할 모델을 선택하세요 (1-{len(models)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                model_keys = list(models.keys())
                selected_key = model_keys[idx]
                model_info = models[selected_key]
                break
            else:
                print(f"❌ 1-{len(models)} 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n취소되었습니다.")
            return
    
    # 모델 로드 테스트
    print(f"\n🔄 모델 로딩 테스트: {model_info['name']}")
    
    try:
        manager = get_model_manager()
        
        start_time = time.time()
        
        model, processor, device = manager.get_model(model_info['model_id'])
        
        load_time = time.time() - start_time
        
        print(f"✅ 로딩 성공!")
        print(f"⏱️  로딩 시간: {load_time:.2f}초")
        print(f"💾 디바이스: {device}")
        
        # 메모리 상태 확인
        memory_info = manager.get_memory_usage()
        if 'gpu_memory_allocated' in memory_info:
            print(f"🎮 GPU 메모리: {memory_info['gpu_memory_allocated']:.2f}GB")
        
    except Exception as e:
        print(f"❌ 로딩 실패: {e}")
        import traceback
        traceback.print_exc()

def change_settings():
    """설정 변경"""
    print("⚙️  설정 변경")
    print("=" * 20)
    
    try:
        from model_manager import get_model_manager
        
        manager = get_model_manager()
        current_max = manager.max_models
        
        print(f"현재 최대 모델 수: {current_max}")
        print("최대 모델 수를 변경할 수 있습니다. (권장: 1-3)")
        
        while True:
            try:
                new_max = input(f"새로운 최대 모델 수 (1-5, 현재: {current_max}): ").strip()
                new_max = int(new_max)
                
                if 1 <= new_max <= 5:
                    manager.change_max_models(new_max)
                    print(f"✅ 최대 모델 수가 {new_max}로 변경되었습니다.")
                    break
                else:
                    print("❌ 1-5 사이의 숫자를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n취소되었습니다.")
                return
                
    except Exception as e:
        print(f"❌ 설정 변경 실패: {e}")

def test_model_reuse():
    """모델 재사용 테스트"""
    print("🔄 모델 재사용 테스트")
    print("=" * 30)
    
    print("이 테스트는 동일한 모델을 여러 번 로드하여")
    print("두 번째부터는 빠르게 로드되는지 확인합니다.")
    
    from models import list_local_models
    from model_manager import get_model_manager
    
    # 가장 작은 모델 선택
    models = list_local_models()
    smallest_model = None
    for key, info in models.items():
        if "2B" in info['params']:
            smallest_model = info
            break
    
    if not smallest_model:
        smallest_model = list(models.values())[0]  # 첫 번째 모델
    
    print(f"테스트 모델: {smallest_model['name']}")
    
    manager = get_model_manager()
    
    # 첫 번째 로드
    print("\n1️⃣  첫 번째 로드...")
    start_time = time.time()
    
    try:
        model, processor, device = manager.get_model(smallest_model['model_id'])
        first_load_time = time.time() - start_time
        print(f"✅ 첫 번째 로드 완료: {first_load_time:.2f}초")
        
        # 두 번째 로드 (재사용)
        print("\n2️⃣  두 번째 로드 (재사용)...")
        start_time = time.time()
        
        model, processor, device = manager.get_model(smallest_model['model_id'])
        second_load_time = time.time() - start_time
        print(f"✅ 두 번째 로드 완료: {second_load_time:.2f}초")
        
        # 결과 비교
        speedup = first_load_time / second_load_time if second_load_time > 0 else float('inf')
        print(f"\n📊 결과:")
        print(f"첫 번째: {first_load_time:.2f}초")
        print(f"두 번째: {second_load_time:.2f}초")
        print(f"속도 향상: {speedup:.1f}배 빠름!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

def performance_monitor():
    """성능 모니터링"""
    print("📊 성능 모니터링")
    print("=" * 30)
    
    try:
        import torch
        import psutil
        from model_manager import get_model_manager
        
        manager = get_model_manager()
        
        print("💻 시스템 정보:")
        print(f"   CPU 사용률: {psutil.cpu_percent():.1f}%")
        print(f"   메모리 사용률: {psutil.virtual_memory().percent:.1f}%")
        
        if torch.cuda.is_available():
            print(f"\n🎮 GPU 정보:")
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                memory_allocated = torch.cuda.memory_allocated(i) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(i) / 1024**3
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                
                print(f"   GPU {i}: {gpu_name}")
                print(f"   할당된 메모리: {memory_allocated:.2f}GB")
                print(f"   예약된 메모리: {memory_reserved:.2f}GB")
                print(f"   전체 메모리: {memory_total:.2f}GB")
                print(f"   사용률: {(memory_reserved/memory_total)*100:.1f}%")
        else:
            print("\n⚠️  GPU를 사용할 수 없습니다.")
        
        # 모델 매니저 정보
        memory_info = manager.get_memory_usage()
        print(f"\n🧠 모델 매니저:")
        print(f"   로드된 모델: {memory_info['loaded_models']}/{memory_info['max_models']}")
        
        loaded_models = manager.list_loaded_models()
        if loaded_models:
            for model_info in loaded_models:
                status = "🔴 활성" if model_info['is_current'] else "⚪ 대기"
                print(f"   {status} {model_info['model_id'].split('/')[-1]} ({model_info['device']})")
        
    except Exception as e:
        print(f"❌ 성능 모니터링 실패: {e}")

def main():
    """메인 함수"""
    while True:
        print("\n🛠️  모델 관리 도구")
        print("=" * 25)
        print("1. 모델 상태 확인")
        print("2. 모델 정리")
        print("3. 모델 로딩 테스트")
        print("4. 모델 재사용 테스트")
        print("5. 성능 모니터링")
        print("6. 설정 변경")
        print("7. 종료")
        
        choice = input("\n선택하세요 (1-7): ").strip()
        
        if choice == "1":
            show_model_status()
        elif choice == "2":
            clear_models()
        elif choice == "3":
            test_model_loading()
        elif choice == "4":
            test_model_reuse()
        elif choice == "5":
            performance_monitor()
        elif choice == "6":
            change_settings()
        elif choice == "7":
            print("👋 모델 관리 도구를 종료합니다.")
            break
        else:
            print("❌ 1-7 사이의 숫자를 입력해주세요.")
        
        # 잠시 대기
        input("\n계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    main()
