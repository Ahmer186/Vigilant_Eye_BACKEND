# services/model_loader.py

import torch
import torch.nn as nn
from pytorchvideo.models.hub import slowfast_r50
from ultralytics import YOLO

MODEL_PATH = "slowfast_finetuned.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =============================
# LOAD SLOWFAST
# =============================
model_sf = slowfast_r50(pretrained=False)
in_features = model_sf.blocks[-1].proj.in_features
model_sf.blocks[-1].proj = nn.Linear(in_features, 2)

state_dict = torch.load(MODEL_PATH, map_location=DEVICE)

new_state_dict = {}
for k, v in state_dict.items():
    if k.startswith("module."):
        new_state_dict[k[7:]] = v
    else:
        new_state_dict[k] = v

model_sf.load_state_dict(new_state_dict)
model_sf = model_sf.to(DEVICE)
model_sf.eval()

print("✅ SlowFast Loaded")

# =============================
# LOAD YOLO
# =============================
yolo_model = YOLO("yolov8n.pt")
yolo_model.to(DEVICE)
print("✅ YOLO Loaded")
# ai_model.py mein yeh add karo existing models ke saath
from ultralytics import YOLO

smoking_model = YOLO('smoking_best11.pt')
smoking_model.to(DEVICE)