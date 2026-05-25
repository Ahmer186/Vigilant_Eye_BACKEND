import os
from Vigilant_eye.db import db
from Vigilant_eye.Model.StudentImage import StudentImage
class Student_Controller:
    def upload_student_image_controller(regno, image):

        # folder create
        folder_path = os.path.join("faces", regno)
        os.makedirs(folder_path, exist_ok=True)

        # filename
        filename = image.filename
        file_path = os.path.join(folder_path, filename)

        # save file
        image.save(file_path)

        # DB save
        new_img = StudentImage(
            regno=regno,
            image_path=file_path
        )

        db.session.add(new_img)
        db.session.commit()

        return file_path