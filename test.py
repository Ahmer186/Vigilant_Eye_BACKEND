# import cv2
# import numpy as np
# from ultralytics import YOLO
#
# # Load YOLOv8 model
# model = YOLO("yolov8n.pt")  # better accuracy than nano
#
# # Input video
# video_path = "frnd/fight_0001.webm"  # <-- apni video ka path yahan do
# cap = cv2.VideoCapture(video_path)
#
# prev_centers = []
#
# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     results = model(frame)
#
#     persons = []
#     current_centers = []
#
#     # Detect persons only
#     for r in results:
#         boxes = r.boxes
#         for box in boxes:
#             cls = int(box.cls[0])
#
#             # Class 0 = person (COCO dataset)
#             if cls == 0:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 cx = int((x1 + x2) / 2)
#                 cy = int((y1 + y2) / 2)
#
#                 persons.append((x1, y1, x2, y2))
#                 current_centers.append((cx, cy))
#
#                 # Draw box
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#
#     fight_detected = False
#
#     # Check distance between persons
#     if len(current_centers) >= 2:
#         for i in range(len(current_centers)):
#             for j in range(i + 1, len(current_centers)):
#                 dist = np.linalg.norm(
#                     np.array(current_centers[i]) - np.array(current_centers[j])
#                 )
#
#                 # Agar log close hain
#                 if dist < 100:
#                     fight_detected = True
#
#     # Motion detection (optional improvement)
#     if len(prev_centers) == len(current_centers):
#         for p, c in zip(prev_centers, current_centers):
#             movement = np.linalg.norm(np.array(p) - np.array(c))
#             if movement > 20:
#                 fight_detected = True
#
#     prev_centers = current_centers
#
#     # Show result
#     if fight_detected:
#         cv2.putText(frame, "FIGHT DETECTED!", (50, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
#
#     cv2.imshow("Fight Detection", frame)
#
#     if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
#         break
#
# cap.release()
# cv2.destroyAllWindows()


# from deepface import DeepFace
# import os
# from PIL import Image
#
# DB_PATH = "faces"
# TEST_IMAGE = "frnd/1.jpg"
#
# VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")
#
# def is_valid_image(img_path):
#     try:
#         img = Image.open(img_path)
#         img.verify()  # check corruption
#         return True
#     except:
#         return False
#
#
# def check_person_arcface():
#     if not os.path.exists(TEST_IMAGE):
#         print("❌ Test image not found")
#         return
#
#     found = False
#
#     for person_folder in os.listdir(DB_PATH):
#         person_path = os.path.join(DB_PATH, person_folder)
#
#         if not os.path.isdir(person_path):
#             continue
#
#         for file in os.listdir(person_path):
#             if not file.lower().endswith(VALID_EXTENSIONS):
#                 continue
#
#             img_path = os.path.join(person_path, file)
#
#             # ✅ skip corrupt images
#             if not is_valid_image(img_path):
#                 print("⚠️ Skipping corrupt image:", img_path)
#                 continue
#
#             try:
#                 result = DeepFace.verify(
#                     img1_path=TEST_IMAGE,
#                     img2_path=img_path,
#                     model_name="ArcFace",   # 🔥 best model
#                     enforce_detection=False
#                 )
#
#                 if result["verified"]:
#                     print(f"✅ MATCH FOUND: {person_folder}")
#                     print("📸 Image:", file)
#                     print("📏 Distance:", result["distance"])
#                     found = True
#                     return
#
#             except Exception as e:
#                 print("⚠️ Error processing:", img_path)
#                 continue
#
#     if not found:
#         print("❌ NO MATCH FOUND")
#
#
# check_person_arcface()

import cv2
import numpy as np
import face_recognition
import os
from PIL import Image  # ← Yeh add karo

root_path = 'faces'
encodeListKnown = []
classNames = []

print("Scanning subfolders and encoding faces...")

for subdir, dirs, files in os.walk(root_path):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            student_name = os.path.basename(subdir)
            img_path = os.path.join(subdir, file)

            try:
                # ✅ Pillow se load karo (OpenCV ki jagah)
                pil_img = Image.open(img_path)

                # ✅ Har format ko RGB mein convert karo (CMYK, RGBA, L sab fix)
                pil_img = pil_img.convert('RGB')

                # ✅ Numpy array banao
                img_rgb = np.array(pil_img, dtype=np.uint8)
                img_rgb = np.ascontiguousarray(img_rgb)

                encodings = face_recognition.face_encodings(img_rgb)
                if len(encodings) > 0:
                    encodeListKnown.append(encodings[0])
                    classNames.append(student_name)
                    print(f"Encoded: {student_name} ({file})")
                else:
                    print(f"No face found: {img_path}")

            except Exception as e:
                print(f"Error: {img_path} → {e}")
                continue

print(f"Total Encodings Loaded: {len(encodeListKnown)}")
print("Starting Webcam...")

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    imgS = np.ascontiguousarray(imgS.astype('uint8'))  # ✅ Webcam fix

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        if len(faceDis) > 0:
            matchIndex = np.argmin(faceDis)
            if faceDis[matchIndex] < 0.6:
                name = classNames[matchIndex].upper()
                color = (0, 255, 0)
            else:
                name = "UNKNOWN"
                color = (0, 0, 255)
        else:
            name = "NO DATA"
            color = (0, 0, 255)

        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
        cv2.putText(img, name, (x1 + 6, y2 - 6),
                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow('Student ID System', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

#
# import face_recognition
# import numpy as np
# import os
# import pickle
# from PIL import Image
#
# FACE_DB_PATH = 'faces'
# PICKLE_FILE = 'face_embeddings.pkl'
#
# db = {}
#
# print("Building face DB...")
#
# for person in os.listdir(FACE_DB_PATH):
#     person_path = os.path.join(FACE_DB_PATH, person)
#     if not os.path.isdir(person_path):
#         continue
#
#     db[person] = []
#
#     for img_file in os.listdir(person_path):
#         img_path = os.path.join(person_path, img_file)
#         try:
#             pil_img = Image.open(img_path).convert('RGB')
#             img_rgb = np.array(pil_img, dtype=np.uint8)
#             img_rgb = np.ascontiguousarray(img_rgb)
#
#             encodings = face_recognition.face_encodings(img_rgb)
#             if len(encodings) > 0:
#                 db[person].append(encodings[0])
#                 print(f"  ✅ {person} ({img_file})")
#             else:
#                 print(f"  ⚠️ No face: {img_file}")
#         except Exception as e:
#             print(f"  ❌ {img_file} → {e}")
#
# with open(PICKLE_FILE, 'wb') as f:
#     pickle.dump(db, f)
#
# total = sum(len(v) for v in db.values())
# print(f"\n✅ Done! Total encodings: {total}")
# print(f"✅ Saved: {PICKLE_FILE}")