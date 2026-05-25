from flask import Flask, request, jsonify
from flask_cors import CORS
from Vigilant_eye.db import app, db
from Vigilant_eye.Controller.Users import User_Controller
from Vigilant_eye.Controller.Penalties import penalty_Controller
from Vigilant_eye.Controller.Notification import Notification_Controller
from Vigilant_eye.Controller.Guard import Guard_Controller
from Vigilant_eye.Controller.Detection import Detection_Controller
from Vigilant_eye.Controller.Camera import Camera_Controller
from Vigilant_eye.Controller.Student import Student_Controller

from flask import request, jsonify, Response
from Vigilant_eye.model_processing import add_camera_service,get_cameras_service,generate_live_frames


CORS(app)
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# import torch
# print(torch.cuda.is_available())
# print(torch.cuda.get_device_name(0))
# ----------------- ROUTES -----------------
@app.route("/login", methods=["POST"])
def login_route():
    return User_Controller.login(request)
@app.route("/update_password", methods=["PUT"])
def update_password():
    return User_Controller.update_password()

@app.route('/penalties_by_user', methods=['POST'])
def penalty_route():
    return penalty_Controller.penalties_by_user()
@app.route('/notifications_by_user', methods=['POST'])
def notifications():
    return Notification_Controller.notifications_by_user()

@app.route('/show_ecl_record', methods=['GET'])
def show_ecl_record():
    return Detection_Controller.detections_without_penalty()


@app.route('/detections_without_penalty_cases/<int:user_id>', methods=['GET'])
def Penelty_detection_cases(user_id):
    return Detection_Controller.detections_without_penalty_cases(user_id)

@app.route('/camera_info', methods=['GET'])
def camera_basic_info():
    return Camera_Controller.all_camera()

@app.route('/update_camera_status', methods=['PUT'])
def update_camera_status():
    return Camera_Controller.update_camera_status()

@app.route('/add_camera', methods=['POST'])
def add_camera():
    return Camera_Controller.add_camera()

@app.route('/remove_camera', methods=['DELETE'])
def remove_camera():
    return Camera_Controller.remove_camera()

@app.route('/pending_penalties/<int:user_id>', methods=['GET'])
def pending_penalties(user_id):
    return penalty_Controller.show_all_pending_penalties(user_id)

@app.route('/update_pending_penalties/<int:user_id>', methods=['PUT'])
def update_pending_penalties(user_id):
    return penalty_Controller.update_pending_penalty(user_id)

@app.route('/resolve_penalty', methods=['PUT'])
def resolve_penalty():
    return penalty_Controller.resolve_penalty()

@app.route('/add_penalty', methods=['POST'])
def add_penalty():
    return penalty_Controller.add_penalty_to_detection()


@app.route('/create_admin', methods=['POST'])
def add_admin():
    return User_Controller.create_admin()

@app.route('/create_DC', methods=['POST'])
def add_DC():
    return User_Controller.add_committee_member()

@app.route('/create_DCommetty', methods=['POST'])
def add_DCommetty():
    return User_Controller.create_DC()

@app.route('/remove_DC', methods=['DELETE'])
def remove_DC():
    return User_Controller.remove_committee_member()

@app.route('/remove_DCommetty', methods=['DELETE'])
def remove_DCommetty():
    return User_Controller.remove_DC()


@app.route('/remove_admin', methods=['DELETE'])
def remove_admin():
    return User_Controller.remove_admin()


@app.route('/detect_video', methods=['POST'])
def detect_video():
    return Detection_Controller.detect_video()

@app.route('/detect_activity', methods=['POST'])
def detect_activity():
    return Detection_Controller.detect_activity()

@app.route('/upload_student_image', methods=['POST'])
def upload_student_image():

    regno = request.form['regno']
    image = request.files['image']

    file_path = Student_Controller.upload_student_image_controller(regno, image)

    return jsonify({
        "message": "Image uploaded successfully",
        "path": file_path
    })

from flask import send_from_directory

@app.route('/uploads/<filename>')
def serve_video(filename):
    return send_from_directory('uploads', filename)

@app.route('/remove_wrong_person', methods=['PUT'])
def remove_wrong_person():
    return Detection_Controller.remove_wrong_person()

@app.route('/add_person', methods=['POST'])
def add_person():
    return Detection_Controller.add_student_to_detection()


@app.route("/get_locations", methods=["GET"])
def get_location():
    return Camera_Controller.get_locations()

@app.route("/get_cameras", methods=["GET"])
def get_camera():
    return Camera_Controller.get_camera()


###############
app.add_url_rule('/start_stream', view_func=Detection_Controller.start_stream, methods=['POST'])
app.add_url_rule('/stop_stream', view_func=Detection_Controller.stop_stream, methods=['POST'])
##############
# =============================
# ADD CAMERA
# =============================
@app.route("/live_camera", methods=["POST"])
def live_camera():

    data = request.get_json()

    response, status = add_camera_service(data)

    return jsonify(response), status
# =============================
# LIVE STREAM
# =============================
@app.route("/video_feed/<camera_name>")
def video_feed(camera_name):

    return Response(
        generate_live_frames(camera_name,app),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
########################
@app.route('/student_activity/<aridno>', methods=['GET'])
def student_activity(aridno):
    return Detection_Controller.get_student_activity(aridno)

@app.route('/admin/dashboard_counts', methods=['GET'])
def admin_dashboard_counts():
    return User_Controller.get_admin_dashboard_counts()
#######################
if __name__ == "__main__":
    app.run(debug=True)

