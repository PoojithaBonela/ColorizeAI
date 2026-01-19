from dataset import ColorizationDataset
import torch

def test_loader():
    print("Initializing ColorizationDataset (train split)...")
    try:
        dataset = ColorizationDataset(split="train")
    except Exception as e:
        print(f"Failed to initialize dataset: {e}")
        return

    print(f"Total training samples: {len(dataset)}")

    if len(dataset) == 0:
        print("Dataset is empty. Skipping sample check.")
        return

    # Load the first sample
    l, ab = dataset[0]

    print("\nSample check:")
    print(f"L shape : {l.shape}  (Expected: [1, H, W])")
    print(f"AB shape: {ab.shape} (Expected: [2, H, W])")
    print(f"L type  : {l.dtype}")
    print(f"AB type : {ab.dtype}")

    # Basic range check
    print(f"\nL range : {l.min().item():.2f} to {l.max().item():.2f} (Expected: 0 to 1)")
    print(f"A range : {ab[0].min().item():.2f} to {ab[0].max().item():.2f} (Expected: ~ -128 to 127)")
    print(f"B range : {ab[1].min().item():.2f} to {ab[1].max().item():.2f} (Expected: ~ -128 to 127)")

if __name__ == "__main__":
    test_loader()
