# import cv2
# import torch
# import argparse
# import os
# import time
# from pathlib import Path
# from ultralytics import YOLO
#
# # ============================================================
# # CONFIGURATION
# # ============================================================
# MODEL_PATH   = 'smoking_yolov8s_best.pt'   # apna downloaded model yahan rakho
# CONF_THRESH  = 0.25                 # confidence threshold (0.0 - 1.0)
# IOU_THRESH   = 0.45                 # NMS IoU threshold
# IMG_SIZE     = 640                  # input size
# SAVE_OUTPUT  = True                 # output save karo ya nahi
#
# # Colors (BGR format)
# BOX_COLOR    = (0, 255, 0)          # green box
# TEXT_COLOR   = (0, 0, 255)          # red text
# ALERT_COLOR  = (0, 0, 255)          # red alert
#
#
# # ============================================================
# # MODEL LOAD
# # ============================================================
# def load_model(model_path):
#     if not os.path.exists(model_path):
#         print(f"❌ Model nahi mila: {model_path}")
#         print("   Model file is script ke saath same folder mein rakho!")
#         exit(1)
#
#     print(f"✅ Model load ho raha hai: {model_path}")
#     model = YOLO(model_path)
#     device = 'cuda' if torch.cuda.is_available() else 'cpu'
#     print(f"✅ Device: {device.upper()}")
#     print(f"✅ Classes: {model.names}")
#     return model, device
#
#
# # ============================================================
# # IMAGE TEST
# # ============================================================
# def test_image(model, img_path, save=True):
#     if not os.path.exists(img_path):
#         print(f"❌ Image nahi mili: {img_path}")
#         return
#
#     print(f"\n📸 Image process ho rahi hai: {img_path}")
#
#     # Predict
#     results = model.predict(
#         source    = img_path,
#         conf      = CONF_THRESH,
#         iou       = IOU_THRESH,
#         imgsz     = IMG_SIZE,
#         verbose   = False
#     )[0]
#
#     # Image load karo drawing ke liye
#     img = cv2.imread(img_path)
#     h, w = img.shape[:2]
#
#     # Detections
#     detections = results.boxes
#     total = len(detections)
#
#     print(f"🔍 Total detections: {total}")
#
#     if total == 0:
#         print("✅ Koi smoking detect nahi hua!")
#         label = "NO SMOKING DETECTED"
#         cv2.putText(img, label, (20, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.2, BOX_COLOR, 3)
#     else:
#         print(f"🚨 SMOKING DETECTED — {total} instance(s)!")
#
#         for i, box in enumerate(detections):
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             conf  = float(box.conf[0])
#             cls   = int(box.cls[0])
#             label = f"{model.names[cls]}: {conf:.2f}"
#
#             # Box draw karo
#             cv2.rectangle(img, (x1, y1), (x2, y2), ALERT_COLOR, 3)
#
#             # Label background
#             (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
#             cv2.rectangle(img, (x1, y1 - th - 10), (x1 + tw + 10, y1), ALERT_COLOR, -1)
#             cv2.putText(img, label, (x1 + 5, y1 - 5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
#
#             print(f"   [{i+1}] {model.names[cls]} | Confidence: {conf:.2f} | Box: ({x1},{y1}) -> ({x2},{y2})")
#
#         # Alert banner
#         banner = f"⚠ SMOKING DETECTED: {total} person(s)"
#         cv2.rectangle(img, (0, 0), (w, 60), ALERT_COLOR, -1)
#         cv2.putText(img, banner, (10, 42),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
#
#     # Save output
#     if save:
#         out_dir = 'output'
#         os.makedirs(out_dir, exist_ok=True)
#         out_path = os.path.join(out_dir, 'result_' + os.path.basename(img_path))
#         cv2.imwrite(out_path, img)
#         print(f"💾 Result saved: {out_path}")
#
#     # Show image
#     cv2.imshow('Smoking Detection Result', img)
#     print("   (Koi bhi key dabao band karne ke liye)")
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#
# # ============================================================
# # VIDEO TEST
# # ============================================================
# def test_video(model, video_path, save=True):
#     if not os.path.exists(video_path):
#         print(f"❌ Video nahi mili: {video_path}")
#         return
#
#     print(f"\n🎥 Video process ho rahi hai: {video_path}")
#
#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         print("❌ Video open nahi ho sakha!")
#         return
#
#     # Video properties
#     fps    = int(cap.get(cv2.CAP_PROP_FPS))
#     width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#
#     print(f"📊 FPS: {fps} | Size: {width}x{height} | Total Frames: {total_frames}")
#
#     # Output video writer
#     writer = None
#     if save:
#         out_dir = 'output'
#         os.makedirs(out_dir, exist_ok=True)
#         out_path = os.path.join(out_dir, 'result_' + os.path.basename(video_path))
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
#         print(f"💾 Output save hoga: {out_path}")
#
#     frame_num  = 0
#     smoke_frames = 0
#     start_time = time.time()
#
#     print("\n▶ Processing... (Q dabao band karne ke liye)\n")
#
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#
#         frame_num += 1
#
#         # Predict
#         results = model.predict(
#             source  = frame,
#             conf    = CONF_THRESH,
#             iou     = IOU_THRESH,
#             imgsz   = IMG_SIZE,
#             verbose = False
#         )[0]
#
#         detections = results.boxes
#         detected   = len(detections) > 0
#
#         if detected:
#             smoke_frames += 1
#
#         # Draw detections
#         for box in detections:
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             conf  = float(box.conf[0])
#             cls   = int(box.cls[0])
#             label = f"{model.names[cls]}: {conf:.2f}"
#
#             cv2.rectangle(frame, (x1, y1), (x2, y2), ALERT_COLOR, 3)
#             (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
#             cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 10, y1), ALERT_COLOR, -1)
#             cv2.putText(frame, label, (x1 + 5, y1 - 5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#
#         # Status banner
#         elapsed  = time.time() - start_time
#         curr_fps = frame_num / elapsed if elapsed > 0 else 0
#
#         if detected:
#             status = f"🚨 SMOKING DETECTED | {len(detections)} person(s)"
#             cv2.rectangle(frame, (0, 0), (width, 55), ALERT_COLOR, -1)
#         else:
#             status = "✅ No Smoking"
#             cv2.rectangle(frame, (0, 0), (width, 55), (0, 180, 0), -1)
#
#         cv2.putText(frame, status, (10, 38),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
#
#         # Frame info (bottom)
#         info = f"Frame: {frame_num}/{total_frames} | FPS: {curr_fps:.1f}"
#         cv2.putText(frame, info, (10, height - 15),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
#
#         # Progress print
#         if frame_num % 30 == 0:
#             pct = (frame_num / total_frames) * 100
#             print(f"   Progress: {pct:.1f}% | Frame {frame_num}/{total_frames} | "
#                   f"Smoke frames: {smoke_frames} | FPS: {curr_fps:.1f}")
#
#         if writer:
#             writer.write(frame)
#
#         cv2.imshow('Smoking Detection', frame)
#
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             print("\n⏹ User ne band kiya")
#             break
#
#     cap.release()
#     if writer:
#         writer.release()
#     cv2.destroyAllWindows()
#
#     # Summary
#     print("\n" + "="*50)
#     print("📊 VIDEO SUMMARY")
#     print("="*50)
#     print(f"Total Frames    : {frame_num}")
#     print(f"Smoking Frames  : {smoke_frames}")
#     smoke_pct = (smoke_frames / frame_num * 100) if frame_num > 0 else 0
#     print(f"Smoking %       : {smoke_pct:.1f}%")
#     print(f"Total Time      : {time.time()-start_time:.1f}s")
#     if save:
#         print(f"Output Video    : {out_path}")
#
#
# # ============================================================
# # WEBCAM TEST (BONUS)
# # ============================================================
# def test_webcam(model, cam_id=0):
#     print(f"\n📷 Webcam start ho rahi hai (Camera ID: {cam_id})")
#     print("   Q dabao band karne ke liye\n")
#
#     cap = cv2.VideoCapture(cam_id)
#     if not cap.isOpened():
#         print("❌ Webcam open nahi ho sakha!")
#         return
#
#     width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#
#         results = model.predict(
#             source  = frame,
#             conf    = CONF_THRESH,
#             imgsz   = IMG_SIZE,
#             verbose = False
#         )[0]
#
#         detections = results.boxes
#
#         for box in detections:
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             conf  = float(box.conf[0])
#             cls   = int(box.cls[0])
#             label = f"{model.names[cls]}: {conf:.2f}"
#
#             cv2.rectangle(frame, (x1, y1), (x2, y2), ALERT_COLOR, 3)
#             cv2.putText(frame, label, (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, ALERT_COLOR, 2)
#
#         status = "🚨 SMOKING!" if len(detections) > 0 else "✅ Clear"
#         color  = ALERT_COLOR if len(detections) > 0 else (0, 200, 0)
#         cv2.rectangle(frame, (0, 0), (width, 55), color, -1)
#         cv2.putText(frame, status, (10, 38),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
#
#         cv2.imshow('Smoking Detection - Live', frame)
#
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#
#     cap.release()
#     cv2.destroyAllWindows()
#
#
# # ============================================================
# # MAIN
# # ============================================================
# def main():
#     parser = argparse.ArgumentParser(description='Smoking Detection Test')
#     parser.add_argument('--input',  type=str, required=True,
#                         help='Image/video path, ya "webcam" live ke liye')
#     parser.add_argument('--model',  type=str, default=MODEL_PATH,
#                         help='Model path (default: smoking_best.pt)')
#     parser.add_argument('--conf',   type=float, default=CONF_THRESH,
#                         help='Confidence threshold (default: 0.25)')
#     parser.add_argument('--nosave', action='store_true',
#                         help='Output save mat karo')
#     args = parser.parse_args()
#
#     # Config update
#     global CONF_THRESH
#     CONF_THRESH = args.conf
#
#     # Model load
#     model, device = load_model(args.model)
#
#     # Input type check
#     inp = args.input.lower()
#
#     if inp == 'webcam':
#         test_webcam(model)
#
#     elif inp.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
#         test_image(model, args.input, save=not args.nosave)
#
#     elif inp.endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
#         test_video(model, args.input, save=not args.nosave)
#
#     else:
#         # Extension se pata nahi — file check karo
#         if os.path.isfile(args.input):
#             ext = Path(args.input).suffix.lower()
#             img_exts   = ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff']
#             video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
#
#             if ext in img_exts:
#                 test_image(model, args.input, save=not args.nosave)
#             elif ext in video_exts:
#                 test_video(model, args.input, save=not args.nosave)
#             else:
#                 print(f"❌ Unknown file type: {ext}")
#         else:
#             print(f"❌ File nahi mili: {args.input}")
#
#
# if __name__ == '__main__':
#     main()


