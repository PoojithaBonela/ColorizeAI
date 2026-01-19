import torch
checkpoint_path = 'model/finetuned/last_checkpoint.pth'
try:
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    print(f"RESUME_EPOCH: {checkpoint['epoch'] + 1}")
except Exception as e:
    print(f"ERROR: {e}")
