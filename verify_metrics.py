import http.client
import cv2
import numpy as np
import json
import secrets
import sys

def create_multipart_body(fields, files, boundary):
    body = []
    for key, value in fields.items():
        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        body.append(b'')
        body.append(str(value).encode())
        
    for key, (filename, content, content_type) in files.items():
        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode())
        body.append(f'Content-Type: {content_type}'.encode())
        body.append(b'')
        body.append(content)
        
    body.append(f'--{boundary}--'.encode())
    body.append(b'')
    return b'\r\n'.join(body)

def request_post(endpoint, files=None, fields=None):
    if files is None: files = {}
    if fields is None: fields = {}
    
    boundary = secrets.token_hex(16)
    body = create_multipart_body(fields, files, boundary)
    
    try:
        conn = http.client.HTTPConnection("localhost", 8000, timeout=10)
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body))
        }
        conn.request("POST", endpoint, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, data
    except Exception as e:
        print(f"Connection Error: {e}")
        return 0, b""

def verify_colorize():
    print("Verifying /colorize...")
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.circle(img, (128, 128), 50, (0, 0, 255), -1)
    _, buf = cv2.imencode(".jpg", img)
    
    files = {"file": ("test.jpg", buf.tobytes(), "image/jpeg")}
    
    status, data = request_post("/colorize", files=files)
    
    if status != 200:
        print(f"FAILED: Status {status}")
        print(data[:200])
        return False
        
    try:
        json_data = json.loads(data)
    except:
        print("FAILED: Response is not JSON")
        return False
        
    if "metrics" not in json_data:
        print("FAILED: Missing metrics keys")
        return False
        
    metrics = json_data["metrics"]
    print(f"Global Score: {metrics.get('global_color_strength')}")
    
    if len(metrics.get("tile_confidence_map", [])) != 4:
        print("FAILED: Tile map invalid")
        return False
        
    print("PASS: /colorize verified")
    return True

def verify_refine():
    print("Verifying /refine...")
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    _, img_buf = cv2.imencode(".jpg", img)
    
    mask = np.zeros((256, 256), dtype=np.uint8)
    cv2.rectangle(mask, (50, 50), (100, 100), 255, -1)
    _, mask_buf = cv2.imencode(".jpg", mask)
    
    files = {
        "file": ("test.jpg", img_buf.tobytes(), "image/jpeg"),
        "mask": ("mask.jpg", mask_buf.tobytes(), "image/jpeg")
    }
    
    status, data = request_post("/refine", files=files)
    
    if status != 200:
        print(f"FAILED: Status {status}")
        return False
        
    try:
        json_data = json.loads(data)
    except:
        print("FAILED: Response is not JSON")
        return False
        
    if "metrics" not in json_data:
        print("FAILED: Missing metrics")
        return False
        
    brush = json_data["metrics"].get("brush_confidence")
    print(f"Brush Confidence: {brush}")
    
    if brush is None:
        print("FAILED: Missing brush confidence")
        return False
        
    print("PASS: /refine verified")
    return True

if __name__ == "__main__":
    if verify_colorize() and verify_refine():
        print("ALL TESTS PASSED")
    else:
        sys.exit(1)
