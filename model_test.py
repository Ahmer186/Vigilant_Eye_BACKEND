import torch
import torch.nn as nn
import cv2
import numpy as np
from pytorchvideo.models.hub import slowfast_r50
from ultralytics import YOLO
from deepface import DeepFace
import os

# =============================
# CONFIG
# =============================
MODEL_PATH = "slowfast_finetuned.pth"
VIDEO_PATH = "frnd/111.mp4"
FACE_DB_PATH = r"frnd\face"   # 👈 your images folder
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = ["Fighting", "Normal"]
CLIP_LEN = 32

# =============================
# NORMALIZATION
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
# LOAD SLOWFAST
# =============================
model_sf = slowfast_r50(pretrained=False)
in_features = model_sf.blocks[-1].proj.in_features
model_sf.blocks[-1].proj = nn.Linear(in_features, 2)

state_dict = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)

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
print("✅ YOLO Loaded")

# =============================
# VIDEO
# =============================
cap = cv2.VideoCapture(VIDEO_PATH)

frame_buffer = []
identified_people = set()

sf_pred = "Analyzing..."
sf_conf = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    display_frame = frame.copy()

    # =============================
    # YOLO PERSON DETECTION
    # =============================
    results = yolo_model(frame)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])

            if cls == 0:  # person
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                person_crop = frame[y1:y2, x1:x2]

                name = "Unknown"

                try:
                    result = DeepFace.find(
                        img_path=person_crop,
                        db_path=FACE_DB_PATH,
                        enforce_detection=False
                    )

                    if len(result) > 0 and len(result[0]) > 0:
                        identity_path = result[0].iloc[0]['identity']
                        name = os.path.basename(identity_path).split('.')[0]
                        identified_people.add(name)

                except:
                    pass

                # Draw box + name
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(display_frame, name, (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    # =============================
    # SLOWFAST BUFFER
    # =============================
    frame_sf = cv2.resize(frame, (256, 256))
    frame_sf = cv2.cvtColor(frame_sf, cv2.COLOR_BGR2RGB)
    frame_buffer.append(frame_sf)

    if len(frame_buffer) == CLIP_LEN:
        frames = np.array(frame_buffer, dtype=np.float32) / 255.0
        frames = torch.from_numpy(frames).permute(3,0,1,2)
        frames = transform(frames)

        slow = frames[:, ::4, :, :]
        fast = frames

        slow = slow.unsqueeze(0).to(DEVICE)
        fast = fast.unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model_sf([slow, fast])
            probs = torch.softmax(outputs, dim=1)
            pred = torch.argmax(probs, dim=1).item()

        sf_pred = CLASS_NAMES[pred]
        sf_conf = probs[0][pred].item()

        frame_buffer = []

    # =============================
    # DISPLAY
    # =============================
    if sf_pred == "Fighting":
        cv2.putText(display_frame, "🔥 FIGHT DETECTED!",
                    (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)

    cv2.putText(display_frame,
                f"{sf_pred} ({sf_conf:.2f})",
                (50,100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255,255,0),
                2)

    cv2.imshow("Final System", display_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

# =============================
# FINAL OUTPUT
# =============================
print("\n================ FINAL RESULT ================")
print("Fight Detected:", sf_pred)
print("Confidence:", sf_conf)

if len(identified_people) > 0:
    print("People Involved:")
    for p in identified_people:
        print("-", p)
else:
    print("No known person detected")