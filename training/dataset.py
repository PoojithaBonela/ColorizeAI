import os
import numpy as np
import torch
from torch.utils.data import Dataset

# Define paths relative to the project root
L_PATH = r"data/processed/train/L"
AB_PATH = r"data/processed/train/AB"

class ColorizationDataset(Dataset):
    """
    Custom PyTorch Dataset for LAB colorization.
    Loads L (grayscale) as input and AB (color) as target.
    """
    def __init__(self, split="train", train_ratio=0.8, val_ratio=0.1):
        # List all files and ensure they are sorted to maintain alignment
        try:
            self.l_files = sorted([f for f in os.listdir(L_PATH) if f.endswith('.npy')])
            self.ab_files = sorted([f for f in os.listdir(AB_PATH) if f.endswith('.npy')])
        except FileNotFoundError:
            print(f"Error: Could not find processed data in {L_PATH} or {AB_PATH}.")
            self.l_files = []
            self.ab_files = []

        if len(self.l_files) != len(self.ab_files):
            raise RuntimeError(f"Mismatch between L files ({len(self.l_files)}) and AB files ({len(self.ab_files)}).")

        total = len(self.l_files)
        
        # Calculate split indices
        train_end = int(train_ratio * total)
        val_end = int((train_ratio + val_ratio) * total)

        if split == "train":
            self.indices = range(0, train_end)
        elif split == "val":
            self.indices = range(train_end, val_end)
        else: # test split
            self.indices = range(val_end, total)

        print(f"Loaded {split} split with {len(self.indices)} samples.")

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        # Map dataset index to the actual file index
        real_idx = self.indices[idx]

        # Load the pre-processed NumPy arrays
        l = np.load(os.path.join(L_PATH, self.l_files[real_idx]))
        ab = np.load(os.path.join(AB_PATH, self.ab_files[real_idx]))

        # Convert to PyTorch tensors
        # L shape: (H, W) -> (1, H, W)
        l_tensor = torch.from_numpy(l).unsqueeze(0).float()
        
        # AB shape: (H, W, 2) -> (2, H, W)
        ab_tensor = torch.from_numpy(ab).permute(2, 0, 1).float()

        return l_tensor, ab_tensor
