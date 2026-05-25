from pytorchvideo.models.hub import slowfast_r50
import torch

# Load model directly (safe method)
model = slowfast_r50(pretrained=True)

model.eval()

print("SlowFast model loaded successfully!")