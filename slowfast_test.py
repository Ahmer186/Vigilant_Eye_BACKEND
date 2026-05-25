import torch
import torch.nn as nn
import cv2
import numpy as np
from pytorchvideo.models.hub import slowfast_r50

# =============================
# CONFIG
# =============================
MODEL_PATH = "slowfast_finetuned.pth"
VIDEO_PATH = r"frnd\123232-727221558.mp4"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = ["Fighting", "Normal"]   # ⚠️ check alphabetical order
CLIP_LEN = 32

# =============================
# NORMALIZATION (SAME AS TRAINING)
# =============================
class VideoNormalize(torch.nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.mean = torch.tensor(mean).view(-1,1,1,1)
        self.std = torch.tensor(std).view(-1,1,1,1)

    def forward(self, x):
        return (x - self.mean) / self.std

transform = VideoNormalize(
    mean=[0.45, 0.45, 0.45],
    std=[0.225, 0.225, 0.225]
)

# =============================
# CREATE MODEL STRUCTURE
# =============================
model = slowfast_r50(pretrained=False)

in_features = model.blocks[-1].proj.in_features
model.blocks[-1].proj = nn.Linear(in_features, 2)

# =============================
# LOAD MODEL (FIXED FOR PYTORCH 2.6)
# =============================
state_dict = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=False   # 🔥 IMPORTANT FIX
)

# 🔥 Remove "module." if exists
new_state_dict = {}
for k, v in state_dict.items():
    if k.startswith("module."):
        new_state_dict[k[7:]] = v
    else:
        new_state_dict[k] = v

model.load_state_dict(new_state_dict)

model = model.to(DEVICE)
model.eval()

print("✅ Model Loaded Successfully")

# =============================
# LOAD VIDEO
# =============================
cap = cv2.VideoCapture(VIDEO_PATH)
frames = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (256, 256))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frames.append(frame)

cap.release()

print("Total Frames:", len(frames))

# =============================
# FRAME HANDLING
# =============================
if len(frames) == 0:
    frames = np.zeros((CLIP_LEN, 256, 256, 3), dtype=np.float32)

if len(frames) < CLIP_LEN:
    repeat = (CLIP_LEN // len(frames)) + 1
    frames = frames * repeat

frames = frames[:CLIP_LEN]

frames = np.array(frames, dtype=np.float32) / 255.0
frames = torch.from_numpy(frames).permute(3,0,1,2)

frames = transform(frames)

# =============================
# SLOWFAST INPUT
# =============================
slow = frames[:, ::4, :, :]
fast = frames

slow = slow.unsqueeze(0).to(DEVICE)
fast = fast.unsqueeze(0).to(DEVICE)

# =============================
# INFERENCE
# =============================
with torch.no_grad():
    outputs = model([slow, fast])
    probs = torch.softmax(outputs, dim=1)

    pred = torch.argmax(probs, dim=1).item()

print("\n🎯 Prediction:", CLASS_NAMES[pred])
print("Confidence:", probs[0][pred].item())