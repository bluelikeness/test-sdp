#!/usr/bin/env python3
"""
웹 기반 영역 선택 도구 실행기 (개선된 버전)
OpenCV GUI 문제 해결을 위한 웹 기반 대체 도구
"""

import os
import sys
import subprocess
import importlib
import importlib.util
from pathlib import Path

class WebToolsLauncher:
    """웹 도구 실행기 클래스"""
    
    def __init__(self):
        self.tools = {
            '1': {
                'name': '웹 영역 선택만',
                'module': 'web_region_selector',
                'function': 'main',
                'description': '브라우저에서 영역 선택 및 크롭',
                'port': 5000
            },
            '2': {
                'name': '웹 영역 선택 + OCR 통합',
                'module': 'web_region_ocr_integrated', 
                'function': 'main',
                'description': '영역 선택 + 자동 OCR 처리',
                'port': 5001
            }
        }
        
        self.required_packages = {
            'flask': 'Flask>=2.0.0',
            'PIL': 'Pillow>=8.0.0', 
            'cv2': 'opencv-python>=4.5.0',
            'numpy': 'numpy>=1.20.0'
        }
    
    def find_project_directory(self):
        """프로젝트 디렉토리를 동적으로 찾기"""
        current = Path.cwd()
        
        # 현재 디렉토리부터 상위로 올라가며 test-sdp 찾기
        for parent in [current] + list(current.parents):
            if parent.name == 'test-sdp':
                return parent
            test_sdp_path = parent / 'test-sdp'
            if test_sdp_path.exists():
                return test_sdp_path
        
        # 환경별 기본 경로들
        possible_paths = [
            Path.home() / 'work' / 'test-sdp',  # ~/work/test-sdp
            Path('/home/kckang/work/test-sdp'),  # WSL/Linux
            Path('C:/work/test-sdp'),            # Windows
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def check_dependencies(self):
        """의존성 확인 및 설치"""
        print("🔍 의존성 확인 중...")
        
        missing_packages = []
        
        for module, package in self.required_packages.items():
            spec = importlib.util.find_spec(module)
            if spec is None:
                print(f"❌ {package}")
                missing_packages.append(package.split('>=')[0])  # 버전 제거
            else:
                print(f"✅ {package}")
        
        if missing_packages:
            print(f"\\n📦 설치 필요한 패키지: {', '.join(missing_packages)}")
            
            install_choice = input("\\n자동으로 설치하시겠습니까? (y/n): ").lower()
            if install_choice in ['y', 'yes']:
                return self._install_packages(missing_packages)
            else:
                print("의존성을 먼저 설치해주세요.")
                print(f"pip install {' '.join(missing_packages)}")
                return False
        
        return True
    
    def _install_packages(self, packages):
        """패키지 자동 설치"""
        try:
            for package in packages:
                print(f"📦 {package} 설치 중...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5분 타임아웃
                )
                
                if result.returncode == 0:
                    print(f"✅ {package} 설치 완료")
                else:
                    print(f"❌ {package} 설치 실패: {result.stderr}")
                    return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ 설치 시간 초과")
            return False
        except Exception as e:
            print(f"❌ 설치 중 오류: {e}")
            return False
    
    def check_test_image(self):
        """테스트 이미지 확인"""
        test_image = Path("input/17301.png")
        if test_image.exists():
            print(f"✅ 테스트 이미지 확인: {test_image}")
            return True
        else:
            print(f"❌ 테스트 이미지 없음: {test_image}")
            print("💡 input/ 폴더에 17301.png 파일을 준비해주세요.")
            return False
    
    def show_menu(self):
        """메뉴 표시"""
        print(f"\\n🛠️  웹 도구 선택:")
        for key, tool in self.tools.items():
            print(f"{key}. {tool['name']}")
            print(f"   📝 {tool['description']}")
            print(f"   🌐 포트: {tool['port']}")
        print("3. 종료")
    
    def run_tool(self, choice):
        """선택된 도구 실행"""
        if choice not in self.tools:
            return False
            
        tool = self.tools[choice]
        print(f"\\n🚀 {tool['name']} 실행 중...")
        
        try:
            # 모듈 동적 import
            module = importlib.import_module(tool['module'])
            func = getattr(module, tool['function'])
            
            print(f"🌐 브라우저에서 http://localhost:{tool['port']} 으로 접속하세요")
            print("⏹️  종료하려면 Ctrl+C를 누르세요\\n")
            
            # 도구 실행
            func()
            return True
            
        except ImportError as e:
            print(f"❌ 모듈 import 오류: {e}")
            print("💡 필요한 파일들이 있는지 확인해주세요.")
            return False
        except Exception as e:
            print(f"❌ {tool['name']} 실행 오류: {e}")
            return False
    
    def run(self):
        """메인 실행 루프"""
        print("🌐 웹 기반 영역 선택 도구 실행기")
        print("=" * 50)
        
        # 1. 프로젝트 디렉토리 찾기 및 이동
        project_dir = self.find_project_directory()
        if project_dir is None:
            print("❌ test-sdp 디렉토리를 찾을 수 없습니다.")
            print("💡 스크립트를 test-sdp 디렉토리에서 실행해주세요.")
            return
        
        os.chdir(project_dir)
        print(f"📁 작업 디렉토리: {project_dir}")
        
        # 2. 의존성 확인
        if not self.check_dependencies():
            return
        
        # 3. 테스트 이미지 확인
        if not self.check_test_image():
            return
        
        # 4. 메뉴 루프
        while True:
            self.show_menu()
            choice = input("\\n선택 (1-3): ").strip()
            
            if choice == '3':
                print("👋 종료합니다.")
                break
            elif choice in self.tools:
                try:
                    self.run_tool(choice)
                    print("\\n🔄 도구가 종료되었습니다. 메뉴로 돌아갑니다.")
                except KeyboardInterrupt:
                    print("\\n⏹️  사용자에 의해 중단되었습니다.")
                    print("🔄 메뉴로 돌아갑니다.")
                continue
            else:
                print("❌ 1, 2, 또는 3을 입력해주세요.")

def main():
    """메인 함수"""
    try:
        launcher = WebToolsLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
