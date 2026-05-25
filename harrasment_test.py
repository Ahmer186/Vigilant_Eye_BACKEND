import cv2
import numpy as np
from collections import deque
from deepface import DeepFace
from ultralytics import YOLO

# ---------------------------- CONFIG ----------------------------
EMOTION_TARGETS = ["fear", "surprise", "sad", "angry"]
DIST_THRESHOLD_PIXELS = 250
HARASSMENT_FRAMES = 3

VIDEO_SOURCE = r"frnd/gettyimages-1681860519-640_adpp.mp4"

# ---------------------------- LOAD MODELS ----------------------------
yolo_model = YOLO("yolov8n.pt")

# ---------------------------- EMOTION ----------------------------
def get_emotion(face_img):
    try:
        result = DeepFace.analyze(
            img_path=face_img,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend='opencv',
            silent=True
        )
        return result[0]['dominant_emotion']
    except:
        return "unknown"

# ---------------------------- DISTANCE ----------------------------
def is_near(box1, box2):
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2

    c1 = ((x1 + x2) // 2, (y1 + y2) // 2)
    c2 = ((x3 + x4) // 2, (y3 + y4) // 2)

    dist = ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2) ** 0.5
    print(f"[DEBUG] Distance: {dist}")

    return dist < DIST_THRESHOLD_PIXELS

# ---------------------------- DATA ----------------------------
emotion_buffers = {}

# ---------------------------- VIDEO ----------------------------
cap = cv2.VideoCapture(VIDEO_SOURCE)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    annotated_frame = frame.copy()
    results = yolo_model.track(frame, persist=True, classes=[0], conf=0.5, tracker="bytetrack.yaml")

    if results:
        boxes = results[0].boxes
        persons = []

        # -------- Collect persons --------
        for box in boxes:
            if box.id is None:
                continue

            pid = int(box.id.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]

            # Face region (top 40%)
            face_crop = crop[0:int((y2 - y1) * 0.4), :]

            if face_crop.shape[0] < 40 or face_crop.shape[1] < 40:
                continue

            persons.append((pid, (x1, y1, x2, y2), face_crop))

        # -------- Process each person --------
        for pid, (x1, y1, x2, y2), face_crop in persons:

            # Emotion detect
            emotion = get_emotion(face_crop)
            print(f"[DEBUG] ID:{pid} Emotion:{emotion}")

            if pid not in emotion_buffers:
                emotion_buffers[pid] = deque(maxlen=HARASSMENT_FRAMES)

            emotion_buffers[pid].append(emotion)

            # -------- HARASSMENT LOGIC --------
            harassment = False

            if len(emotion_buffers[pid]) == HARASSMENT_FRAMES:
                # Kam az kam 2 baar negative emotion aaye
                if sum(e in EMOTION_TARGETS for e in emotion_buffers[pid]) >= 2:
                    for other_id, other_box, _ in persons:
                        if other_id == pid:
                            continue
                        if is_near((x1, y1, x2, y2), other_box):
                            harassment = True
                            break

            # -------- DRAW --------
            label = "HARASSMENT ⚠️" if harassment else "Normal"
            color = (0, 0, 255) if harassment else (0, 255, 0)

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated_frame,
                f"ID:{pid} | {label}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

    cv2.imshow("Harassment Detection", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()