# from ultralytics import YOLO
# import cv2
#
# model = YOLO('smoking_yolov8s_best.pt')
#
# # ============================================================
# # YAHAN PATH CHANGE KARO
# # ============================================================
# INPUT = 'frnd/smoke/111.jpg'  # image ya video path
# # ============================================================
#
# results = model.predict(INPUT, conf=0.25, show=True, save=True)
# print("Done! Output 'runs/detect' folder mein save hua.")


# from ultralytics import YOLO
# import cv2
#
# model = YOLO('smoking_yolov8s_best.pt')
#
# # YAHAN PATH CHANGE KARO
# INPUT = r'frnd/WhatsApp Video 2026-04-25 at 2.40.06 PM.mp4'
#
# # Predict
# results = model.predict(INPUT, conf=0.25)
#
# # Screen pe show karo
# img = results[0].plot()  # boxes draw ho jayengi automatically
# cv2.imshow('Smoking Detection', img)
# cv2.waitKey(0)  # koi bhi key dabao band karne ke liye
# cv2.destroyAllWindows()
#
# from ultralytics import YOLO
# import cv2
#
# model = YOLO('smoking_yolov8s_best.pt')
#
# # YAHAN APNA VIDEO PATH LIKHO
# INPUT = r'frnd/WhatsApp Video 2026-04-25 at 2.40.06 PM.mp4'
#
# cap = cv2.VideoCapture(INPUT)
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     results = model.predict(frame, conf=0.25, verbose=False)
#     annotated = results[0].plot()
#
#     cv2.imshow('Smoking Detection', annotated)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# cv2.destroyAllWindows()




