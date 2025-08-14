"""
효율적인 모델 관리자 - 싱글톤 패턴으로 모델 재사용
"""

import torch
import os
from typing import Optional, Dict, Any
import threading
import time

try:
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
except ImportError:
    from transformers import AutoModelForCausalLM as Qwen2VLForConditionalGeneration, AutoProcessor

class ModelManager:
    """
    싱글톤 패턴으로 모델을 관리하는 클래스
    한 번 로드된 모델을 메모리에 유지하고 재사용
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.models = {}  # {model_id: {'model': model, 'processor': processor, 'device': device, 'last_used': time}}
            self.current_model_id = None
            self.max_models = 2  # 최대 2개 모델까지 메모리에 유지
            self.initialized = True
            print("🔧 모델 매니저 초기화 완료")
    
    def _get_device(self, device="auto"):
        """디바이스 설정"""
        if device == "auto":
            if torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                    test_tensor = torch.tensor([1.0]).cuda()
                    del test_tensor
                    torch.cuda.empty_cache()
                    return "cuda"
                except Exception:
                    return "cpu"
            else:
                return "cpu"
        return device
    
    def get_model(self, model_id: str, device: str = "auto", force_reload: bool = False):
        """
        모델을 가져오거나 로드함
        
        Args:
            model_id: 모델 식별자 (예: "Qwen/Qwen2.5-VL-3B-Instruct")
            device: 디바이스 ("auto", "cuda", "cpu")
            force_reload: 강제로 다시 로드할지 여부
        
        Returns:
            (model, processor, actual_device) 튜플
        """
        actual_device = self._get_device(device)
        cache_key = f"{model_id}_{actual_device}"
        
        # 이미 로드된 모델이 있고 강제 리로드가 아니면 재사용
        if cache_key in self.models and not force_reload:
            model_info = self.models[cache_key]
            model_info['last_used'] = time.time()
            self.current_model_id = cache_key
            
            print(f"♻️  기존 모델 재사용: {model_id}")
            print(f"📍 디바이스: {actual_device}")
            
            return model_info['model'], model_info['processor'], actual_device
        
        # 새로 로드해야 하는 경우
        print(f"🔄 새 모델 로딩: {model_id}")
        print(f"📍 디바이스: {actual_device}")
        
        if actual_device == "cpu":
            print("⚠️  CPU 모드로 실행됩니다. 매우 느릴 수 있습니다.")
            print("⏳ 모델 로딩에 몇 분이 걸릴 수 있습니다...")
        
        try:
            # 메모리 정리 (필요시)
            self._cleanup_old_models()
            
            # 프로세서 로드
            print("📦 프로세서 로딩 중...")
            processor = AutoProcessor.from_pretrained(
                model_id,
                trust_remote_code=True
            )
            
            # 모델 로드
            print("🧠 모델 로딩 중...")
            if actual_device == "cpu":
                model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32,
                    device_map=None,
                    trust_remote_code=True
                )
                model = model.to("cpu")
            else:
                model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            
            # 캐시에 저장
            self.models[cache_key] = {
                'model': model,
                'processor': processor,
                'device': actual_device,
                'last_used': time.time(),
                'model_id': model_id
            }
            
            self.current_model_id = cache_key
            
            print("✅ 모델 로딩 완료")
            return model, processor, actual_device
            
        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            
            # GPU 실패 시 CPU로 재시도
            if actual_device == "cuda":
                print("♾️ CPU 모드로 재시도...")
                return self.get_model(model_id, "cpu", force_reload)
            
            raise e
    
    def _cleanup_old_models(self):
        """오래된 모델들을 메모리에서 정리"""
        if len(self.models) >= self.max_models:
            # 가장 오래 사용되지 않은 모델 찾기
            oldest_key = min(self.models.keys(), 
                           key=lambda k: self.models[k]['last_used'])
            
            print(f"🧹 오래된 모델 정리: {self.models[oldest_key]['model_id']}")
            
            # 모델 정리
            model_info = self.models[oldest_key]
            del model_info['model']
            del model_info['processor']
            del self.models[oldest_key]
            
            # GPU 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def list_loaded_models(self):
        """현재 로드된 모델들의 정보 반환"""
        result = []
        for cache_key, model_info in self.models.items():
            result.append({
                'cache_key': cache_key,
                'model_id': model_info['model_id'],
                'device': model_info['device'],
                'last_used': model_info['last_used'],
                'is_current': cache_key == self.current_model_id
            })
        return result
    
    def clear_all_models(self):
        """모든 모델을 메모리에서 정리"""
        print("🧹 모든 모델 정리 중...")
        for model_info in self.models.values():
            del model_info['model']
            del model_info['processor']
        
        self.models.clear()
        self.current_model_id = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("✅ 모든 모델 정리 완료")
    
    def get_memory_usage(self):
        """메모리 사용량 정보 반환"""
        info = {
            'loaded_models': len(self.models),
            'max_models': self.max_models,
            'current_model': self.current_model_id
        }
        
        if torch.cuda.is_available():
            info['gpu_memory_allocated'] = torch.cuda.memory_allocated() / 1024**3  # GB
            info['gpu_memory_reserved'] = torch.cuda.memory_reserved() / 1024**3    # GB
        
        return info
    
    def change_max_models(self, max_models: int):
        """최대 모델 수 변경"""
        old_max = self.max_models
        self.max_models = max_models
        
        # 현재 로드된 모델이 새로운 최대값보다 많으면 정리
        while len(self.models) > self.max_models:
            self._cleanup_old_models()
        
        print(f"📊 최대 모델 수 변경: {old_max} → {max_models}")


# 전역 모델 매니저 인스턴스
model_manager = ModelManager()


def get_model_manager():
    """모델 매니저 인스턴스 반환"""
    return model_manager


if __name__ == "__main__":
    # 테스트
    print("🧪 모델 매니저 테스트")
    
    manager = get_model_manager()
    
    # 메모리 사용량 확인
    print("메모리 사용량:", manager.get_memory_usage())
    
    # 로드된 모델 목록
    print("로드된 모델들:", manager.list_loaded_models())
