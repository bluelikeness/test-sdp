# 📖 영역 선택 UI + OCR 도구 사용법

## 🎯 개요

이 도구들은 이미지에서 사용자가 직접 영역을 선택하여 OCR 처리를 할 수 있게 해줍니다.

## 🛠️ 만들어진 도구들

### 1. `region_selector_ui.py` - 영역 선택 UI
- 마우스로 드래그하여 관심 영역 선택
- 여러 영역 선택 가능
- 선택된 영역을 개별 이미지로 저장

### 2. `region_ocr_integrated.py` - 영역 선택 + OCR 통합
- 영역 선택 후 바로 OCR 처리
- 각 영역별로 텍스트 추출
- 결과를 다양한 형식으로 저장

### 3. `run_region_tool.py` - 간단 실행기
- 메뉴 방식으로 도구 선택 실행

## 🚀 사용법

### 방법 1: 간단 실행기 사용 (추천)
```bash
cd /home/kckang/work/test-sdp
python3 run_region_tool.py
```

### 방법 2: 개별 도구 직접 실행

#### 영역 선택만:
```bash
python3 region_selector_ui.py [이미지_경로]
python3 region_selector_ui.py input/17301.png
```

#### 영역 선택 + OCR:
```bash
python3 region_ocr_integrated.py [이미지_경로]
python3 region_ocr_integrated.py input/17301.png
```

## 🖱️ UI 조작법

### 마우스 조작:
- **좌클릭 + 드래그**: 영역 선택
- **ESC**: 종료

### 키보드 조작:
- **'c'**: 선택된 영역들 크롭
- **'s'**: 영역 정보 저장 (JSON)
- **'r'**: 모든 영역 초기화
- **'d'**: 마지막 영역 삭제
- **'h'**: 도움말 다시 보기

## 📁 출력 파일

### `output/cropped_regions/` 폴더에 저장:
- `이미지명_영역명_타임스탬프.png` - 크롭된 개별 영역 이미지
- `이미지명_ocr_results_타임스탬프.txt` - OCR 결과 상세 정보
- `이미지명_ocr_results_타임스탬프.json` - OCR 결과 JSON 데이터
- `이미지명_all_text_타임스탬프.txt` - 추출된 모든 텍스트

### `output/region_info/` 폴더에 저장:
- `이미지명_regions_타임스탬프.json` - 영역 좌표 정보

## 🔧 기술적 특징

### 1. 좌표 변환
- 화면 표시용 좌표 ↔ 원본 이미지 좌표 자동 변환
- 큰 이미지도 화면에 맞게 스케일링

### 2. OCR 처리
- 원형/타원형 도형 내 텍스트 특화 인식
- measure_time 데코레이터의 tuple 반환값 안전 처리
- 의미없는 응답 자동 필터링

### 3. 결과 저장
- 다양한 형식으로 결과 저장 (TXT, JSON)
- 타임스탬프로 버전 관리
- 영역 정보 재사용 가능

## 💡 사용 시나리오

### 시나리오 1: 새로운 이미지 처리
1. `region_ocr_integrated.py` 실행
2. 마우스로 관심 영역들 선택
3. 'c' 키로 크롭 + OCR 자동 처리
4. 결과 확인

### 시나리오 2: 영역만 선택 (OCR 나중에)
1. `region_selector_ui.py` 실행
2. 영역 선택 후 's' 키로 정보 저장
3. 나중에 JSON 파일로 OCR 처리:
   ```bash
   python3 region_ocr_integrated.py output/region_info/파일명.json
   ```

### 시나리오 3: 여러 설정 테스트
1. 같은 이미지로 다른 영역 선택
2. 각각 다른 타임스탬프로 결과 저장
3. 결과 비교 분석

## 🔍 문제 해결

### OpenCV 오류:
```bash
pip install opencv-python
```

### API 키 오류:
`.env` 파일에 `QWEN_API_KEY=실제키` 설정

### 이미지 표시 문제:
- WSL의 경우 X11 forwarding 설정 필요
- 또는 Windows에서 실행

## 📊 이전 자동 도구들과 비교

| 도구 | 장점 | 단점 |
|------|------|------|
| **UI 영역 선택** | 정확한 영역 지정, 사용자 제어 | 수동 작업 필요 |
| 그리드 자동 분할 | 빠른 처리, 자동화 | 불필요한 영역 포함 |
| AI 위치 분석 | 지능적 분할 | 분석 정확도 의존 |

## 🎯 권장 워크플로우

1. **첫 시도**: UI 영역 선택으로 정확한 영역 파악
2. **반복 작업**: 영역 정보 저장 후 재사용
3. **비교 분석**: 여러 방법 결과 비교
4. **최적화**: 가장 좋은 결과의 설정 기록

---

💡 **Tip**: 영역을 너무 작게 선택하면 OCR 정확도가 떨어질 수 있습니다. 텍스트 주변에 여백을 포함해서 선택하는 것이 좋습니다.
