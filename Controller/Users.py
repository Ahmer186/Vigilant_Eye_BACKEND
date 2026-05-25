from flask import request, jsonify
from Vigilant_eye.Model.Users import Users
from Vigilant_eye.Model.Admin import Admin
from Vigilant_eye.Model.DisciplineCommittee import DisciplineCommittee
from Vigilant_eye.Model.CommitteeMember import CommitteeMember
from Vigilant_eye.db import db
class User_Controller:
    @staticmethod
    def login(request):
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return jsonify({"message": "Please provide username and password"}), 400


            user = Users.query.filter_by(username=username).first()

            if not user:
                return jsonify({"message": "Username not found"}), 404

            # Compare password (plain text like your original code)
            if password != user.password:
                return jsonify({"message": "Incorrect password"}), 401

            return jsonify({
                "message": f"Welcome {user.role}, {user.username}",
                "user_id": user.id,
                "role": user.role
            }), 200

        except Exception as e:
            return jsonify({"message": str(e)}), 500

    @staticmethod
    def update_password():
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON body required"}), 400

        username = data.get("username")
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # Validate required fields
        if not username or not old_password or not new_password or not confirm_password:
            return jsonify({
                "error": "All fields (username, old_password, new_password, confirm_password) are required"
            }), 400

        try:
            # Find user by username
            user = Users.query.filter_by(username=username).first()

            if not user:
                return jsonify({"error": "Username not found"}), 404

            # Check old password
            if user.password != old_password:
                return jsonify({"error": "Old password is incorrect"}), 401

            # Check new password confirmation
            if new_password != confirm_password:
                return jsonify({"error": "New password and confirm password do not match"}), 400

            # Update password
            user.password = new_password
            db.session.commit()

            return jsonify({"message": "Password updated successfully!"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def create_admin():

        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON body required"}), 400

        name = data.get("name")
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        # Validate input
        if not all([name, username, password, email]):
            return jsonify({"error": "All fields (name, username, password, email) are required"}), 400

        try:
            # Check if username or email already exists
            existing_user = Users.query.filter(
                (Users.username == username) | (Users.email == email)
            ).first()

            if existing_user:
                return jsonify({"error": "Username or Email already exists"}), 400

            # Create new user
            new_user = Users(
                username=username,
                password=password,
                email=email,
                role="Admin",
                status="Active"
            )

            # Create admin and attach via relationship (clean ORM way)
            new_admin = Admin(
                name=name
            )

            # Link both tables using relationship
            new_user.admin_rship = new_admin

            # Add and commit
            db.session.add(new_user)
            db.session.commit()

            return jsonify({
                "message": " Admin created successfully",
                "user_id": new_user.id,
                "admin_id": new_admin.id
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def add_committee_member():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            name = data.get("name")
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            case_solving = data.get("case_solving")  # ✅ naya — "Fighting,Smoking,Harassment"

            if not all([name, username, password, email]):
                return jsonify({"error": "Provide name, username, password, email"}), 400

            if not case_solving:
                return jsonify({"error": "Please select at least one case solving activity"}), 400

            if Users.query.filter(
                    (Users.username == username) | (Users.email == email)
            ).first():
                return jsonify({"error": "Username or email already exists"}), 400

            new_user = Users(
                username=username,
                password=password,
                email=email,
                role="Committee",
                status="Active"
            )
            db.session.add(new_user)
            db.session.flush()

            new_committee = DisciplineCommittee(
                name=name,
                user_id=new_user.id,
                case_solving=case_solving  # ✅ save karo
            )
            db.session.add(new_committee)
            db.session.commit()

            return jsonify({
                "message": "Committee member added successfully",
                "name": name,
                "username": username,
                "email": email,
                "role": "Committee",
                "status": "Active",
                "case_solving": case_solving
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def remove_committee_member():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "JSON body required"}), 400

                username = data.get("username")
                password = data.get("password")

                if not username or not password:
                    return jsonify({"error": "Provide username and password"}), 400

                # Find user
                user = Users.query.filter_by(username=username, password=password).first()

                if not user:
                    return jsonify({"error": "Invalid username or password"}), 401

                # Ensure user is Committee
                if user.role != "Committee":
                    return jsonify({"error": "User is not a Committee member"}), 403

                # Find committee record
                committee = DisciplineCommittee.query.filter_by(user_id=user.id).first()

                if not committee:
                    return jsonify({"error": "Committee record not found"}), 404

                # Delete committee record first
                db.session.delete(committee)

                # Delete user record
                db.session.delete(user)

                db.session.commit()

                return jsonify({
                    "message": "Committee member removed successfully",
                    "username": username
                }), 200

            except Exception as e:
                db.session.rollback()
                return jsonify({"error": str(e)}), 500

    @staticmethod
    def remove_admin():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return jsonify({"error": "Provide username and password"}), 400

            # Find user
            user = Users.query.filter_by(username=username, password=password).first()

            if not user:
                return jsonify({"error": "Invalid username or password"}), 401

            # Check role
            if user.role != "Admin":
                return jsonify({"error": "User is not an Admin"}), 403

            # Find admin record
            admin = Admin.query.filter_by(user_id=user.id).first()

            if not admin:
                return jsonify({"error": "Admin record not found"}), 404

            # Delete admin record first
            db.session.delete(admin)

            # Delete user record
            db.session.delete(user)

            db.session.commit()

            return jsonify({
                "message": "Admin removed successfully",
                "username": username
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def get_admin_dashboard_counts():
        try:
            admin_count = Users.query.filter(Users.role == "Admin").count()

            dc_count = Users.query.filter(
                Users.role.in_(["Committee", "committee"])
            ).count()

            return jsonify({
                "admin_count": admin_count,
                "dc_count": dc_count
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def create_DC():
        data = request.get_json()

        # ✅ Step 1: User banao (simple password)
        new_user = Users(
            username=data['username'],
            password=data['password'],  # simple password
            email=data['email'],
            role='Committee',
            status='active'
        )
        db.session.add(new_user)
        db.session.flush()  # user.id mil jayega

        # ✅ Step 2: DisciplineCommittee mein save karo
        new_dc = DisciplineCommittee(
            name=data['name'],
            user_id=new_user.id,
            case_solving=data['case_solving']  # "Fighting,Smoking"
        )
        db.session.add(new_dc)
        db.session.flush()

        # ✅ Step 3: case_solving split karo aur CommitteeMember mein save karo
        activities = data['case_solving'].split(',')  # ["Fighting", "Smoking"]

        for activity in activities:
            member = CommitteeMember(
                committee_type=activity.strip().lower(),  # "fighting", "smoking"
                user_id=new_user.id,
                position=data.get('position', 'member')
            )
            db.session.add(member)

        db.session.commit()

        return jsonify({'message': 'DC Member added successfully!'}), 201
    @staticmethod
    def remove_DC():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return jsonify({"error": "Provide username and password"}), 400

            # Find user
            user = Users.query.filter_by(username=username, password=password).first()

            if not user:
                return jsonify({"error": "Invalid username or password"}), 401

            # Ensure user is dc_member
            if user.role != "Committee":
                return jsonify({"error": "User is not a Committee member"}), 403

            # ✅ Step 1: CommitteeMember table sy delete karo
            CommitteeMember.query.filter_by(user_id=user.id).delete()

            # ✅ Step 2: DisciplineCommittee table sy delete karo
            DisciplineCommittee.query.filter_by(user_id=user.id).delete()

            # ✅ Step 3: User table sy delete karo
            db.session.delete(user)

            db.session.commit()

            return jsonify({
                "message": "Committee member removed successfully",
                "username": username
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500