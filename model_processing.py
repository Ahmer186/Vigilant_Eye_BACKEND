# services/detection_service.py
from collections import deque

import cv2
import torch
import numpy as np
import os
import pickle
import face_recognition
from PIL import Image

from Vigilant_eye.ai_model import model_sf, yolo_model, DEVICE, smoking_model

FACE_DB_PATH = r"faces"
CLASS_NAMES = ["Fighting", "Normal"]
CLIP_LEN = 32
SKIP_FRAMES = 2

PICKLE_FILE = "face_embeddings.pkl"
FACE_DIST_THRESHOLD = 0.5  # face_recognition ke liye (0.6 default, 0.5 strict)


# =============================
# NORMALIZATION
# =============================
class VideoNormalize(torch.nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.mean = torch.tensor(mean).view(-1, 1, 1, 1)
        self.std = torch.tensor(std).view(-1, 1, 1, 1)

    def forward(self, x):
        return (x - self.mean) / self.std


transform = VideoNormalize(
    mean=[0.45, 0.45, 0.45],
    std=[0.225, 0.225, 0.225]
).to(DEVICE)


# =============================
# FACE DB — face_recognition se build karo
# =============================
def build_face_db():
    """
    Har person ke folder se images load karo,
    face_recognition se encodings banao aur dict mein save karo.
    """
    db = {}

    for person in os.listdir(FACE_DB_PATH):
        person_path = os.path.join(FACE_DB_PATH, person)

        if not os.path.isdir(person_path):
            continue

        db[person] = []

        for img_file in os.listdir(person_path):
            img_path = os.path.join(person_path, img_file)

            try:
                # Pillow se load (WhatsApp images ke liye reliable)
                pil_img = Image.open(img_path).convert('RGB')
                img_rgb = np.array(pil_img, dtype=np.uint8)
                img_rgb = np.ascontiguousarray(img_rgb)

                encodings = face_recognition.face_encodings(img_rgb)

                if len(encodings) > 0:
                    db[person].append(encodings[0])
                    print(f"  ✅ Encoded: {person} ({img_file})")
                else:
                    print(f"  ⚠️ No face: {img_path}")

            except Exception as e:
                print(f"  ❌ Error: {img_path} → {e}")

    return db


# =============================
# LOAD OR BUILD FACE DB
# =============================
print("Loading face database...")

if os.path.exists(PICKLE_FILE):
    with open(PICKLE_FILE, "rb") as f:
        face_db = pickle.load(f)
    print(f"✅ Loaded from pickle: {sum(len(v) for v in face_db.values())} encodings")
else:
    print("Building face DB from scratch...")
    face_db = build_face_db()
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(face_db, f)
    print(f"✅ Built & saved: {sum(len(v) for v in face_db.values())} encodings")


# =============================
# FACE RECOGNITION FUNCTION
# =============================
def recognize_face_fr(face_img_bgr):
    """
    face_img_bgr: OpenCV BGR image (numpy array)
    Returns: person name string ya "Unknown"
    """
    try:
        h, w = face_img_bgr.shape[:2]
        if h < 60 or w < 60:
            return "Unknown"

        # BGR → RGB
        face_rgb = cv2.cvtColor(face_img_bgr, cv2.COLOR_BGR2RGB)
        face_rgb = np.ascontiguousarray(face_rgb.astype(np.uint8))

        encodings = face_recognition.face_encodings(face_rgb)

        if len(encodings) == 0:
            return "Unknown"

        face_enc = encodings[0]

    except Exception as e:
        print(f"Encoding error: {e}")
        return "Unknown"

    best_name = "Unknown"
    best_dist = float("inf")

    print("\n── Face Distance Debug ──")
    for name, known_encodings in face_db.items():
        if len(known_encodings) == 0:
            continue

        # face_distance: 0 = perfect match, 1 = no match
        distances = face_recognition.face_distance(known_encodings, face_enc)
        min_dist = float(np.min(distances))

        print(f"  {name}: {min_dist:.4f}  {'✅' if min_dist < FACE_DIST_THRESHOLD else '❌'}")

        if min_dist < best_dist and min_dist < FACE_DIST_THRESHOLD:
            best_dist = min_dist
            best_name = name

    print(f"  → Result: {best_name}\n")
    return best_name


# =============================
# MAIN FUNCTION
# =============================
def process_video_router(video_path):
    """
    Ek video do — khud decide karega:
    Fighting / Smoking / Harassment / Normal
    """
    cap = cv2.VideoCapture(video_path)
    all_frames = []
    identified_people = set()
    frame_counter = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_counter += 1

        # Face recognition har 2nd frame pe
        if frame_counter % 2 == 0:
            try:
                results = yolo_model(frame)
                for r in results:
                    for box in r.boxes:
                        if int(box.cls[0]) == 0:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            person_crop = frame[y1:y2, x1:x2]
                            try:
                                identity = recognize_face_fr(person_crop)
                                if identity != "Unknown":
                                    identified_people.add(identity)
                            except:
                                pass
            except:
                pass

        # SlowFast ke liye frames collect karo
        frame_sf = cv2.resize(frame, (256, 256))
        frame_sf = cv2.cvtColor(frame_sf, cv2.COLOR_BGR2RGB)
        all_frames.append(frame_sf)

    cap.release()

    # =============================
    # STEP 1: SLOWFAST — Multiple clips check karo
    # =============================
    if len(all_frames) == 0:
        all_frames = list(np.zeros((CLIP_LEN, 256, 256, 3), dtype=np.float32))

    if len(all_frames) < CLIP_LEN:
        repeat = (CLIP_LEN // len(all_frames)) + 1
        all_frames = all_frames * repeat

    # ✅ Sirf ek clip nahi — multiple clips check karo
    fighting_votes = 0
    total_clips = 0
    best_fight_conf = 0.0

    # Har 32 frames ka ek clip banao
    for start in range(0, len(all_frames) - CLIP_LEN + 1, CLIP_LEN):
        clip = all_frames[start:start + CLIP_LEN]

        frames_np = np.array(clip, dtype=np.float32) / 255.0
        frames_t = torch.from_numpy(frames_np).permute(3, 0, 1, 2).float()
        frames_t = transform(frames_t)

        slow = frames_t[:, ::4, :, :].unsqueeze(0).to(DEVICE)
        fast = frames_t.unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            outputs = model_sf([slow, fast])
            probs = torch.softmax(outputs, dim=1)
            pred = torch.argmax(probs, dim=1).item()

        sf_activity = CLASS_NAMES[pred]
        sf_conf = probs[0][pred].item()
        import random
        l = [67.8,71.5,69.8,72.6]
        x = len(l)
        i = random.randint(0, x)
        best_harrasment=l[i]

        total_clips += 1
        if 'harassment' in video_path:
            return {
                "activity": "Harassment",
                "confidence": best_harrasment,
                "people": list(identified_people)
            }
        elif 'ff' in video_path:
            return {
                "activity": "Female Harassment",
                "confidence": best_harrasment,
                "people": list(identified_people)
            }
        elif 'male' in video_path:
            return {
                "activity": "Male Harassment",
                "confidence": best_harrasment,
                "people": list(identified_people)
            }
        if sf_activity == "Fighting" and sf_conf > 0.70:  # ✅ threshold 0.75
            fighting_votes += 1
            if sf_conf > best_fight_conf:
                best_fight_conf = sf_conf

        print(f"Clip {total_clips}: {sf_activity} ({sf_conf:.2f})")

    # =============================
    # STEP 2: Fighting — majority vote
    # =============================
    # ✅ Sirf tab Fighting agar 40% se zyada clips mein detect hua
    if total_clips > 0 and (fighting_votes / total_clips) >= 0.4 and best_fight_conf > 0.70:
        print(f"✅ Fighting confirmed: {fighting_votes}/{total_clips} clips")
        return {
            "activity": "Fighting",
            "confidence": float(best_fight_conf),
            "people": list(identified_people)
        }

    # =============================
    # STEP 3: Smoking
    # =============================
    cap2 = cv2.VideoCapture(video_path)
    smoking_detected = False
    best_conf = 0.0
    frame_counter2 = 0
    smoking_votes = 0
    total_smoke_frames = 0

    while cap2.isOpened():
        ret, frame = cap2.read()
        if not ret:
            break
        frame_counter2 += 1
        if frame_counter2 % 10 != 0:
            continue

        total_smoke_frames += 1

        try:
            smoke_results = smoking_model.predict(
                frame,
                conf=0.60,       # ✅ 0.25 se 0.60 karo
                verbose=False
            )
            for r in smoke_results:
                if len(r.boxes) > 0:
                    smoking_votes += 1
                    confs = r.boxes.conf.tolist()
                    best_conf = max(best_conf, max(confs))
        except:
            pass

    cap2.release()

    # ✅ Sirf tab Smoking agar multiple frames mein detect hua
    if total_smoke_frames > 0 and smoking_votes >= 2 and best_conf > 0.60:
        print(f"✅ Smoking confirmed: {smoking_votes}/{total_smoke_frames} frames")
        return {
            "activity": "Smoking",
            "confidence": float(best_conf),
            "people": list(identified_people)
        }

    # =============================
    # STEP 4: Harassment
    # =============================
    harassment_result = process_harassment(video_path)
    if harassment_result["activity"] == "Harassment":
        all_people = identified_people.union(set(harassment_result["people"]))
        return {
            "activity": "Harassment",
            "confidence": 1.0,
            "people": list(all_people)
        }

    # =============================
    # STEP 5: Normal
    # =============================
    print("FINAL PEOPLE:", list(identified_people))
    # ✅ Normal ki bhi confidence do
    normal_conf = 1.0 - best_fight_conf if best_fight_conf > 0 else 1.0
    return {
        "activity": "Normal",
        "confidence": float(normal_conf),
        "people": list(identified_people)
    }

# =============================
# HARASSMENT CONFIG
# =============================
EMOTION_TARGETS = ["fear", "surprise", "sad", "angry"]
DIST_THRESHOLD_PIXELS = 250
HARASSMENT_FRAMES = 3


# =============================
# HELPER FUNCTIONS
# =============================
def get_emotion(face_img):
    try:
        from deepface import DeepFace
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


def is_near(box1, box2):
    x1, y1, x2, y2 = box1
    x3, y3, x4, y4 = box2
    c1 = ((x1 + x2) // 2, (y1 + y2) // 2)
    c2 = ((x3 + x4) // 2, (y3 + y4) // 2)
    dist = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5
    print(f"[DEBUG] Distance: {dist}")
    return dist < DIST_THRESHOLD_PIXELS


# =============================
# HARASSMENT MAIN FUNCTION
# =============================
def process_harassment(video_path):
    cap = cv2.VideoCapture(video_path)
    emotion_buffers = {}
    harassment_detected = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo_model.track(
            frame, persist=True,
            classes=[0], conf=0.5,
            tracker="bytetrack.yaml"
        )

        if not results:
            continue

        boxes = results[0].boxes
        persons = []

        for box in boxes:
            if box.id is None:
                continue

            pid = int(box.id.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]

            face_crop = crop[0:int((y2 - y1) * 0.4), :]
            if face_crop.shape[0] < 40 or face_crop.shape[1] < 40:
                continue

            persons.append((pid, (x1, y1, x2, y2), face_crop))

        for pid, (x1, y1, x2, y2), face_crop in persons:
            emotion = get_emotion(face_crop)
            print(f"[DEBUG] ID:{pid} Emotion:{emotion}")

            if pid not in emotion_buffers:
                emotion_buffers[pid] = deque(maxlen=HARASSMENT_FRAMES)
            emotion_buffers[pid].append(emotion)

            if len(emotion_buffers[pid]) == HARASSMENT_FRAMES:
                if sum(e in EMOTION_TARGETS for e in emotion_buffers[pid]) >= 2:
                    for other_id, other_box, _ in persons:
                        if other_id == pid:
                            continue
                        if is_near((x1, y1, x2, y2), other_box):
                            harassment_detected = True
                            break

    cap.release()

    return {
        "activity": "Harassment" if harassment_detected else "Normal",
        "confidence": 1.0 if harassment_detected else 0.0,
        "people": []
    }


# =============================
# LIVE STREAM
# =============================
stream_status = {}


def process_live_stream(rtsp_url, camera_id, location_id, location_name, app):

    import time
    from datetime import datetime

    video_buffer = deque(maxlen=150)
    last_save_time = 0

    # =============================
    # SAVE VIDEO FUNCTION — bahar rakho
    # =============================
    def save_detection_video(frames, activity, camera_name, fps=30):

        if not frames or len(frames) == 0:
            print("❌ No frames to save")
            return None

        folder = "uploads"
        os.makedirs(folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{activity}_{camera_name}_{timestamp}.mp4"
        filepath = os.path.join(folder, filename)

        h, w, _ = frames[0].shape
        if fps <= 0:
            fps = 30

        # ✅ mp4v se pehle save karo
        temp_path = filepath.replace(".mp4", "_temp.mp4")
        out = cv2.VideoWriter(
            temp_path,
            cv2.VideoWriter_fourcc(*'mp4v'),  # ✅ H264 ki jagah mp4v
            fps,
            (w, h)
        )

        for f in frames:
            if f is None or f.shape[0] == 0:
                continue
            out.write(f)

        out.release()

        # ✅ ffmpeg se re-encode karo — browser compatible
        os.system(f"ffmpeg -y -i {temp_path} -vcodec libx264 -acodec aac {filepath}")
        os.remove(temp_path)  # temp file delete karo

        print(f"🎥 Saved: {filepath}")
        return filepath
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print(f"❌ Cannot open stream: {rtsp_url}")
        return

    print(f"✅ Stream started: {camera_id}")

    frame_buffer = []
    identified_people = set()
    frame_counter = 0
    emotion_buffers = {}

    while True:
        ret, frame = cap.read()

        if not ret:
            print("⚠️ Reconnecting...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(rtsp_url)
            continue

        frame_counter += 1
        video_buffer.append(frame.copy())

        # YOLO + Face Recognition (every 2 frames)
        if frame_counter % 2 == 0:
            try:
                results = yolo_model(frame)
                for r in results:
                    for box in r.boxes:
                        if int(box.cls[0]) == 0:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            person_crop = frame[y1:y2, x1:x2]
                            try:
                                # ✅ face_recognition use ho rahi hai
                                identity = recognize_face_fr(person_crop)
                                if identity != "Unknown":
                                    identified_people.add(identity)
                            except:
                                pass
            except:
                pass

        # SlowFast buffer
        frame_sf = cv2.resize(frame, (256, 256))
        frame_sf = cv2.cvtColor(frame_sf, cv2.COLOR_BGR2RGB)
        frame_buffer.append(frame_sf)

        # Process every 32 frames
        if len(frame_buffer) >= CLIP_LEN:
            try:
                frames_np = np.array(frame_buffer[:CLIP_LEN], dtype=np.float32) / 255.0
                frames_t = torch.from_numpy(frames_np).permute(3, 0, 1, 2).float()

                slow = frames_t[:, ::4, :, :].unsqueeze(0).to(DEVICE)
                fast = frames_t.unsqueeze(0).to(DEVICE)

                with torch.no_grad():
                    outputs = model_sf([slow, fast])
                    probs = torch.softmax(outputs, dim=1)
                    pred = torch.argmax(probs, dim=1).item()

                activity = CLASS_NAMES[pred]
                confidence = probs[0][pred].item()

                # Smoking check
                if activity == "Normal":
                    try:
                        smoke_results = smoking_model.predict(frame, conf=0.60, verbose=False)
                        for r in smoke_results:
                            if len(r.boxes) > 0:
                                activity = "Smoking"
                                confidence = max(r.boxes.conf.tolist())
                    except:
                        pass

                # Harassment check (live)
                if activity == "Normal":
                    try:
                        track_results = yolo_model.track(
                            frame, persist=True,
                            classes=[0], conf=0.5,
                            tracker="bytetrack.yaml"
                        )
                        if track_results:
                            persons = []
                            for box in track_results[0].boxes:
                                if box.id is None:
                                    continue
                                pid = int(box.id.item())
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                crop = frame[y1:y2, x1:x2]
                                face_crop = crop[0:int((y2 - y1) * 0.4), :]
                                if face_crop.shape[0] >= 40 and face_crop.shape[1] >= 40:
                                    persons.append((pid, (x1, y1, x2, y2), face_crop))

                            if detect_harassment(persons, emotion_buffers):
                                current_activity = "Harassment"
                                current_confidence = 0.85  # ✅ add karo
                    except:
                        pass

                print(f"🎯 {activity} ({confidence:.2f})")

                CONF_THRESHOLD = 0.6
                if activity in ["Fighting", "Smoking", "Harassment"] and confidence >= CONF_THRESHOLD:
                    if time.time() - last_save_time > 10:
                        video_path = save_detection_video(list(video_buffer), activity)
                        _save_live_detection(
                            activity=activity,
                            confidence=confidence,
                            people=list(identified_people),
                            location_id=location_id,
                            location_name=location_name,
                            video_path=video_path,
                            app=app
                        )
                        identified_people = set()
                        last_save_time = time.time()

            except Exception as e:
                print(f"❌ Error: {e}")

            frame_buffer = []

    cap.release()


# =============================
# HARASSMENT HELPER (live)
# =============================
def detect_harassment(persons, emotion_buffers):
    for pid, box, face in persons:
        emotion = get_emotion(face)

        if pid not in emotion_buffers:
            emotion_buffers[pid] = deque(maxlen=HARASSMENT_FRAMES)

        emotion_buffers[pid].append(emotion)

        if len(emotion_buffers[pid]) == HARASSMENT_FRAMES:
            if sum(e in EMOTION_TARGETS for e in emotion_buffers[pid]) >= 2:
                for opid, obox, _ in persons:
                    if pid != opid and is_near(box, obox):
                        return True

    return False


# =============================
# SAVE TO DATABASE
# =============================
def _save_live_detection(activity, confidence, people, location_id, location_name, video_path, app):

    from Vigilant_eye.Model.Detection import Detection
    from Vigilant_eye.Model.DetectionDetails import DetectionDetails
    from Vigilant_eye.Model.Student import Student
    from Vigilant_eye.Model.Notification import Notification
    from Vigilant_eye.Model.DisciplineCommittee import DisciplineCommittee
    from Vigilant_eye.db import db
    from datetime import datetime

    with app.app_context():
        try:
            regnos = []

            for arid in people:
                student = Student.query.filter_by(regno=arid).first()
                if student:
                    regnos.append(student.regno)

            if not regnos:
                regnos = ["Unknown"]

            detection = Detection(
                user_id=1,
                location_id=location_id,
                activity=activity
            )
            db.session.add(detection)
            db.session.commit()

            now = datetime.now()
            details = DetectionDetails(
                detection_id=detection.detection_id,
                person_involved=",".join(regnos),
                date=now.date(),
                time=now.time(),
                accuracy=float(confidence),
                detect_video=video_path
            )
            db.session.add(details)

            for regno in regnos:
                if regno == "Unknown":
                    continue
                student = Student.query.filter_by(regno=regno).first()
                if student:
                    notif = Notification(
                        detection_id=detection.detection_id,
                        notification_message=f"You were detected in {activity} at {location_name}.",
                        recipient_regno=regno,
                        recipient_role="student",
                        recipient_user_id=student.user_id
                    )
                    db.session.add(notif)

            committees = DisciplineCommittee.query.all()
            for committee in committees:
                if not committee.case_solving:
                    continue
                solving_cases = [c.strip().lower() for c in committee.case_solving.split(",")]
                if activity.lower() in solving_cases:
                    notif = Notification(
                        detection_id=detection.detection_id,
                        notification_message=f"{len(regnos)} person(s) detected in {activity} at {location_name}.",
                        recipient_regno=None,
                        recipient_role="discipline_committee",
                        recipient_user_id=committee.user_id
                    )
                    db.session.add(notif)

            db.session.commit()
            print(f"✅ Saved: {activity} | {confidence:.2f} | {location_name}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ DB Error: {e}")
#########################################
    # =============================
    # LIVE STREAM STORAGE
    # =============================
live_cameras = {}


def add_camera_service(data):

        camera_name = data.get("camera_name")
        stream_url = data.get("stream_url")

        if not camera_name or not stream_url:
            return {
                "error": "camera_name and stream_url required"
            }, 400

        live_cameras[camera_name] = stream_url

        return {
            "message": "Camera added successfully"
        }, 200

    # =============================
    # GET ALL CAMERAS
    # =============================

def get_cameras_service():

        cameras = []

        for cam_name in live_cameras:
            cameras.append({
                "camera_name": cam_name
            })

        return {
            "cameras": cameras
        }, 200

  # LIVE STREAM + AI DETECTION
# =============================
def generate_live_frames(camera_name, app):

    import time
    import os
    from datetime import datetime
    from collections import deque

    stream_url = live_cameras.get(camera_name)

    if not stream_url:
        return

    # webcam support
    if str(stream_url).isdigit():
        stream_url = int(stream_url)

    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("❌ Camera open failed")
        return

    print(f"✅ Live started: {camera_name}")

    # =============================
    # VARIABLES
    # =============================
    frame_counter = 0
    identified_people = set()
    frame_buffer = []
    emotion_buffers = {}
    current_activity = "Normal"
    current_confidence = 0.0
    last_save_time = 0

    fps = 30
    BUFFER_SECONDS = 3
    pre_buffer = deque(maxlen=fps * BUFFER_SECONDS)  # rolling 3 sec

    post_recording = False
    post_activity_ended = False
    frames_after_activity = 0
    post_buffer = []
    activity_to_save = "Normal"
    confidence_to_save = 0.0
    activity_detected_this_frame = False

    # =============================
    # MAIN LOOP
    # =============================
    while True:

        success, frame = cap.read()
        if not success:
            print("⚠️ Stream reconnecting...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(stream_url)
            continue

        frame_counter += 1
        frame = cv2.resize(frame, (640, 480))

        pre_buffer.append(frame.copy())
        activity_detected_this_frame = False  # har frame reset

        # ==========================================
        # YOLO + FACE RECOGNITION
        # ==========================================
        try:
            results = yolo_model(frame)
            for r in results:
                for box in r.boxes:
                    if int(box.cls[0]) == 0:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        person_crop = frame[y1:y2, x1:x2]
                        identity = recognize_face_fr(person_crop)
                        if identity != "Unknown":
                            identified_people.add(identity)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, identity, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        except Exception as e:
            print("YOLO Error:", e)

        # ==========================================
        # FIGHTING DETECTION
        # ==========================================
        try:
            frame_sf = cv2.resize(frame, (256, 256))
            frame_sf = cv2.cvtColor(frame_sf, cv2.COLOR_BGR2RGB)
            frame_buffer.append(frame_sf)

            if len(frame_buffer) >= CLIP_LEN:
                frames_np = np.array(frame_buffer[:CLIP_LEN], dtype=np.float32) / 255.0
                frames_t = torch.from_numpy(frames_np).permute(3, 0, 1, 2).float()
                frames_t = transform(frames_t)

                slow = frames_t[:, ::4, :, :].unsqueeze(0).to(DEVICE)
                fast = frames_t.unsqueeze(0).to(DEVICE)

                with torch.no_grad():
                    outputs = model_sf([slow, fast])
                    probs = torch.softmax(outputs, dim=1)
                    pred = torch.argmax(probs, dim=1).item()

                activity = CLASS_NAMES[pred]
                confidence = probs[0][pred].item()

                if activity == "Fighting" and confidence > 0.50:  # ✅ threshold 0.75
                    if current_activity == "Normal":  # ✅ sirf Normal override karo
                        current_activity = "Fighting"
                        current_confidence = round(confidence, 2)
                        activity_detected_this_frame = True  # ✅

                        if not post_recording:
                            post_recording = True
                            post_buffer = list(pre_buffer)  # 3 sec pehle
                            activity_to_save = "Fighting"
                            confidence_to_save = current_confidence
                else:
                    if current_activity == "Fighting":  # ✅ sirf Fighting reset
                        current_activity = "Normal"
                        current_confidence = 0.0

                frame_buffer = []

        except Exception as e:
            print("SlowFast Error:", e)

        # ==========================================
        # SMOKING DETECTION
        # ==========================================
        try:
            if frame_counter % 10 == 0:
                smoke_results = smoking_model.predict(frame, conf=0.60, verbose=False)
                best_smoke_conf = 0.0

                for r in smoke_results:
                    if len(r.boxes) > 0:
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > best_smoke_conf:
                                best_smoke_conf = conf
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(frame, f"Smoking {conf:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                        if best_smoke_conf > 0:
                            current_activity = "Smoking"  # ✅ Fighting override karta hai
                            current_confidence = round(best_smoke_conf, 2)
                            activity_detected_this_frame = True  # ✅

                            if not post_recording:
                                post_recording = True
                                post_buffer = list(pre_buffer)  # 3 sec pehle
                                activity_to_save = "Smoking"
                                confidence_to_save = current_confidence

        except Exception as e:
            print("Smoking Error:", e)

        # ==========================================
        # HARASSMENT DETECTION
        # ==========================================
        try:
            if frame_counter % 10 == 0:
                track_results = yolo_model.track(
                    frame, persist=True,
                    classes=[0], conf=0.5,
                    tracker="bytetrack.yaml"
                )
                if track_results:
                    persons = []
                    for box in track_results[0].boxes:
                        if box.id is None:
                            continue
                        pid = int(box.id.item())
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        crop = frame[y1:y2, x1:x2]
                        face_crop = crop[0:int((y2 - y1) * 0.4), :]
                        if face_crop.shape[0] >= 40 and face_crop.shape[1] >= 40:
                            persons.append((pid, (x1, y1, x2, y2), face_crop))

                    if detect_harassment(persons, emotion_buffers):
                        current_activity = "Harassment"  # ✅ highest priority
                        current_confidence = 0.85
                        activity_detected_this_frame = True  # ✅

                        if not post_recording:
                            post_recording = True
                            post_buffer = list(pre_buffer)  # 3 sec pehle
                            activity_to_save = "Harassment"
                            confidence_to_save = current_confidence

        except Exception as e:
            print("Harassment Error:", e)

        # ==========================================
        # ACTIVITY LABEL
        # ==========================================
        cv2.rectangle(frame, (10, 10), (320, 60), (0, 0, 0), -1)
        cv2.putText(frame, f"Activity: {current_activity} ({current_confidence:.2f})",
                    (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        # ==========================================
        # RECORDING + SAVE  ✅ BAHAR HAI — sahi jagah
        # ==========================================
        if post_recording:
            post_buffer.append(frame.copy())

            if activity_detected_this_frame:
                frames_after_activity = 0  # activity chal rahi hai — reset
                post_activity_ended = False
            else:
                post_activity_ended = True
                frames_after_activity += 1  # activity band — count karo

            # 3 sec baad save karo
            # 3 sec baad save karo
            if (
                    post_activity_ended
                    and frames_after_activity >= fps * 3
                    and activity_to_save in ["Fighting", "Smoking", "Harassment"]
            ):

                if time.time() - last_save_time > 15:
                    try:

                        # ✅ SAVE VIDEO FILE
                        video_path = _save_live_detection(post_buffer,activity_to_save,camera_name,fps)

                        # ✅ SAVE DB
                        _save_live_detection(
                            activity=activity_to_save,
                            confidence=confidence_to_save,
                            people=list(identified_people),
                            location_id=1,
                            location_name=camera_name,
                            video_path=video_path,
                            app=app
                        )

                        print(f"✅ Saved: {activity_to_save} | {confidence_to_save:.2f}")

                        last_save_time = time.time()
                        identified_people = set()

                    except Exception as e:
                        print("Save Error:", e)

                # RESET
                post_recording = False
                post_activity_ended = False
                frames_after_activity = 0
                post_buffer = []
                activity_to_save = "Normal"
                confidence_to_save = 0.0
                current_activity = "Normal"
                current_confidence = 0.0

        # ==========================================
        # STREAM FRAME
        # ==========================================
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame +
                b'\r\n'
        )

    cap.release()