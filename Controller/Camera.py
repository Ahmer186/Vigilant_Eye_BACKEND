from flask import request, jsonify
from Vigilant_eye.Model.Camera import Camera
from Vigilant_eye.Model.CameraLinks import CameraLinks
from Vigilant_eye.Model.Location import Location
from datetime import datetime
from Vigilant_eye.db import db
class Camera_Controller:
    @staticmethod
    def all_camera():
        try:
            cameras = Camera.query.all()

            results = []

            for cam in cameras:
                location = Location.query.filter_by(
                    camera_id=cam.camera_id
                ).first()

                results.append({

                    "camera_id": cam.camera_id,

                    "camera_name": cam.camera_name,

                    "location": (
                        location.loc_name
                        if location else "Unknown"
                    ),

                    # ✅ CAMERA STATUS
                    "status": cam.status

                })

            return jsonify({
                "cameras": results
            }), 200

        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500
    @staticmethod
    def update_camera_status():
            try:
                data = request.get_json()

                if not data:
                    return jsonify({"error": "JSON body required"}), 400

                camera_name = data.get("camera_name")
                new_status = data.get("status")

                if not camera_name or not new_status:
                    return jsonify({
                        "error": "Provide 'camera_name' and 'status'"
                    }), 400

                new_status = new_status.lower()

                if new_status not in ["active", "inactive"]:
                    return jsonify({
                        "error": "Status must be 'active' or 'inactive'"
                    }), 400

                camera = Camera.query.filter_by(camera_name=camera_name).first()

                if not camera:
                    return jsonify({"message": "Camera not found"}), 404

                # ✅ Update status
                camera.status = new_status

                # ✅ Save current time whenever status changes
                camera.active_time = datetime.utcnow()

                db.session.commit()

                return jsonify({
                    "message": "Camera status updated successfully",
                    "camera_name": camera.camera_name,
                    "new_status": camera.status,
                    "updated_time": camera.active_time.strftime("%Y-%m-%d %H:%M:%S")
                }), 200

            except Exception as e:
                db.session.rollback()
                return jsonify({"error": str(e)}), 500

    @staticmethod
    def remove_camera():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            ip = data.get("ipAddress")  # <-- updated to match your column name

            if not ip:
                return jsonify({"error": "Provide ipAddress"}), 400

            # Find camera by ipAddress
            camera = Camera.query.filter_by(ipAddress=ip).first()

            if not camera:
                return jsonify({"error": "Camera not found"}), 404

            # Delete all links where this camera is involved
            CameraLinks.query.filter(
                (CameraLinks.camera_id == camera.camera_id) |
                (CameraLinks.linked_camera_id == camera.camera_id)
            ).delete(synchronize_session=False)

            # Delete camera
            db.session.delete(camera)

            db.session.commit()

            return jsonify({
                "message": "Camera removed successfully",
                "ipAddress": ip
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    @staticmethod

    def add_camera():
        try:
            data = request.get_json()

            # =========================================
            # GET DATA
            # =========================================
            camera_name = data.get("camera_name")
            ipAddress = data.get("ipAddress")
            direction = data.get("direction")

            # ✅ NEW LOCATION FIELD
            location_name = data.get("location_name")

            # =========================================
            # LINKED CAMERAS
            # =========================================
            raw_ids = data.get("linked_cameras", [])

            linked_ids = []

            for cid in raw_ids:
                try:
                    linked_ids.append(int(cid))
                except (ValueError, TypeError):
                    continue

            # =========================================
            # VALIDATION
            # =========================================
            if (
                    not camera_name or
                    not ipAddress or
                    not direction or
                    not location_name
            ):
                return jsonify({
                    "error": "camera_name, ipAddress, direction and location_name required"
                }), 400

            # =========================================
            # CREATE CAMERA
            # =========================================
            new_cam = Camera(
                camera_name=camera_name,
                ipAddress=ipAddress,
                direction=direction,
                status="active"
            )

            db.session.add(new_cam)

            # Generate camera_id
            db.session.flush()

            # =========================================
            # LINK LOCATION
            # =========================================
            location = Location.query.filter_by(
                loc_name=location_name
            ).first()

            if location:

                # Update location with camera_id
                location.camera_id = new_cam.camera_id

            else:

                return jsonify({
                    "error": "Location not found"
                }), 404

            # =========================================
            # VERIFY EXISTING CAMERAS
            # =========================================
            existing_cameras = db.session.query(
                Camera.camera_id
            ).filter(
                Camera.camera_id.in_(linked_ids)
            ).all()

            valid_ids = [cam[0] for cam in existing_cameras]

            # =========================================
            # BIDIRECTIONAL LINKING
            # =========================================
            for linked_id in valid_ids:
                # New -> Existing
                link1 = CameraLinks(
                    camera_id=new_cam.camera_id,
                    linked_camera_id=linked_id
                )

                # Existing -> New
                link2 = CameraLinks(
                    camera_id=linked_id,
                    linked_camera_id=new_cam.camera_id
                )

                db.session.add(link1)
                db.session.add(link2)

            # =========================================
            # COMMIT
            # =========================================
            db.session.commit()

            # =========================================
            # RESPONSE
            # =========================================
            return jsonify({

                "message": "Camera added successfully",

                "new_camera_id": new_cam.camera_id,

                "location": location_name,

                "linked_with": valid_ids

            }), 201

        except Exception as e:

            db.session.rollback()

            print("ERROR:", str(e))

            return jsonify({
                "error": str(e)
            }), 500


    @staticmethod
    def get_locations():
        try:

            # =====================================
            # GET ALL LOCATIONS FROM LOCATION TABLE
            # =====================================
            locations = Location.query.all()

            location_names = []

            for loc in locations:

                if loc.loc_name:
                    location_names.append(loc.loc_name)

            # =====================================
            # RETURN RESPONSE
            # =====================================
            return jsonify({
                "locations": location_names
            }), 200

        except Exception as e:

            print("ERROR:", str(e))

            return jsonify({
                "error": str(e)
            }), 500

    @staticmethod
    def get_camera():
        try:
            cameras = Camera.query.all()

            camera_list = []

            for cam in cameras:
                camera_list.append({
                    "camera_id": cam.camera_id,  # ya jo bhi PK field ho
                    "camera_name": cam.camera_name
                })

            return jsonify({
                "cameras": camera_list  # ✅ key bhi match, objects bhi
            }), 200

        except Exception as e:
            print("ERROR:", str(e))
            return jsonify({"error": str(e)}), 500