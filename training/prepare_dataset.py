import os
import cv2
import numpy as np
import argparse
from tqdm import tqdm

# Define paths relative to the project root
# Assuming script is run from project root: python training/prepare_dataset.py
RAW_DATA_PATH = r'data/raw'
PROCESSED_PATH = r'data/processed/train'
L_PATH = os.path.join(PROCESSED_PATH, 'L')
AB_PATH = os.path.join(PROCESSED_PATH, 'AB')

def prepare_dataset():
    """
    Reads RGB images from data/raw, converts them to LAB color space,
    and saves the L channel (input) and AB channels (target) as .npy files.
    """
    
    # 1. Create directory structure
    print("Setting up directory structure...")
    os.makedirs(L_PATH, exist_ok=True)
    os.makedirs(AB_PATH, exist_ok=True)
    print(f"Output directories ready:\n - {L_PATH}\n - {AB_PATH}")

    # 2. Gather all image files recursively
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    image_files = []

    print(f"Scanning {RAW_DATA_PATH} for images...")
    for root, _, files in os.walk(RAW_DATA_PATH):
        for file in files:
            if os.path.splitext(file)[1].lower() in image_extensions:
                image_files.append(os.path.join(root, file))

    if not image_files:
        print(f"No images found in {RAW_DATA_PATH}. Please check your data.")
        return

    print(f"Found {len(image_files)} images. Starting conversion...")

    # 3. Process images
    success_count = 0
    error_count = 0
    img_id = 0

    for img_path in tqdm(image_files, desc="Converting Images"):
        try:
            # Read image in color mode (BGR default in OpenCV)
            img = cv2.imread(img_path)

            if img is None:
                # Could not decode image
                error_count += 1
                continue
            
            # Handle grayscale images (if any found, strict conversion to RGB first or skip)
            # LAB conversion requires 3 channels.
            if len(img.shape) == 2:
                # Convert Grayscale to BGR so we can convert to LAB (though A,B will be zero)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
            # Convert BGR to LAB
            # L: 0-255, A: 0-255, B: 0-255 (OpenCV implementation)
            lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            
            # Split channels
            l_channel, a_channel, b_channel = cv2.split(lab_img)

            # --- PROFESSIONAL IMPROVEMENTS ---
            
            # Fix 1: Normalize L channel to [0, 1] range for neural networks
            l_channel = l_channel.astype(np.float32) / 255.0

            # Fix 2: Shift A,B from [0, 255] to [-128, 127] (real LAB range centered at 0)
            a_channel = a_channel.astype(np.float32) - 128
            b_channel = b_channel.astype(np.float32) - 128

            # Stack A and B channels -> Shape (H, W, 2)
            ab_channels = np.dstack((a_channel, b_channel))

            # Fix 3: Use a numeric counter for filenames to prevent collisions
            filename = f"{img_id:06d}"
            
            # Save as NumPy arrays for efficient loading in ML
            # L channel shape: (H, W)
            # AB channel shape: (H, W, 2)
            np.save(os.path.join(L_PATH, f"{filename}.npy"), l_channel)
            np.save(os.path.join(AB_PATH, f"{filename}.npy"), ab_channels)

            success_count += 1
            img_id += 1

        except Exception as e:
            error_count += 1
            # print(f"Error processing {img_path}: {e}") # Uncomment for verbose error logging

    # 4. Final Report
    print("\n" + "="*30)
    print("      PROCESSING COMPLETE      ")
    print("="*30)
    print(f"Successfully processed : {success_count}")
    print(f"Corrupted / Skipped    : {error_count}")
    print(f"L channel saved to     : {L_PATH}")
    print(f"AB channels saved to   : {AB_PATH}")
    print("="*30)

if __name__ == "__main__":
    prepare_dataset()