# from ultralytics import YOLO
# import cv2
#
# model = YOLO('smoking_yolov8m_best_1.pt')
#
# # APNA VIDEO PATH YAHAN LIKHO
# VIDEO_PATH = r'frnd/1111.mp4'
#
# cap = cv2.VideoCapture(VIDEO_PATH)
#
# total_frames    = 0
# detected_frames = 0
# all_confidences = []
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     total_frames += 1
#     results    = model.predict(frame, conf=0.25, verbose=False)
#     detections = results[0].boxes
#
#     if len(detections) > 0:
#         detected_frames += 1
#         for box in detections:
#             conf = float(box.conf[0])
#             all_confidences.append(conf)
#
#     # Screen pe dikhao
#     annotated = results[0].plot()
#     cv2.imshow('Smoking Detection', annotated)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# cv2.destroyAllWindows()
#
# # ============================================================
# # OVERALL SUMMARY
# # ============================================================
# print("\n" + "="*45)
# print("        OVERALL CONFIDENCE SUMMARY")
# print("="*45)
# print(f"Total Frames        : {total_frames}")
# print(f"Smoking Frames      : {detected_frames}")
# print(f"Clean Frames        : {total_frames - detected_frames}")
# print(f"Smoking %           : {detected_frames/total_frames*100:.1f}%")
#
# if all_confidences:
#     avg = sum(all_confidences) / len(all_confidences)
#     print(f"\nAvg Confidence      : {avg*100:.1f}%")
#     print(f"Highest Confidence  : {max(all_confidences)*100:.1f}%")
#     print(f"Lowest Confidence   : {min(all_confidences)*100:.1f}%")
#     print(f"Total Detections    : {len(all_confidences)}")
#
#     # Verdict
#     print("\n" + "="*45)
#     if avg >= 0.70:
#         print("✅ VERDICT: HIGH CONFIDENCE — Smoking detected!")
#     elif avg >= 0.50:
#         print("⚠️  VERDICT: MEDIUM CONFIDENCE — Likely smoking")
#     else:
#         print("❓ VERDICT: LOW CONFIDENCE — Uncertain")
# else:
#     print("\n✅ VERDICT: No smoking detected in video!")
#
# print("="*45)



