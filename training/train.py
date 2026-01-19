import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

# Import our custom modules
from dataset import ColorizationDataset
from colorization_model import ColorizationNet

# --- Configuration ---
BATCH_SIZE = 16          # Number of images per batch (reduce to 8 if you run out of memory)
LEARNING_RATE = 1e-4     # Good starting point for Adam
NUM_EPOCHS = 20          # How many times to go through the dataset
SAVE_DIR = "model/finetuned"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def train_one_epoch(model, loader, criterion, optimizer, scaler):
    """
    Runs one epoch of training.
    """
    model.train()  # Set model to training mode
    running_loss = 0.0
    
    # Progress bar for the loop
    loop = tqdm(loader, desc="Training", leave=True)
    
    for l_input, ab_target in loop:
        # Move data to GPU if available
        l_input = l_input.to(DEVICE)
        ab_target = ab_target.to(DEVICE)
        
        # Zero the gradients
        optimizer.zero_grad()
        
        # Forward pass (predict colors)
        # We use mixed precision for speed/memory efficiency if available
        with torch.cuda.amp.autocast(enabled=(DEVICE=="cuda")):
            ab_predicted = model(l_input)
            loss = criterion(ab_predicted, ab_target)
            
        # Backward pass (calculate gradients)
        scaler.scale(loss).backward()
        
        # Optimize (update weights)
        scaler.step(optimizer)
        scaler.update()
        
        running_loss += loss.item()
        
        # Update progress bar
        loop.set_postfix(loss=loss.item())
        
    avg_loss = running_loss / len(loader)
    return avg_loss

def validate(model, loader, criterion):
    """
    Evaluates the model on validation data (unseen images).
    """
    model.eval()  # Set model to evaluation mode (no dropout/batchnorm updates)
    running_loss = 0.0
    
    with torch.no_grad():  # No need to calculate gradients for validation
        for l_input, ab_target in tqdm(loader, desc="Validation", leave=False):
            l_input = l_input.to(DEVICE)
            ab_target = ab_target.to(DEVICE)
            
            ab_predicted = model(l_input)
            loss = criterion(ab_predicted, ab_target)
            
            running_loss += loss.item()
            
    avg_loss = running_loss / len(loader)
    return avg_loss

def main():
    print(f"Using device: {DEVICE}")
    
    # 1. Setup Data Loaders
    print("Loading datasets...")
    train_dataset = ColorizationDataset(split="train")
    val_dataset = ColorizationDataset(split="val")
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
    
    # 2. Setup Model
    print("Initializing model...")
    model = ColorizationNet().to(DEVICE)
    
    # Freeze encoder (Transfer Learning)
    for param in model.encoder.parameters():
        param.requires_grad = False
        
    # 3. Setup Loss and Optimizer
    criterion = nn.L1Loss() 
    optimizer = optim.Adam(model.decoder.parameters(), lr=LEARNING_RATE)
    scaler = torch.cuda.amp.GradScaler(enabled=(DEVICE=="cuda"))
    
    # 4. Check for Checkpoints to Resume
    os.makedirs(SAVE_DIR, exist_ok=True)
    checkpoint_path = os.path.join(SAVE_DIR, "last_checkpoint.pth")
    best_model_path = os.path.join(SAVE_DIR, "colorizer.pth")
    
    start_epoch = 0
    best_val_loss = float("inf")
    
    if os.path.exists(checkpoint_path):
        print(f"Found checkpoint at {checkpoint_path}. Resuming...")
        checkpoint = torch.load(checkpoint_path, map_location=DEVICE)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_loss = checkpoint['best_val_loss']
        print(f"Resuming from Epoch {start_epoch+1}")
    elif os.path.exists(best_model_path):
        print(f"Found existing weights at {best_model_path}. Loading weights but restarting Epoch counter...")
        model.load_state_dict(torch.load(best_model_path, map_location=DEVICE))
        print("Model knowledge restored. Training will show Epoch 1/20 but is building on previous work.")
    
    # 5. Training Loop
    print("\n" + "="*30)
    print("      STARTING TRAINING      ")
    print("="*30)
    
    for epoch in range(start_epoch, NUM_EPOCHS):
        print(f"\nEpoch {epoch+1}/{NUM_EPOCHS}")
        
        # Train
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, scaler)
        
        # Validate
        val_loss = validate(model, val_loader, criterion)
        
        print(f"Result: Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f}")
        
        # Save "last" checkpoint (for resuming)
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'best_val_loss': best_val_loss,
        }, checkpoint_path)
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_model_path)
            print(f"--> New best model saved to {best_model_path} 🟢")
            
    print("\n" + "="*30)
    print("      TRAINING COMPLETE      ")
    print("="*30)
    print(f"Final Best Validation Loss: {best_val_loss:.5f}")

if __name__ == "__main__":
    main()
