# import cv2
# import torch
# import numpy as np
# from ultralytics import YOLO
# from pytorchvideo.models.hub import slowfast_r50
# from torchvision.transforms import Compose, Lambda
#
# # ------------------ CONFIG ------------------
# VIDEO_PATH = "frnd/fighting9.mp4"      # Input video path
# OUTPUT_PATH = "frnd/fighting333.mp4"    # Output video path
# FRAME_LIMIT = 32                     # SlowFast clip length
# FIGHT_CLASSES = [23, 24, 25, 26]    # Fighting class IDs
#
# # ------------------ LOAD MODELS ------------------
# device = "cuda" if torch.cuda.is_available() else "cpu"
#
# # YOLOv8 small
# yolo_model = YOLO("yolov8n.pt")
#
# # SlowFast pretrained
# slowfast_model = slowfast_r50(pretrained=True)
# slowfast_model.eval()
# slowfast_model = slowfast_model.to(device)
#
# # ------------------ TRANSFORMS ------------------
# transform = Compose([
#     Lambda(lambda x: x / 255.0),
#     Lambda(lambda x: (x - 0.45) / 0.225)
# ])
#
# # ------------------ VIDEO SETUP ------------------
# cap = cv2.VideoCapture(VIDEO_PATH)
# frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# fps = cap.get(cv2.CAP_PROP_FPS)
#
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (frame_width, frame_height))
#
# frame_buffer = []
# fight_detected = False  # Track cumulative fight
# fight_label = "Analyzing..."
#
# # ------------------ PROCESS VIDEO ------------------
# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     display_frame = frame.copy()
#
#     # ------------------ YOLO PERSON DETECTION ------------------
#     results = yolo_model(frame)
#     person_count = 0
#     persons_boxes = []
#     for r in results:
#         for box in r.boxes:
#             cls = int(box.cls[0])
#             if cls == 0:  # person
#                 person_count += 1
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 persons_boxes.append((x1, y1, x2, y2))
#
#     # ------------------ FRAME BUFFER FOR SLOWFAST ------------------
#     frame_resized = cv2.resize(frame, (256, 256))
#     frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
#     frame_buffer.append(frame_rgb)
#     if len(frame_buffer) > FRAME_LIMIT:
#         frame_buffer.pop(0)
#
#     # ------------------ SLOWFAST PREDICTION ------------------
#     if len(frame_buffer) == FRAME_LIMIT:
#         frames = np.array(frame_buffer)
#         frames = torch.tensor(frames).permute(3,0,1,2).float()  # C,T,H,W
#         frames = transform(frames)
#
#         slow = frames[:, ::4, :, :]
#         fast = frames
#         inputs = [slow.unsqueeze(0).to(device), fast.unsqueeze(0).to(device)]
#
#         with torch.no_grad():
#             preds = slowfast_model(inputs)
#         pred_class = preds.argmax().item()
#         if pred_class in FIGHT_CLASSES:
#             fight_label = "FIGHTING"
#             fight_detected = True
#         else:
#             fight_label = "NORMAL"
#
#     # ------------------ FINAL LABEL ------------------
#     final_label = "FIGHTING" if fight_detected else "NORMAL"
#     color = (0,0,255) if final_label=="FIGHTING" else (0,255,0)
#
#     # Draw bounding boxes with color
#     for x1, y1, x2, y2 in persons_boxes:
#         cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
#
#     # Display info
#     cv2.putText(display_frame, f"Persons: {person_count}", (20,40),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
#     cv2.putText(display_frame, f"Action: {final_label}", (20,80),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
#
#     # ------------------ WRITE FRAME TO OUTPUT ------------------
#     out.write(display_frame)
#
#     # Optional: show real-time
#     cv2.imshow("YOLO + SlowFast", display_frame)
#     if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
#         break
#
# # ------------------ CLEANUP ------------------
# cap.release()
# out.release()
# cv2.destroyAllWindows()
# print(f"✅ Video processed and saved: {OUTPUT_PATH}")
# print(f"Final cumulative action in video: {final_label}")
# ###############################################
import torch
import cv2
import numpy as np
from torchvision.transforms import Compose, Resize, ToTensor
from pytorchvideo.models.hub import slowfast_r50  # we use this to define architecture
from torch.nn import functional as F

# --------- 1. Device setup ---------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --------- 2. Load YOUR trained SlowFast model ---------
# Create a new SlowFast model (same architecture as your trained one)
model = slowfast_r50(pretrained=False)  # architecture only
state_dict = torch.load("full_slowfast_model.pth", map_location=device)  # your trained weights
model.load_state_dict(state_dict)  # load your trained weights
model.to(device)
model.eval()

# --------- 3. Video capture ---------
video_path = "frnd/fighting32.mp4"  # replace with your video path
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# --------- 4. Preprocessing for SlowFast ---------
transform = Compose([
    Resize((256, 256)),  # resize frame
    ToTensor(),
])

def prepare_clip(frames, device):
    """
    Prepare clip for SlowFast input
    SlowFast expects [batch_size, 3, num_frames, H, W]
    and two pathways: slow (sampled), fast (full)
    """
    clip = torch.stack([transform(frame) for frame in frames])  # [T, C, H, W]
    clip = clip.permute(1, 0, 2, 3).unsqueeze(0).to(device)     # [1, C, T, H, W]

    # Slow pathway (1/4 frames)
    slow_pathway = torch.index_select(
        clip, 2, torch.linspace(0, clip.shape[2]-1, clip.shape[2]//4).long()
    )
    fast_pathway = clip

    return [slow_pathway, fast_pathway]

# --------- 5. Read video in clips ---------
clip_length = 32  # number of frames per clip
frames = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to RGB
    frames.append(frame)

    if len(frames) == clip_length:
        # Prepare input for SlowFast
        clip_input = prepare_clip(frames, device)

        # Inference
        with torch.no_grad():
            preds = model(clip_input)
            probs = F.softmax(preds, dim=1)
            class_id = torch.argmax(probs, dim=1).item()
            print(f"Predicted class ID: {class_id}, confidence: {probs[0,class_id]:.3f}")

        frames = []  # reset for next clip

cap.release()
print("Video testing done!")