#!/usr/bin/env python3
"""
웹 기반 영역 선택 + OCR 통합 도구 (완전 버전)
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import threading
import webbrowser
import time

sys.path.append('src')

from web_region_selector import WebRegionSelector

class WebRegionOCRProcessor:
    """웹 기반 영역 선택 + OCR 처리"""
    
    def __init__(self, api_key, model_name="qwen-vl-plus"):
        self.api_key = api_key
        self.model_name = model_name
        
    def process_regions_with_ocr(self, selector):
        """선택된 영역들을 OCR 처리"""
        if not selector.regions:
            return False, "선택된 영역이 없습니다."
        
        try:
            from cloud_ocr import CloudOCRProcessor
            
            # 먼저 영역 크롭
            success, message = selector.crop_regions()
            if not success:
                return False, f"크롭 실패: {message}"
            
            # OCR 프로세서 초기화
            ocr_processor = CloudOCRProcessor(self.api_key, self.model_name)
            
            results = []
            successful_count = 0
            
            output_dir = "output/cropped_regions"
            
            for region in selector.regions:
                print(f"🤖 {region['name']} OCR 처리 중...")
                
                # 크롭된 파일 찾기
                import glob
                pattern = os.path.join(output_dir, f"{selector.base_name}_{region['name']}_*.png")
                cropped_files = glob.glob(pattern)
                
                if not cropped_files:
                    print(f"❌ 크롭된 파일 없음: {region['name']}")
                    continue
                
                cropped_file = max(cropped_files, key=os.path.getctime)
                
                try:
                    # OCR 처리
                    result_tuple = ocr_processor.process_image(cropped_file, "shape_detection")
                    
                    # tuple 처리
                    if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                        result_text, process_time = result_tuple
                    else:
                        result_text = result_tuple
                        process_time = 0
                    
                    if result_text and len(result_text.strip()) > 3:
                        if result_text.lower() not in ['없음', 'none', 'no text', 'no circles']:
                            results.append({
                                'region': region['name'],
                                'coordinates': region['original_coords'],
                                'size': f"{region['width']}×{region['height']}",
                                'text': result_text.strip(),
                                'file': os.path.basename(cropped_file),
                                'process_time': process_time
                            })
                            successful_count += 1
                            print(f"✅ 텍스트 추출: '{result_text.strip()[:50]}...'")
                        else:
                            print(f"❌ 의미있는 텍스트 없음")
                    else:
                        print(f"❌ 텍스트 추출 실패")
                        
                except Exception as e:
                    print(f"❌ OCR 오류: {e}")
                    continue
            
            if results:
                self.save_ocr_results(results, selector.image_path, output_dir)
                return True, f"{successful_count}개 영역에서 텍스트 추출 완료"
            else:
                return False, "모든 영역에서 텍스트 추출 실패"
                
        except Exception as e:
            return False, f"OCR 처리 오류: {str(e)}"
    
    def save_ocr_results(self, results, original_image_path, output_dir):
        """OCR 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(original_image_path))[0]
        
        # 텍스트 결과 파일
        txt_file = os.path.join(output_dir, f"{base_name}_web_ocr_results_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=== 웹 기반 영역별 OCR 결과 ===\n")
            f.write(f"원본 이미지: {original_image_path}\n")
            f.write(f"처리 시간: {timestamp}\n")
            f.write(f"추출된 영역: {len(results)}개\n\n")
            
            for result in results:
                f.write(f"--- {result['region']} ---\n")
                f.write(f"좌표: {result['coordinates']}\n")
                f.write(f"크기: {result['size']}\n")
                f.write(f"추출 텍스트:\n{result['text']}\n\n")
        
        print(f"💾 OCR 결과 저장: {os.path.basename(txt_file)}")

# Flask 앱과 전역 변수
app = Flask(__name__)
selector = None
ocr_processor = None

