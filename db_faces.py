import os
import base64
from datetime import datetime

BASE_DIR = os.path.join(os.getcwd(), "face_db")

def save_user_image(regno, base64_img):

    # user folder
    folder_path = os.path.join(BASE_DIR, regno)
    os.makedirs(folder_path, exist_ok=True)

    # unique filename
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    file_path = os.path.join(folder_path, filename)

    # decode base64
    img_data = base64.b64decode(base64_img)

    with open(file_path, "wb") as f:
        f.write(img_data)

    return file_path
#2
from Vigilant_eye.Model.StudentImage import StudentImage
from Vigilant_eye.db import db
class StudentImage:
    def save_student_image(regno, base64_img):

        # 1. image folder me save karo
        path = save_user_image(regno, base64_img)

        # 2. DB me path save karo
        new_img = StudentImage(
            regno=regno,
            image_path=path
        )

        db.session.add(new_img)
        db.session.commit()

        return path
