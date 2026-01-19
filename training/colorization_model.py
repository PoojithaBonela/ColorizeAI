import torch
import torch.nn as nn
import torchvision.models as models

class ColorizationNet(nn.Module):
    def __init__(self, input_size=128):
        super(ColorizationNet, self).__init__()
        
        # 1. Load Pretrained ResNet18
        # We start with a model pre-trained on ImageNet to leverage "world knowledge"
        resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        
        # 2. Encoder: Remove the last two layers (AvgPool and FC)
        # ResNet18 downsamples by factor of 32 (2^5)
        # Input: (1, 256, 256) -> adapted to (3, 256, 256)
        # Output: (512, 8, 8)
        self.encoder = nn.Sequential(*list(resnet.children())[:-2])
        
        # 3. Input Adapter (1 channel -> 3 channels)
        # ResNet expects RGB, so we map our Grayscale L channel to 3 channels using a 1x1 conv
        self.input_adapter = nn.Conv2d(1, 3, kernel_size=1)
        
        # 4. Decoder: Upsample from (512, 8, 8) back to (2, 256, 256)
        # We need 5 upsampling steps (x2 each) to go from 8 to 256 (8 * 2^5 = 256)
        self.decoder = nn.Sequential(
            # Block 1: 512 -> 256 (8x8 -> 16x16)
            nn.Conv2d(512, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
            
            # Block 2: 256 -> 128 (16x16 -> 32x32)
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
            
            # Block 3: 128 -> 64 (32x32 -> 64x64)
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
            
            # Block 4: 64 -> 32 (64x64 -> 128x128)
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
            
            # Block 5: 32 -> 16 (128x128 -> 256x256)
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
            
            # Final Layer: 16 -> 2 (AB Channels)
            nn.Conv2d(16, 2, kernel_size=3, padding=1)
        )

    def forward(self, x):
        # x shape: (Batch, 1, H, W)
        x = self.input_adapter(x)  # -> (Batch, 3, H, W)
        x = self.encoder(x)        # -> (Batch, 512, H/32, W/32)
        x = self.decoder(x)        # -> (Batch, 2, H, W)
        return x

if __name__ == "__main__":
    # Simple verification if run directly
    model = ColorizationNet()
    dummy_input = torch.randn(1, 1, 256, 256)
    output = model(dummy_input)
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    assert output.shape == (1, 2, 256, 256), "Output shape mismatch!"
    print("Model architecture verification passed!")
