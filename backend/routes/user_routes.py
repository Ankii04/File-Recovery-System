from flask import Blueprint, jsonify

user_blueprint = Blueprint('users', __name__)

@user_blueprint.route('/info', methods=['GET'])
def user_info():
    user = {"name": "John Doe", "role": "Admin"}
    return jsonify(user)
