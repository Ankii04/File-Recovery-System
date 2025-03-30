from flask import Blueprint, request, jsonify, send_file
import os
from datetime import datetime

file_routes = Blueprint("file_routes", __name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 🟢 Upload a file
@file_routes.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return jsonify({"message": f"{file.filename} uploaded successfully"}), 201

# 🟢 Create a new file
@file_routes.route('/create-file', methods=['POST'])
def create_file():
    data = request.json
    filename = data.get("filename", "").strip()
    content = data.get("content", "")

    if not filename:
        return jsonify({"error": "Filename is required"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if os.path.exists(file_path):
        return jsonify({"error": "File already exists"}), 409

    with open(file_path, "w") as f:
        f.write(content)

    return jsonify({"message": f"File '{filename}' created successfully"}), 201

# 🟢 List all files with metadata, search, and sorting
@file_routes.route('/files', methods=['GET'])
def list_files():
    search_query = request.args.get('search', '').lower()
    sort_by = request.args.get('sort_by', 'name')  # Default sorting by name
    files = []

    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            file_info = {
                "name": filename,
                "size": os.path.getsize(filepath),
                "type": filename.split('.')[-1] if '.' in filename else "Unknown",
                "date_modified": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            }
            files.append(file_info)

    # Search Filter
    if search_query:
        files = [file for file in files if search_query in file['name'].lower()]

    # Sorting Mechanism
    if sort_by == 'size':
        files.sort(key=lambda x: x['size'])
    elif sort_by == 'date_modified':
        files.sort(key=lambda x: datetime.strptime(x['date_modified'], '%Y-%m-%d %H:%M:%S'), reverse=True)
    else:  # Default sort by name
        files.sort(key=lambda x: x['name'].lower())

    return jsonify(files)

# 🟢 Delete a file
@file_routes.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": f"{filename} deleted successfully"}), 200
    return jsonify({"error": "File not found"}), 404

# 🟢 Rename a file
@file_routes.route('/rename', methods=['PUT'])
def rename_file():
    data = request.json
    old_name = data.get("old_name")
    new_name = data.get("new_name")

    if not old_name or not new_name:
        return jsonify({"error": "Both old and new file names are required"}), 400

    old_path = os.path.join(UPLOAD_FOLDER, old_name)
    new_path = os.path.join(UPLOAD_FOLDER, new_name)

    if not os.path.exists(old_path):
        return jsonify({"error": "File not found"}), 404

    if os.path.exists(new_path):
        return jsonify({"error": "A file with the new name already exists"}), 409

    os.rename(old_path, new_path)
    return jsonify({"message": f"File renamed from {old_name} to {new_name}"}), 200

# 🟢 Download a file
@file_routes.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404
