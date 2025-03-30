from flask import Flask, render_template, request, jsonify, send_file
import os
import shutil
from datetime import datetime
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
TRASH_FOLDER = "trash"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRASH_FOLDER"] = TRASH_FOLDER

logging.basicConfig(level=logging.DEBUG)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    
    try:
        file.save(filepath)
        logging.info(f"File {file.filename} uploaded successfully.")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        return jsonify({"error": "Failed to upload file"}), 500
    
    return jsonify({"message": f"{file.filename} uploaded successfully"}), 201

@app.route('/files', methods=['GET'])
def list_files():
    search_query = request.args.get('search', '').lower()
    sort_by = request.args.get('sort_by', 'name')

    try:
        files = [
            {
                "name": filename,
                "size": os.path.getsize(os.path.join(UPLOAD_FOLDER, filename)),
                "type": filename.split('.')[-1] if '.' in filename else "Unknown",
                "date_modified": datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_FOLDER, filename))).strftime('%Y-%m-%d %H:%M:%S')
            }
            for filename in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename))
        ]
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        return jsonify({"error": "Failed to list files"}), 500

    if search_query:
        files = [file for file in files if search_query in file['name'].lower()]

    try:
        if sort_by == 'size':
            files.sort(key=lambda x: x['size'])
        elif sort_by == 'date_modified':
            files.sort(key=lambda x: datetime.strptime(x['date_modified'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        else:
            files.sort(key=lambda x: x['name'].lower())
    except Exception as e:
        logging.error(f"Sorting error: {e}")

    return jsonify(files)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    src_path = os.path.join(UPLOAD_FOLDER, filename)
    dest_path = os.path.join(TRASH_FOLDER, filename)

    if os.path.exists(src_path):
        try:
            shutil.move(src_path, dest_path)
            logging.info(f"File {filename} moved to trash.")
        except Exception as e:
            logging.error(f"Error moving file to trash: {e}")
            return jsonify({"error": "Failed to move file to trash"}), 500
        return jsonify({"message": f"{filename} moved to trash.", "status": "deleted"}), 200
    return jsonify({"error": "File not found"}), 404

@app.route('/restore/<filename>', methods=['PUT'])
def restore_file(filename):
    src_path = os.path.join(TRASH_FOLDER, filename)
    dest_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(src_path):
        try:
            shutil.move(src_path, dest_path)
            logging.info(f"File {filename} restored.")
        except Exception as e:
            logging.error(f"Error restoring file: {e}")
            return jsonify({"error": "Failed to restore file"}), 500
        return jsonify({"message": f"{filename} restored successfully.", "status": "restored"}), 200
    return jsonify({"error": "File not found in trash"}), 404

@app.route('/trash', methods=['GET'])
def list_trash():
    try:
        files = [
            {
                "name": filename,
                "size": os.path.getsize(os.path.join(TRASH_FOLDER, filename)),
                "date_deleted": datetime.fromtimestamp(os.path.getmtime(os.path.join(TRASH_FOLDER, filename))).strftime('%Y-%m-%d %H:%M:%S')
            }
            for filename in os.listdir(TRASH_FOLDER) if os.path.isfile(os.path.join(TRASH_FOLDER, filename))
        ]
    except Exception as e:
        logging.error(f"Error listing trash: {e}")
        return jsonify({"error": "Failed to list trash"}), 500
    return jsonify(files)

@app.route('/delete-permanent/<filename>', methods=['DELETE'])
def permanently_delete_file(filename):
    file_path = os.path.join(TRASH_FOLDER, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logging.info(f"File {filename} permanently deleted.")
        except Exception as e:
            logging.error(f"Error permanently deleting file: {e}")
            return jsonify({"error": "Failed to permanently delete file"}), 500
        return jsonify({"message": f"{filename} permanently deleted."}), 200
    return jsonify({"error": "File not found in trash"}), 404

@app.route('/rename', methods=['PUT'])
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

    try:
        os.rename(old_path, new_path)
        logging.info(f"File renamed from {old_name} to {new_name}.")
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        return jsonify({"error": "Failed to rename file"}), 500

    return jsonify({"message": f"File renamed from {old_name} to {new_name}"}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        try:
            return send_file(filepath, as_attachment=True)
        except Exception as e:
            logging.error(f"Error sending file: {e}")
            return jsonify({"error": "Failed to download file"}), 500
    return jsonify({"error": "File not found"}), 404

@app.route('/create-file', methods=['POST'])
def create_file():
    data = request.get_json()  # Get JSON data from the request
    filename = data.get('filename')
    content = data.get('content')

    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        with open(file_path, 'w') as f:
            f.write(content)  # Write content to the file
        logging.info(f"File {filename} created successfully.")
        return jsonify({"message": "File created successfully!"}), 201
    except Exception as e:
        logging.error(f"Error creating file: {e}")
        return jsonify({"error": "Error creating file"}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
