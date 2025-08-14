#!/usr/bin/env python3
"""
UI 기반 영역 선택 도구
사용자가 마우스로 영역을 선택하여 이미지를 크롭하는 도구
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image
import json
from datetime import datetime

class RegionSelector:
    """영역 선택을 위한 UI 클래스"""
    
    def __init__(self, image_path):
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        self.display_image = self.original_image.copy()
        self.regions = []
        self.current_region = None
        self.drawing = False
        self.start_point = None
        
        # 화면 크기에 맞게 이미지 리사이즈
        self.scale_factor = self._calculate_scale_factor()
        self.scaled_image = self._resize_image_for_display()
        
        print(f"📸 이미지 로드 완료: {os.path.basename(image_path)}")
        print(f"📏 원본 크기: {self.original_image.shape[1]}×{self.original_image.shape[0]}")
        print(f"🔍 표시 크기: {self.scaled_image.shape[1]}×{self.scaled_image.shape[0]} (스케일: {self.scale_factor:.2f})")
        
    def _calculate_scale_factor(self):
        """화면에 맞는 스케일 팩터 계산"""
        max_width = 1200
        max_height = 800
        
        height, width = self.original_image.shape[:2]
        scale_w = max_width / width
        scale_h = max_height / height
        
        return min(scale_w, scale_h, 1.0)  # 1.0을 넘지 않도록
    
    def _resize_image_for_display(self):
        """화면 표시용 이미지 리사이즈"""
        height, width = self.original_image.shape[:2]
        new_width = int(width * self.scale_factor)
        new_height = int(height * self.scale_factor)
        
        return cv2.resize(self.original_image, (new_width, new_height))
    
    def _scale_coordinates_to_original(self, x, y):
        """표시 좌표를 원본 이미지 좌표로 변환"""
        orig_x = int(x / self.scale_factor)
        orig_y = int(y / self.scale_factor)
        return orig_x, orig_y
    
    def _scale_coordinates_to_display(self, x, y):
        """원본 좌표를 표시 좌표로 변환"""
        disp_x = int(x * self.scale_factor)
        disp_y = int(y * self.scale_factor)
        return disp_x, disp_y
    
    def mouse_callback(self, event, x, y, flags, param):
        """마우스 이벤트 처리"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
            self.current_region = [x, y, x, y]
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing and self.current_region is not None:
                self.current_region[2] = x
                self.current_region[3] = y
                self._update_display()
                
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing and self.current_region is not None:
                self.drawing = False
                
                # 최소 크기 확인 (10x10 픽셀)
                width = abs(self.current_region[2] - self.current_region[0])
                height = abs(self.current_region[3] - self.current_region[1])
                
                if width > 10 and height > 10:
                    # 좌표 정규화 (왼쪽 위, 오른쪽 아래)
                    x1 = min(self.current_region[0], self.current_region[2])
                    y1 = min(self.current_region[1], self.current_region[3])
                    x2 = max(self.current_region[0], self.current_region[2])
                    y2 = max(self.current_region[1], self.current_region[3])
                    
                    # 원본 이미지 좌표로 변환
                    orig_x1, orig_y1 = self._scale_coordinates_to_original(x1, y1)
                    orig_x2, orig_y2 = self._scale_coordinates_to_original(x2, y2)
                    
                    region_info = {
                        'id': len(self.regions) + 1,
                        'name': f'영역_{len(self.regions) + 1}',
                        'display_coords': (x1, y1, x2, y2),
                        'original_coords': (orig_x1, orig_y1, orig_x2, orig_y2),
                        'width': orig_x2 - orig_x1,
                        'height': orig_y2 - orig_y1
                    }
                    
                    self.regions.append(region_info)
                    print(f"✅ {region_info['name']} 추가: {region_info['width']}×{region_info['height']}")
                    
                self.current_region = None
                self._update_display()
    
    def _update_display(self):
        """화면 업데이트"""
        self.display_image = self.scaled_image.copy()
        
        # 기존 영역들 그리기
        for i, region in enumerate(self.regions):
            x1, y1, x2, y2 = region['display_coords']
            
            # 영역 테두리
            cv2.rectangle(self.display_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 영역 번호
            cv2.putText(self.display_image, region['name'], 
                       (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 반투명 오버레이
            overlay = self.display_image.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.2, self.display_image, 0.8, 0, self.display_image)
        
        # 현재 그리고 있는 영역
        if self.current_region is not None:
            x1, y1, x2, y2 = self.current_region
            cv2.rectangle(self.display_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        cv2.imshow('영역 선택 도구', self.display_image)
    
    def show_instructions(self):
        """사용법 안내"""
        instructions = [
            "=== 영역 선택 도구 사용법 ===",
            "",
            "🖱️  마우스 조작:",
            "   • 좌클릭 + 드래그: 영역 선택",
            "   • ESC: 종료",
            "",
            "⌨️  키보드 조작:",
            "   • 'c': 선택된 영역들 크롭",
            "   • 's': 영역 정보 저장",
            "   • 'r': 모든 영역 초기화",
            "   • 'd': 마지막 영역 삭제",
            "   • 'h': 도움말 다시 보기",
            "",
            "💾 결과는 'output/cropped_regions/' 폴더에 저장됩니다.",
            ""
        ]
        
        for line in instructions:
            print(line)
    
    def crop_regions(self):
        """선택된 영역들을 크롭하여 저장"""
        if not self.regions:
            print("❌ 선택된 영역이 없습니다.")
            return False
        
        # 출력 디렉토리 생성
        output_dir = "output/cropped_regions"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        cropped_files = []
        
        for region in self.regions:
            x1, y1, x2, y2 = region['original_coords']
            
            # 영역 크롭
            cropped = self.original_image[y1:y2, x1:x2]
            
            # 파일명 생성
            filename = f"{base_name}_{region['name']}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 저장
            cv2.imwrite(filepath, cropped)
            cropped_files.append(filepath)
            
            print(f"💾 {region['name']} 저장: {filename} ({region['width']}×{region['height']})")
        
        # 영역 정보도 JSON으로 저장
        info_file = os.path.join(output_dir, f"{base_name}_regions_{timestamp}.json")
        region_info = {
            'original_image': self.image_path,
            'timestamp': timestamp,
            'regions': self.regions,
            'cropped_files': cropped_files
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(region_info, f, ensure_ascii=False, indent=2)
        
        print(f"📋 영역 정보 저장: {os.path.basename(info_file)}")
        print(f"📁 총 {len(cropped_files)}개 파일이 {output_dir}에 저장되었습니다.")
        
        return True
    
    def delete_last_region(self):
        """마지막 영역 삭제"""
        if self.regions:
            deleted = self.regions.pop()
            print(f"🗑️  {deleted['name']} 삭제됨")
            self._update_display()
        else:
            print("❌ 삭제할 영역이 없습니다.")
    
    def clear_all_regions(self):
        """모든 영역 초기화"""
        if self.regions:
            self.regions.clear()
            print("🗑️  모든 영역이 초기화되었습니다.")
            self._update_display()
        else:
            print("❌ 초기화할 영역이 없습니다.")
    
    def save_regions_info(self):
        """영역 정보만 저장 (크롭하지 않고)"""
        if not self.regions:
            print("❌ 저장할 영역이 없습니다.")
            return False
        
        output_dir = "output/region_info"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        
        info_file = os.path.join(output_dir, f"{base_name}_regions_{timestamp}.json")
        region_info = {
            'original_image': self.image_path,
            'timestamp': timestamp,
            'image_size': {
                'width': self.original_image.shape[1],
                'height': self.original_image.shape[0]
            },
            'regions': self.regions
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(region_info, f, ensure_ascii=False, indent=2)
        
        print(f"📋 영역 정보 저장: {os.path.basename(info_file)}")
        return True
    
    def run(self):
        """메인 실행 루프"""
        self.show_instructions()
        
        cv2.namedWindow('영역 선택 도구', cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback('영역 선택 도구', self.mouse_callback)
        
        self._update_display()
        
        print(f"\n🖼️  이미지가 준비되었습니다. 마우스로 영역을 선택해주세요.")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == ord('c'):  # 크롭
                self.crop_regions()
            elif key == ord('s'):  # 저장
                self.save_regions_info()
            elif key == ord('r'):  # 초기화
                self.clear_all_regions()
            elif key == ord('d'):  # 삭제
                self.delete_last_region()
            elif key == ord('h'):  # 도움말
                self.show_instructions()
        
        cv2.destroyAllWindows()
        
        # 종료 시 요약
        if self.regions:
            print(f"\n📊 선택된 영역: {len(self.regions)}개")
            for region in self.regions:
                print(f"   • {region['name']}: {region['width']}×{region['height']}")
            
            while True:
                choice = input("\n💾 종료 전에 영역을 크롭하시겠습니까? (y/n): ").lower()
                if choice in ['y', 'yes']:
                    self.crop_regions()
                    break
                elif choice in ['n', 'no']:
                    break
                else:
                    print("y 또는 n을 입력해주세요.")
        
        print("👋 영역 선택 도구를 종료합니다.")


def main():
    """메인 함수"""
    print("🖼️  UI 기반 영역 선택 도구")
    print("=" * 50)
    
    # 기본 테스트 이미지 경로
    default_image = "input/17301.png"
    
    # 명령행 인자 확인
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image
    
    # 이미지 파일 존재 확인
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        print(f"💡 사용법: python {sys.argv[0]} <이미지_경로>")
        print(f"   예시: python {sys.argv[0]} input/17301.png")
        return
    
    try:
        # 영역 선택 도구 실행
        selector = RegionSelector(image_path)
        selector.run()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
