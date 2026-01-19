import os
import sys
import argparse
import cv2
import numpy as np
import torch

# Ensure we can import the model from the training directory
# This assumes the script is run from the project root.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from training.colorization_model import ColorizationNet
except ImportError:
    print("Error: Could not find training/colorization_model.py.")
    print("Make sure you are running this script from the project root.")
    sys.exit(1)

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

def colorize_image(input_path, output_path, model_path, vibrancy=1.6, grid_size=3):
    """
    Main function with High-Density Tiled Inference + Adaptive Stretching.
    grid_size=3 means a 3x3 grid (9 tiles), much more thorough than 2x2.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 1. Load Model
    model = ColorizationNet()
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device).eval()

    # 2. Load Original Image
    img_bgr = cv2.imread(input_path)
    if img_bgr is None: return
    orig_h, orig_w = img_bgr.shape[:2]
    orig_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    orig_l_channel = orig_lab[:, :, 0]

    def run_model(img_np):
        img_resized = cv2.resize(img_np, (256, 256))
        l_chan = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)[:, :, 0]
        l_norm = l_chan.astype(np.float32) / 255.0
        l_tensor = torch.from_numpy(l_norm).unsqueeze(0).unsqueeze(0).to(device)
        with torch.no_grad():
            ab_pred = model(l_tensor).squeeze(0).cpu().numpy()
        return ab_pred # (2, 256, 256)

    # 3. GLOBAL PASS (The 'Baseline' colors)
    print("Running Global Pass...")
    ab_global = run_model(img_bgr)
    a_global = cv2.resize(ab_global[0], (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)
    b_global = cv2.resize(ab_global[1], (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)

    # 4. HIGH-DENSITY TILED PASS
    if grid_size > 1:
        print(f"Running {grid_size}x{grid_size} Tiled Pass ({grid_size**2} units)...")
        final_a = np.zeros((orig_h, orig_w), dtype=np.float32)
        final_b = np.zeros((orig_h, orig_w), dtype=np.float32)
        weight_sum = np.zeros((orig_h, orig_w), dtype=np.float32)

        # Calculate stride and window size with 50% overlap for smoothness
        # Each tile will cover roughly (1 / (grid_size - offset)) of the image
        win_h = int(orig_h / (grid_size * 0.6)) if grid_size > 1 else orig_h
        win_w = int(orig_w / (grid_size * 0.6)) if grid_size > 1 else orig_w
        
        # Ensure window isn't larger than original
        win_h = min(win_h, orig_h)
        win_w = min(win_w, orig_w)

        # Pre-calculate soft weights for blending
        mask = np.ones((win_h, win_w), dtype=np.float32)
        border = 10
        cv2.copyMakeBorder(mask[border:-border, border:-border], border, border, border, border, cv2.BORDER_CONSTANT, value=0)
        mask = cv2.GaussianBlur(mask, (31, 31), 0)

        y_coords = np.linspace(0, orig_h - win_h, grid_size).astype(int)
        x_coords = np.linspace(0, orig_w - win_w, grid_size).astype(int)

        for y1 in y_coords:
            for x1 in x_coords:
                y2, x2 = y1 + win_h, x1 + win_w
                tile_img = img_bgr[y1:y2, x1:x2]
                
                # Inference on tile
                ab_tile = run_model(tile_img)
                
                # Upscale back to current tile window size
                a_tile = cv2.resize(ab_tile[0], (win_w, win_h), interpolation=cv2.INTER_CUBIC)
                b_tile = cv2.resize(ab_tile[1], (win_w, win_h), interpolation=cv2.INTER_CUBIC)
                
                # Accumulate with soft weights
                final_a[y1:y2, x1:x2] += a_tile * mask
                final_b[y1:y2, x1:x2] += b_tile * mask
                weight_sum[y1:y2, x1:x2] += mask

        # Blend tiled result with global pass
        valid = weight_sum > 0
        final_a[valid] /= (weight_sum[valid] + 1e-6)
        final_b[valid] /= (weight_sum[valid] + 1e-6)
        
        # Final mix: 80% Dense Tiles (Details) + 20% Global (Stability)
        a_final = final_a * 0.8 + a_global * 0.2
        b_final = final_b * 0.8 + b_global * 0.2
    else:
        a_final, b_final = a_global, b_global

    # 5. Adaptive Boost (The final 'Pop')
    a_final, b_final = apply_adaptive_stretch(a_final, b_final, vibrancy)

    # 6. Combine & Save
    a_uint8 = (a_final + 128).clip(0, 255).astype(np.uint8)
    b_uint8 = (b_final + 128).clip(0, 255).astype(np.uint8)
    colorized_lab = cv2.merge([orig_l_channel, a_uint8, b_uint8])
    result = cv2.cvtColor(colorized_lab, cv2.COLOR_LAB2BGR)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, result)
    print(f"Success! High-Density colorized image saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pro Colorization with High-Density Tiling.")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="results/colorized.jpg")
    parser.add_argument("--weights", type=str, default="model/finetuned/colorizer.pth")
    parser.add_argument("--vibrancy", type=float, default=1.8)
    parser.add_argument("--grid", type=int, default=3, help="Grid density (e.g., 3 for 3x3=9 units).")

    args = parser.parse_args()
    colorize_image(args.input, args.output, args.weights, args.vibrancy, args.grid)

# Example command:
# python inference/colorize.py --input test.jpg --output results/test_vibrant.jpg --vibrancy 1.6
