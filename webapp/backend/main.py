import os
import io
import torch
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from training.colorization_model import ColorizationNet

# Initialize FastAPI app
app = FastAPI(title="AI Image Colorization API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
MODEL_PATH = "model/finetuned/colorizer.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
VIBRANCY = 2.0      # Balanced vibrancy
GRID_SIZE = 4       # Reverted to 4x4 for more consistent results
REFINE_VIBRANCY = 4.5 # Increased for Phase 5 ("Saturated Bloom")

# --- Load Model at Startup ---
print(f"--> Using device: {DEVICE}")
model = ColorizationNet()

if os.path.exists(MODEL_PATH):
    print(f"--> Loading trained weights from {MODEL_PATH}...")
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
else:
    print(f"--> WARNING: {MODEL_PATH} not found. Using uninitialized weights.")

model.to(DEVICE)
model.eval()

def apply_adaptive_stretch(a_pred, b_pred, vibrancy):
    """
    Applies non-linear gamma stretching to amplify faint color signals.
    """
    mag = np.sqrt(a_pred**2 + b_pred**2)
    max_mag = np.max(mag)
    
    if max_mag > 0:
        gamma = 0.6
        a_pred = np.sign(a_pred) * (np.abs(a_pred) ** gamma)
        b_pred = np.sign(b_pred) * (np.abs(b_pred) ** gamma)
        
        target_boost = (vibrancy * 25.0) / (max_mag ** gamma + 1e-6)
        a_pred *= target_boost
        b_pred *= target_boost
    return a_pred, b_pred

def run_model_internal(img_np):
    """Helper to run model on a specific image patch."""
    img_resized = cv2.resize(img_np, (256, 256))
    l_chan = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)[:, :, 0]
    l_norm = l_chan.astype(np.float32) / 255.0
    l_tensor = torch.from_numpy(l_norm).unsqueeze(0).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        ab_pred = model(l_tensor).squeeze(0).cpu().numpy()
    return ab_pred

