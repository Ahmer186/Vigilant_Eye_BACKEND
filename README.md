# 🎥 Vigilant Eye - Backend

> AI-powered intelligent surveillance system backend built with Flask & Python

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-27338e?style=for-the-badge&logo=OpenCV&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)

---

## 📌 About The Project

**Vigilant Eye** is an AI-based surveillance system that uses Deep Learning and Computer Vision to monitor and detect suspicious activities in real-time. The backend handles all AI processing, database management, and REST API endpoints.

---

## ✨ Features

### 👁️ Face Recognition
- Real-time face detection and recognition
- Face embeddings stored using `face_embeddings.pkl`
- Automatic identification of registered students/members

### 🚬 Smoking Detection
- YOLOv8 based smoking detection model
- Real-time video analysis
- Instant alert generation on detection

### 🏃 Violence Detection
- SlowFast deep learning model for action recognition
- Detects violent behavior from CCTV footage
- High accuracy with fine-tuned model

### 🛡️ Guard Screen
- Live camera feed management
- Guard interface for real-time monitoring
- Instant alert notifications

### 🔔 Notifications
- Automatic alerts on suspicious activity detection
- Notification history stored in MySQL database
- Role-based notification system

### 👨‍💼 Admin Dashboard
- Complete system management via REST APIs
- User management (Add/Remove admins, DC members)
- Camera management
- Fine and penalty handling

---

## 🏗️ Project Structure
## ⚙️ Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/Ahmer186/Vigilant_Eye_BACKEND.git
cd Vigilant_Eye_BACKEND
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Setup MySQL Database**
```bash
# Create database in MySQL
CREATE DATABASE vigilant_eye;
```

**5. Run the server**
```bash
python Router.py
```

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User authentication |
| GET | `/notifications` | Get all notifications |
| POST | `/detect/smoking` | Smoking detection |
| POST | `/detect/violence` | Violence detection |
| POST | `/face/recognize` | Face recognition |
| GET | `/admin/members` | Get all members |
| POST | `/admin/add` | Add new member |
| DELETE | `/admin/remove` | Remove member |

---

## 🧠 AI Models Used

| Model | Purpose | Framework |
|-------|---------|-----------|
| YOLOv8 | Smoking Detection | Ultralytics |
| SlowFast R50 | Violence Detection | PyTorch |
| Face Recognition | Identity Verification | DeepFace/OpenCV |

---

## 🔗 Related Repository

👉 **Frontend:** [Vigilant_Eye_FRONTEND](https://github.com/Ahmer186/Vigilant_Eye_FRONTEND)

---

## 👨‍💻 Developer

**Ahmer Noor**
[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:ahmernoor555@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Ahmer186)
