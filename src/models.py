"""
사용 가능한 모델 정보 관리
"""

AVAILABLE_LOCAL_MODELS = {
    "qwen2.5-vl-7b": {
        "name": "Qwen2.5-VL-7B-Instruct",
        "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "params": "7B",
        "min_gpu_memory": 14,  # GB
        "recommended_gpu_memory": 16,  # GB
        "description": "최고 성능, 복잡한 이미지 처리 우수"
    },
    "qwen2.5-vl-3b": {
        "name": "Qwen2.5-VL-3B-Instruct", 
        "model_id": "Qwen/Qwen2.5-VL-3B-Instruct",
        "params": "3B",
        "min_gpu_memory": 6,
        "recommended_gpu_memory": 8,
        "description": "균형잡힌 성능, 일반적인 OCR 작업"
    },
    "qwen2.5-vl-2b": {
        "name": "Qwen2.5-VL-2B-Instruct",
        "model_id": "Qwen/Qwen2.5-VL-2B-Instruct", 
        "params": "2B",
        "min_gpu_memory": 4,
        "recommended_gpu_memory": 6,
        "description": "빠른 처리, 간단한 텍스트 인식"
    },
    "qwen2-vl-2b": {
        "name": "Qwen2-VL-2B-Instruct",
        "model_id": "Qwen/Qwen2-VL-2B-Instruct",
        "params": "2B", 
        "min_gpu_memory": 4,
        "recommended_gpu_memory": 6,
        "description": "구버전 2B 모델, 안정성 검증됨"
    }
}

CLOUD_MODELS = {
    "qwen-vl-plus": {
        "name": "Qwen-VL-Plus",
        "description": "클라우드 고성능 모델"
    },
    "qwen-vl-max": {
        "name": "Qwen-VL-Max", 
        "description": "클라우드 최고 성능 모델"
    }
}

def get_model_info(model_key, model_type="local"):
    """모델 정보 반환"""
    if model_type == "local":
        return AVAILABLE_LOCAL_MODELS.get(model_key)
    else:
        return CLOUD_MODELS.get(model_key)

def list_local_models():
    """로컬 모델 목록 반환"""
    return AVAILABLE_LOCAL_MODELS

def list_cloud_models():
    """클라우드 모델 목록 반환"""
    return CLOUD_MODELS
