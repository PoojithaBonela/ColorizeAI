from colorization_model import ColorizationNet
import torch

def setup_model_for_training():
    print("Loading ColorizationNet...")
    model = ColorizationNet()
    
    # Check initial requires_grad status (should be True by default)
    # just checking one parameter from encoder
    first_param = next(model.encoder.parameters())
    print(f"Initial encoder grad status: {first_param.requires_grad}")

    print("Freezing encoder layers...")
    # Step 4B: Freeze the encoder
    for param in model.encoder.parameters():
        param.requires_grad = False
        
    # Verify freezing
    print(f"Encoder grad status after freeze: {first_param.requires_grad}")
    
    # Verify decoder is NOT frozen
    decoder_param = next(model.decoder.parameters())
    print(f"Decoder grad status: {decoder_param.requires_grad}")
    
    # Verify input adapter is NOT frozen (we want to learn the mapping from L -> RGB start)
    adapter_param = next(model.input_adapter.parameters())
    print(f"Input adapter grad status: {adapter_param.requires_grad}")

    return model

if __name__ == "__main__":
    model = setup_model_for_training()
    
    # Double check tensor shapes with a real forward pass
    dummy = torch.randn(1, 1, 256, 256)
    out = model(dummy)
    print(f"Forward pass output shape: {out.shape}")
    print("Encoder frozen. Decoder ready to be trained.")