def process_inference(img_bgr: np.ndarray) -> np.ndarray:
    """
    Advanced inference logic: Global Pass + 4x4 Tiled Pass + Adaptive Stretching.
    """
    orig_h, orig_w = img_bgr.shape[:2]
    orig_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    orig_l = orig_lab[:, :, 0]

    # 1. Global Pass (Baseline)
    ab_global = run_model_internal(img_bgr)
    a_global = cv2.resize(ab_global[0], (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)
    b_global = cv2.resize(ab_global[1], (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)

    # 2. 4x4 Tiled Pass
    final_a = np.zeros((orig_h, orig_w), dtype=np.float32)
    final_b = np.zeros((orig_h, orig_w), dtype=np.float32)
    weight_sum = np.zeros((orig_h, orig_w), dtype=np.float32)

    # Calculate window size with 50% overlap for smoothness
    win_h = int(orig_h / (GRID_SIZE * 0.6))
    win_w = int(orig_w / (GRID_SIZE * 0.6))
    win_h, win_w = min(win_h, orig_h), min(win_w, orig_w)

    # Pre-calculate soft weights (Gaussian mask)
    mask = np.ones((win_h, win_w), dtype=np.float32)
    border = 10
    mask[0:border, :] = 0
    mask[-border:, :] = 0
    mask[:, 0:border] = 0
    mask[:, -border:] = 0
    mask = cv2.GaussianBlur(mask, (31, 31), 0)

    y_coords = np.linspace(0, orig_h - win_h, GRID_SIZE).astype(int)
    x_coords = np.linspace(0, orig_w - win_w, GRID_SIZE).astype(int)

    for y1 in y_coords:
        for x1 in x_coords:
            y2, x2 = y1 + win_h, x1 + win_w
            tile_img = img_bgr[y1:y2, x1:x2]
            ab_tile = run_model_internal(tile_img)
            
            a_tile = cv2.resize(ab_tile[0], (win_w, win_h), interpolation=cv2.INTER_CUBIC)
            b_tile = cv2.resize(ab_tile[1], (win_w, win_h), interpolation=cv2.INTER_CUBIC)
            
            final_a[y1:y2, x1:x2] += a_tile * mask
            final_b[y1:y2, x1:x2] += b_tile * mask
            weight_sum[y1:y2, x1:x2] += mask

    valid = weight_sum > 0
    final_a[valid] /= (weight_sum[valid] + 1e-6)
    final_b[valid] /= (weight_sum[valid] + 1e-6)
    
    # 3. Final Mix & Adaptive Stretch
    # 80% Dense Tiles (Details) + 20% Global (Stability)
    a_mixed = final_a * 0.8 + a_global * 0.2
    b_mixed = final_b * 0.8 + b_global * 0.2
    
    a_final, b_final = apply_adaptive_stretch(a_mixed, b_mixed, VIBRANCY)
    
    # Safety Clamp
    a_final = np.clip(a_final, -128, 127)
    b_final = np.clip(b_final, -128, 127)
    
    a_uint8 = (a_final + 128).clip(0, 255).astype(np.uint8)
    b_uint8 = (b_final + 128).clip(0, 255).astype(np.uint8)
    
    result_lab = cv2.merge([orig_l, a_uint8, b_uint8])
    result_bgr = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)
    
    return result_bgr

@app.post("/colorize")
async def colorize(file: UploadFile = File(...)):
    """
    Endpoint to colorize an uploaded B&W image.
    Returns: Colorized JPG image.
    """
    # Read image from upload
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Could not decode image"}

    # Run AI inference
    result_img = process_inference(img)
    
    # Encode result to JPG
    _, encoded_img = cv2.imencode(".jpg", result_img)
    
    # Stream the response
    return StreamingResponse(io.BytesIO(encoded_img.tobytes()), media_type="image/jpeg")

@app.post("/refine")
async def refine(
    file: UploadFile = File(...), 
    mask: UploadFile = File(...),
    base: UploadFile = File(None),
    target_color: str = Form(None) # Added target_color (hex string)
):
    """
    Refines a specific area of the image based on a user-provided mask.
    Supports iterative persistence and user-provided color guidance.
    """
    # 1. Load Original and Mask
    # ... (skipping unchanged code for context) ...
    img_contents = await file.read()
    mask_contents = await mask.read()
    
    img = cv2.imdecode(np.frombuffer(img_contents, np.uint8), cv2.IMREAD_COLOR)
    mask_img = cv2.imdecode(np.frombuffer(mask_contents, np.uint8), cv2.IMREAD_GRAYSCALE)
    
    if img is None or mask_img is None:
        return {"error": "Could not decode input or mask"}

    orig_h, orig_w = img.shape[:2]

    # Load Base Image (Previous Result) if it exists
    if base:
        base_contents = await base.read()
        background = cv2.imdecode(np.frombuffer(base_contents, np.uint8), cv2.IMREAD_COLOR)
        if background is None: background = process_inference(img)
    else:
        background = process_inference(img)

    # 2. Find Bounding Box of Mask
    coords = cv2.findNonZero(mask_img)
    if coords is None:
        return StreamingResponse(io.BytesIO(cv2.imencode(".jpg", process_inference(img))[1].tobytes()), media_type="image/jpeg")
    
    x_box, y_box, w_box, h_box = cv2.boundingRect(coords)
    center_x, center_y = x_box + w_box // 2, y_box + h_box // 2

    # 3. Targeted Bounding Box Crop (Dynamic Size)
    # Use the mask's actual bounding box with a 10% margin
    margin = int(max(w_box, h_box) * 0.1)
    x1 = max(0, x_box - margin)
    y1 = max(0, y_box - margin)
    x2 = min(orig_w, x_box + w_box + margin)
    y2 = min(orig_h, y_box + h_box + margin)
    
    crop = img[y1:y2, x1:x2]
    crop_h, crop_w = crop.shape[:2]
    
    # 4. Localized Inference
    # We resize the WHOLE bounding box to 256x256 to ensure consistency
    crop_input = cv2.resize(crop, (256, 256))
    l_chan = cv2.cvtColor(crop_input, cv2.COLOR_BGR2LAB)[:, :, 0]
    l_norm = l_chan.astype(np.float32) / 255.0
    l_tensor = torch.from_numpy(l_norm).unsqueeze(0).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        ab_pred = model(l_tensor).squeeze(0).cpu().numpy()
    
    a_pred = ab_pred[0] * REFINE_VIBRANCY
    b_pred = ab_pred[1] * REFINE_VIBRANCY

    # --- SATURATION FLOOR (Phase 5) ---
    # If the AI predicts weak color, we "snap" it to a minimum level to prevent dusky looks.
    mag_pred = np.sqrt(a_pred**2 + b_pred**2)
    floor = 20.0
    boost_mask = (mag_pred < floor) & (mag_pred > 2.0)
    a_pred[boost_mask] *= (floor / (mag_pred[boost_mask] + 1e-6))
    b_pred[boost_mask] *= (floor / (mag_pred[boost_mask] + 1e-6))

    # --- COLOR GUIDANCE ---
    if target_color and len(target_color) == 7:
        try:
            hex_color = target_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            bgr_target = np.uint8([[ [rgb[2], rgb[1], rgb[0]] ]])
            lab_target = cv2.cvtColor(bgr_target, cv2.COLOR_BGR2LAB)[0][0]
            
            target_a = lab_target[1].astype(np.float32) - 128
            target_b = lab_target[2].astype(np.float32) - 128
            
            # Blend AI prediction with Target Color (85% influence for Phase 5)
            # This ensures user colors are bright and dominant
            a_pred = (a_pred * 0.15) + (target_a * 0.85)
            b_pred = (b_pred * 0.15) + (target_b * 0.85)
        except: pass

    # --- SMOOTHING PASS (Anti-Patch) ---
    # Apply light blur to the AB channels to prevent "small squares" look
    a_pred = cv2.blur(a_pred, (3, 3))
    b_pred = cv2.blur(b_pred, (3, 3))

    a_pred = np.clip(a_pred, -128, 127)
    b_pred = np.clip(b_pred, -128, 127)
    
    # Upscale back to exact crop size
    a_up = cv2.resize(a_pred, (crop_w, crop_h), interpolation=cv2.INTER_CUBIC)
    b_up = cv2.resize(b_pred, (crop_w, crop_h), interpolation=cv2.INTER_CUBIC)

    # 5. Smart Blending
    crop_lab_orig = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    l_crop_orig = crop_lab_orig[:, :, 0]
    
    a_f = (a_up + 128).clip(0, 255).astype(np.uint8)
    b_f = (b_up + 128).clip(0, 255).astype(np.uint8)
    
    result_crop_bgr = cv2.cvtColor(cv2.merge([l_crop_orig, a_f, b_f]), cv2.COLOR_LAB2BGR)
    
    # Dynamic Feathering based on area size
    # We Dilate first to ensure the center of the stroke remains strong
    kernel_size = max(5, int(min(crop_w, crop_h) / 20))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    alpha_full = cv2.resize(mask_img, (orig_w, orig_h))
    alpha_full = cv2.dilate(alpha_full, kernel, iterations=2)
    
    blur_radius = max(11, int(min(crop_w, crop_h) / 6) | 1)
    if blur_radius % 2 == 0: blur_radius += 1
    alpha_full = cv2.GaussianBlur(alpha_full, (blur_radius, blur_radius), 0)
    
    alpha = alpha_full.astype(np.float32) / 255.0
    alpha = cv2.merge([alpha, alpha, alpha])
    
    print(f"--> [DEBUG] Mask Peak Intensity: {alpha.max():.2f}")
    
    # --- VIBRANCY GUARD ---
    current_crop = background[y1:y2, x1:x2]
    current_lab = cv2.cvtColor(current_crop, cv2.COLOR_BGR2LAB)
    cur_a, cur_b = current_lab[:,:,1].astype(np.float32)-128, current_lab[:,:,2].astype(np.float32)-128
    cur_mag = np.sqrt(cur_a**2 + cur_b**2)
    
    new_lab = cv2.cvtColor(result_crop_bgr, cv2.COLOR_BGR2LAB)
    new_a, new_b = new_lab[:,:,1].astype(np.float32)-128, new_lab[:,:,2].astype(np.float32)-128
    new_mag = np.sqrt(new_a**2 + new_b**2)
    
    is_new_vibrant = (new_mag > 2).astype(np.float32) # even more permissive
    is_old_gray = (cur_mag < 8).astype(np.float32) 
    v_mask = np.clip(is_new_vibrant + is_old_gray, 0, 1)
    v_mask = cv2.merge([v_mask, v_mask, v_mask])
    v_mask = cv2.GaussianBlur(v_mask, (15, 15), 0)

    # Combine User Brush Mask with Vibrancy Guard
    final_alpha = alpha[y1:y2, x1:x2] * v_mask
    
    print(f"--> [DEBUG] Max Alpha in Crop: {alpha[y1:y2, x1:x2].max():.3f}")
    print(f"--> [DEBUG] Max V-Guard Mask: {v_mask.max():.3f}")
    
    # Blend: Only apply the new color if it passes the vibrancy guard
    background[y1:y2, x1:x2] = (1 - final_alpha) * background[y1:y2, x1:x2] + final_alpha * result_crop_bgr
    
    print(f"--> Refinement Blend Complete at ({x1},{y1}) to ({x2},{y2}).")
    _, encoded_img = cv2.imencode(".jpg", background)
    return StreamingResponse(io.BytesIO(encoded_img.tobytes()), media_type="image/jpeg")

@app.get("/")
async def root():
    return {"message": "AI Colorization API is online", "device": str(DEVICE)}

# To run: uvicorn webapp.backend.main:app --host 0.0.0.0 --port 8000