@app.route('/')
def index():
    """메인 페이지"""
    return '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>웹 기반 영역 선택 + OCR</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn:hover { opacity: 0.8; }
        #canvas { border: 2px solid #ddd; cursor: crosshair; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .processing { display: none; text-align: center; padding: 20px; background: #fff3cd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐🤖 웹 기반 영역 선택 + OCR 도구</h1>
        <p>마우스로 드래그하여 영역을 선택하고 OCR 처리하세요</p>
        
        <div>
            <button class="btn btn-success" onclick="cropRegions()">📷 영역 크롭</button>
            <button class="btn btn-primary" onclick="processOCR()">🤖 OCR 실행</button>
            <button class="btn btn-warning" onclick="cropAndOCR()">🚀 크롭 + OCR</button>
            <button class="btn btn-danger" onclick="clearRegions()">🗑️ 모든 영역 삭제</button>
        </div>
        
        <div class="processing" id="processing">
            <div>⏳ 처리 중...</div>
        </div>
        
        <canvas id="canvas"></canvas>
        
        <div>
            <h3>📍 선택된 영역: <span id="regionCount">0</span>개</h3>
            <div id="regionsList"></div>
        </div>
        
        <div id="status" class="status" style="display:none;"></div>
    </div>

    <script>
        let canvas, ctx;
        let isDrawing = false;
        let startX, startY;
        let regions = [];
        let imageLoaded = false;

        document.addEventListener('DOMContentLoaded', function() {
            canvas = document.getElementById('canvas');
            ctx = canvas.getContext('2d');
            loadImage();
            setupEventListeners();
        });

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

        function setupEventListeners() {
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
        }

        function startDrawing(e) {
            if (!imageLoaded) return;
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isDrawing = true;
        }

        function draw(e) {
            if (!isDrawing) return;
            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            redrawCanvas();
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 2;
            ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
        }

        async function stopDrawing(e) {
            if (!isDrawing) return;
            isDrawing = false;
            
            const rect = canvas.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;
            
            const width = Math.abs(endX - startX);
            const height = Math.abs(endY - startY);
            
            if (width > 10 && height > 10) {
                const x1 = Math.min(startX, endX);
                const y1 = Math.min(startY, endY);
                const x2 = Math.max(startX, endX);
                const y2 = Math.max(startY, endY);
                
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
                        showStatus(data.region.name + ' 추가됨', 'success');
                    }
                } catch (error) {
                    showStatus('영역 추가 실패: ' + error.message, 'error');
                }
            }
        }

        async function redrawCanvas() {
            const response = await fetch('/api/image');
            const data = await response.json();
            
            if (data.image_data) {
                const img = new Image();
                img.onload = function() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0);
                    
                    // 영역들 그리기
                    regions.forEach((region, index) => {
                        ctx.strokeStyle = '#00ff00';
                        ctx.lineWidth = 2;
                        ctx.strokeRect(50 + index * 80, 50, 70, 50);
                        ctx.fillStyle = '#00ff00';
                        ctx.font = '12px Arial';
                        ctx.fillText(region.name, 55 + index * 80, 45);
                    });
                };
                img.src = 'data:image/png;base64,' + data.image_data;
            }
        }

        function updateRegionsList() {
            document.getElementById('regionCount').textContent = regions.length;
            document.getElementById('regionsList').innerHTML = regions.map(region => 
                `<div style="padding:5px; background:#f8f9fa; margin:2px;">
                    <strong>${region.name}</strong> - ${region.width}×${region.height}px
                </div>`
            ).join('');
        }

        function showProcessing() {
            document.getElementById('processing').style.display = 'block';
        }

        function hideProcessing() {
            document.getElementById('processing').style.display = 'none';
        }

        async function cropRegions() {
            if (regions.length === 0) {
                showStatus('선택된 영역이 없습니다.', 'error');
                return;
            }
            
            showProcessing();
            try {
                const response = await fetch('/api/crop', { method: 'POST' });
                const data = await response.json();
                showStatus(data.success ? '크롭 완료: ' + data.message : '크롭 실패: ' + data.message, 
                          data.success ? 'success' : 'error');
            } catch (error) {
                showStatus('크롭 오류: ' + error.message, 'error');
            } finally {
                hideProcessing();
            }
        }

        async function processOCR() {
            if (regions.length === 0) {
                showStatus('선택된 영역이 없습니다.', 'error');
                return;
            }
            
            showProcessing();
            try {
                const response = await fetch('/api/ocr', { method: 'POST' });
                const data = await response.json();
                showStatus(data.success ? 'OCR 완료: ' + data.message : 'OCR 실패: ' + data.message,
                          data.success ? 'success' : 'error');
            } catch (error) {
                showStatus('OCR 오류: ' + error.message, 'error');
            } finally {
                hideProcessing();
            }
        }

        async function cropAndOCR() {
            await cropRegions();
            setTimeout(processOCR, 1000);
        }

        async function clearRegions() {
            await fetch('/api/clear', { method: 'POST' });
            regions = [];
            updateRegionsList();
            redrawCanvas();
            showStatus('모든 영역이 삭제되었습니다.', 'success');
        }

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
            status.style.display = 'block';
            setTimeout(() => { status.style.display = 'none'; }, 3000);
        }
    </script>
</body>
</html>'''

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

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """OCR 처리"""
    if not selector or not ocr_processor:
        return jsonify({'error': 'Not initialized'}), 400
    
    success, message = ocr_processor.process_regions_with_ocr(selector)
    return jsonify({'success': success, 'message': message})

@app.route('/api/clear', methods=['POST'])
def clear_regions():
    """모든 영역 삭제"""
    if selector:
        selector.regions.clear()
        print("🗑️ 모든 영역 삭제됨")
    return jsonify({'success': True})

def run_web_ocr_selector(image_path, api_key):
    """웹 기반 영역 선택 + OCR 도구 실행"""
    global selector, ocr_processor
    
    try:
        selector = WebRegionSelector(image_path)
        ocr_processor = WebRegionOCRProcessor(api_key, "qwen-vl-plus")
        
        print(f"\n🌐🤖 웹 기반 영역 선택 + OCR 도구 시작")
        print(f"📸 이미지: {os.path.basename(image_path)}")
        print(f"🔗 브라우저에서 http://localhost:5001 으로 접속하세요")
        print(f"⏹️  종료하려면 Ctrl+C를 누르세요")
        
        # 자동으로 브라우저 열기
        def open_browser():
            time.sleep(1)
            webbrowser.open('http://localhost:5001')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Flask 앱 실행
        app.run(host='localhost', port=5001, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"❌ 웹 서버 실행 오류: {e}")
        raise

def main():
    """메인 함수"""
    print("🌐🤖 웹 기반 영역 선택 + OCR 도구")
    print("=" * 60)
    
    # 환경 설정 확인
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('QWEN_API_KEY')
        
        if not api_key or api_key == "your_api_key_here":
            print("❌ API 키가 설정되지 않았습니다.")
            print("   .env 파일에서 QWEN_API_KEY를 설정해주세요.")
            return
        
        print("✅ API 키 확인됨")
        
    except ImportError:
        print("❌ 필요한 모듈을 찾을 수 없습니다.")
        print("   pip install python-dotenv flask")
        return
    
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
        run_web_ocr_selector(image_path, api_key)
    except KeyboardInterrupt:
        print(f"\n👋 웹 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
