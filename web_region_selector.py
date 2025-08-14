#!/usr/bin/env python3
"""
웹 기반 영역 선택 도구
OpenCV GUI 대신 웹 브라우저를 사용
"""

import os
import sys
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
import cv2
import numpy as np
import threading
import webbrowser
import time

sys.path.append('src')

class WebRegionSelector:
    """웹 기반 영역 선택기"""
    
    def __init__(self, image_path):
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
        
        self.regions = []
        self.base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # 웹용 이미지 준비
        self.prepare_web_image()
        
        print(f"📸 이미지 로드 완료: {os.path.basename(image_path)}")
        print(f"📏 원본 크기: {self.original_image.shape[1]}×{self.original_image.shape[0]}")
        
    def prepare_web_image(self):
        """웹 표시용 이미지 준비"""
        # PIL로 변환
        rgb_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # 웹용 크기 조정 (최대 800px)
        max_size = 800
        if max(pil_image.size) > max_size:
            pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # base64로 인코딩
        import io
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        self.web_image_data = base64.b64encode(img_buffer.read()).decode('utf-8')
        self.web_image_size = pil_image.size
        
        # 스케일 팩터 계산
        original_size = (self.original_image.shape[1], self.original_image.shape[0])
        self.scale_x = original_size[0] / self.web_image_size[0]
        self.scale_y = original_size[1] / self.web_image_size[1]
    
    def add_region(self, x1, y1, x2, y2):
        """영역 추가"""
        # 웹 좌표를 원본 좌표로 변환
        orig_x1 = int(x1 * self.scale_x)
        orig_y1 = int(y1 * self.scale_y)
        orig_x2 = int(x2 * self.scale_x)
        orig_y2 = int(y2 * self.scale_y)
        
        # 좌표 정규화
        x1, x2 = min(orig_x1, orig_x2), max(orig_x1, orig_x2)
        y1, y2 = min(orig_y1, orig_y2), max(orig_y1, orig_y2)
        
        region = {
            'id': len(self.regions) + 1,
            'name': f'영역_{len(self.regions) + 1}',
            'original_coords': (x1, y1, x2, y2),
            'width': x2 - x1,
            'height': y2 - y1
        }
        
        self.regions.append(region)
        print(f"✅ {region['name']} 추가: {region['width']}×{region['height']}")
        return region
    
    def crop_regions(self):
        """선택된 영역들 크롭"""
        if not self.regions:
            return False, "선택된 영역이 없습니다."
        
        output_dir = "output/cropped_regions"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cropped_files = []
        
        for region in self.regions:
            x1, y1, x2, y2 = region['original_coords']
            cropped = self.original_image[y1:y2, x1:x2]
            
            filename = f"{self.base_name}_{region['name']}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            cv2.imwrite(filepath, cropped)
            cropped_files.append(filepath)
            
            print(f"💾 {region['name']} 저장: {filename}")
        
        # 영역 정보 저장
        info_file = os.path.join(output_dir, f"{self.base_name}_regions_{timestamp}.json")
        region_info = {
            'original_image': self.image_path,
            'timestamp': timestamp,
            'regions': self.regions,
            'cropped_files': cropped_files
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(region_info, f, ensure_ascii=False, indent=2)
        
        return True, f"{len(cropped_files)}개 영역이 저장되었습니다."

# Flask 앱 생성
app = Flask(__name__)
selector = None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('region_selector.html')

@app.route('/api/image')
def get_image():
    """이미지 데이터 반환"""
    if selector:
        return jsonify({
            'image_data': selector.web_image_data,
            'width': selector.web_image_size[0],
            'height': selector.web_image_size[1]
        })
    return jsonify({'error': 'No image loaded'}), 400

@app.route('/api/regions', methods=['GET', 'POST'])
def handle_regions():
    """영역 관리"""
    if request.method == 'GET':
        return jsonify({'regions': selector.regions if selector else []})
    
    elif request.method == 'POST':
        if not selector:
            return jsonify({'error': 'No image loaded'}), 400
        
        data = request.json
        region = selector.add_region(
            data['x1'], data['y1'], data['x2'], data['y2']
        )
        return jsonify({'region': region})

@app.route('/api/crop', methods=['POST'])
def crop_regions():
    """영역 크롭"""
    if not selector:
        return jsonify({'error': 'No image loaded'}), 400
    
    success, message = selector.crop_regions()
    return jsonify({'success': success, 'message': message})

@app.route('/api/clear', methods=['POST'])
def clear_regions():
    """모든 영역 삭제"""
    if selector:
        selector.regions.clear()
        print("🗑️ 모든 영역 삭제됨")
    return jsonify({'success': True})

def create_html_template():
    """HTML 템플릿 파일 생성"""
    template_dir = "templates"
    os.makedirs(template_dir, exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>영역 선택 도구</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-info { background-color: #17a2b8; color: white; }
        .btn:hover { opacity: 0.8; }
        .image-container {
            position: relative;
            display: inline-block;
            border: 2px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        #canvas {
            cursor: crosshair;
            display: block;
        }
        .regions-list {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .region-item {
            padding: 10px;
            margin: 5px 0;
            background-color: white;
            border-radius: 3px;
            border-left: 4px solid #007bff;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .status.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .instructions {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ 영역 선택 도구</h1>
            <p>마우스로 드래그하여 영역을 선택하세요</p>
        </div>
        
        <div class="instructions">
            <h3>📋 사용법:</h3>
            <ul>
                <li><strong>영역 선택:</strong> 마우스로 드래그하여 사각형 그리기</li>
                <li><strong>영역 크롭:</strong> "영역 크롭" 버튼 클릭</li>
                <li><strong>영역 삭제:</strong> "모든 영역 삭제" 버튼 클릭</li>
                <li><strong>결과 확인:</strong> output/cropped_regions/ 폴더 확인</li>
            </ul>
        </div>
        
        <div class="controls">
            <button class="btn btn-success" onclick="cropRegions()">📷 영역 크롭</button>
            <button class="btn btn-danger" onclick="clearRegions()">🗑️ 모든 영역 삭제</button>
            <button class="btn btn-info" onclick="refreshImage()">🔄 새로고침</button>
            <button class="btn btn-primary" onclick="downloadResults()">💾 결과 다운로드</button>
        </div>
        
        <div class="image-container">
            <canvas id="canvas"></canvas>
        </div>
        
        <div class="regions-list">
            <h3>📍 선택된 영역: <span id="regionCount">0</span>개</h3>
            <div id="regionsList"></div>
        </div>
        
        <div id="status" class="status"></div>
    </div>

    <script>
        let canvas, ctx;
        let isDrawing = false;
        let startX, startY, currentX, currentY;
        let regions = [];
        let imageLoaded = false;

        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            canvas = document.getElementById('canvas');
            ctx = canvas.getContext('2d');
            
            loadImage();
            setupEventListeners();
        });

        // 이미지 로드
        async function loadImage() {
            try {
                const response = await fetch('/api/image');
                const data = await response.json();
                
                if (data.image_data) {
                    const img = new Image();
                    img.onload = function() {
                        canvas.width = data.width;
                        canvas.height = data.height;
                        ctx.drawImage(img, 0, 0);
                        imageLoaded = true;
                        showStatus('이미지 로드 완료', 'success');
                    };
                    img.src = 'data:image/png;base64,' + data.image_data;
                }
            } catch (error) {
                showStatus('이미지 로드 실패: ' + error.message, 'error');
            }
        }

        // 이벤트 리스너 설정
        function setupEventListeners() {
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
            canvas.addEventListener('mouseout', stopDrawing);
        }

        // 그리기 시작
        function startDrawing(e) {
            if (!imageLoaded) return;
            
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isDrawing = true;
        }

        // 그리기 중
        function draw(e) {
            if (!isDrawing || !imageLoaded) return;
            
            const rect = canvas.getBoundingClientRect();
            currentX = e.clientX - rect.left;
            currentY = e.clientY - rect.top;
            
            redrawCanvas();
            
            // 현재 그리는 영역 표시
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
            ctx.setLineDash([]);
        }

        // 그리기 종료
        async function stopDrawing(e) {
            if (!isDrawing || !imageLoaded) return;
            
            isDrawing = false;
            
            const width = Math.abs(currentX - startX);
            const height = Math.abs(currentY - startY);
            
            // 최소 크기 확인
            if (width > 10 && height > 10) {
                const x1 = Math.min(startX, currentX);
                const y1 = Math.min(startY, currentY);
                const x2 = Math.max(startX, currentX);
                const y2 = Math.max(startY, currentY);
                
                try {
                    const response = await fetch('/api/regions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ x1, y1, x2, y2 })
                    });
                    
                    const data = await response.json();
                    if (data.region) {
                        regions.push(data.region);
                        updateRegionsList();
                        redrawCanvas();
                        showStatus(`${data.region.name} 추가됨`, 'success');
                    }
                } catch (error) {
                    showStatus('영역 추가 실패: ' + error.message, 'error');
                }
            }
        }

        // 캔버스 다시 그리기
        async function redrawCanvas() {
            try {
                const response = await fetch('/api/image');
                const data = await response.json();
                
                if (data.image_data) {
                    const img = new Image();
                    img.onload = function() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0);
                        
                        // 기존 영역들 그리기
                        regions.forEach((region, index) => {
                            const x1 = region.original_coords[0] / (canvas.width * 1.0);
                            const y1 = region.original_coords[1] / (canvas.height * 1.0);
                            const x2 = region.original_coords[2] / (canvas.width * 1.0);
                            const y2 = region.original_coords[3] / (canvas.height * 1.0);
                            
                            // 스케일링 적용
                            const rectX = x1 * canvas.width;
                            const rectY = y1 * canvas.height;
                            const rectW = (x2 - x1) * canvas.width;
                            const rectH = (y2 - y1) * canvas.height;
                            
                            ctx.strokeStyle = '#00ff00';
                            ctx.lineWidth = 2;
                            ctx.strokeRect(rectX, rectY, rectW, rectH);
                            
                            // 영역 번호
                            ctx.fillStyle = '#00ff00';
                            ctx.font = '14px Arial';
                            ctx.fillText(region.name, rectX + 5, rectY - 5);
                        });
                    };
                    img.src = 'data:image/png;base64,' + data.image_data;
                }
            } catch (error) {
                console.error('캔버스 다시 그리기 오류:', error);
            }
        }

        // 영역 리스트 업데이트
        function updateRegionsList() {
            const regionsList = document.getElementById('regionsList');
            const regionCount = document.getElementById('regionCount');
            
            regionCount.textContent = regions.length;
            
            regionsList.innerHTML = regions.map(region => `
                <div class="region-item">
                    <strong>${region.name}</strong> - 
                    크기: ${region.width}×${region.height}px
                </div>
            `).join('');
        }

        // 영역 크롭
        async function cropRegions() {
            if (regions.length === 0) {
                showStatus('선택된 영역이 없습니다.', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/crop', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('크롭 완료: ' + data.message, 'success');
                } else {
                    showStatus('크롭 실패: ' + data.message, 'error');
                }
            } catch (error) {
                showStatus('크롭 오류: ' + error.message, 'error');
            }
        }

        // 모든 영역 삭제
        async function clearRegions() {
            try {
                await fetch('/api/clear', { method: 'POST' });
                regions = [];
                updateRegionsList();
                redrawCanvas();
                showStatus('모든 영역이 삭제되었습니다.', 'success');
            } catch (error) {
                showStatus('삭제 실패: ' + error.message, 'error');
            }
        }

        // 새로고침
        function refreshImage() {
            loadImage();
            showStatus('이미지를 새로고침했습니다.', 'success');
        }

        // 결과 다운로드 (폴더 열기 안내)
        function downloadResults() {
            showStatus('결과 파일이 output/cropped_regions/ 폴더에 저장됩니다.', 'success');
        }

        // 상태 메시지 표시
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
            
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'region_selector.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

def run_web_selector(image_path):
    """웹 기반 영역 선택기 실행"""
    global selector
    
    try:
        selector = WebRegionSelector(image_path)
        create_html_template()
        
        print(f"\n🌐 웹 기반 영역 선택 도구 시작")
        print(f"📸 이미지: {os.path.basename(image_path)}")
        print(f"🔗 브라우저에서 http://localhost:5000 으로 접속하세요")
        print(f"⏹️  종료하려면 Ctrl+C를 누르세요")
        
        # 자동으로 브라우저 열기
        def open_browser():
            time.sleep(1)
            webbrowser.open('http://localhost:5000')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Flask 앱 실행
        app.run(host='localhost', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ 웹 서버 실행 오류: {e}")
        raise

def main():
    """메인 함수"""
    print("🌐 웹 기반 영역 선택 도구")
    print("=" * 50)
    
    # 기본 테스트 이미지
    default_image = "input/17301.png"
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        print(f"💡 사용법: python {sys.argv[0]} <이미지_경로>")
        return
    
    try:
        run_web_selector(image_path)
    except KeyboardInterrupt:
        print(f"\n👋 웹 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