# ============================================================
#   YOLOv8 SMOKING DETECTION - PYCHARM VIDEO TEST
# ============================================================

from ultralytics import YOLO
import cv2

# ============================================================
# LOAD TRAINED MODEL
# ============================================================

MODEL_PATH = "smoking_best11.pt"

model = YOLO(MODEL_PATH)

print("Model Loaded Successfully!")

# ============================================================
# VIDEO PATH
# ============================================================

VIDEO_PATH = "frnd/smoke/smoking28.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)

# ============================================================
# VIDEO INFO
# ============================================================

width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = int(cap.get(cv2.CAP_PROP_FPS))

# ============================================================
# SAVE OUTPUT VIDEO
# ============================================================

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

out = cv2.VideoWriter(
    'output_smoking.mp4',
    fourcc,
    fps,
    (width, height)
)

# ============================================================
# PROCESS VIDEO
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # ========================================================
    # PREDICTION
    # ========================================================

    results = model.predict(

        source=frame,

        conf=0.70,
        iou=0.50,

        verbose=False
    )

    # ========================================================
    # DRAW RESULTS
    # ========================================================

    annotated_frame = results[0].plot()

    # ========================================================
    # SHOW FRAME
    # ========================================================

    cv2.imshow("Smoking Detection", annotated_frame)

    # ========================================================
    # SAVE FRAME
    # ========================================================

    out.write(annotated_frame)

    # ========================================================
    # EXIT KEY
    # ========================================================

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ============================================================
# RELEASE
# ============================================================

cap.release()
out.release()

cv2.destroyAllWindows()

print("\nVideo Processing Complete!")
print("Saved as: output_smoking.mp4")