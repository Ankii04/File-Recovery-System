from flask import Flask, render_template, request, jsonify, send_file
import os
import shutil
from datetime import datetime
import logging
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage
from io import BytesIO

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

logging.basicConfig(level=logging.DEBUG)

USE_FIREBASE = False
try:
    # Check environment variable first (Vercel deployment)
    if os.environ.get('FIREBASE_CREDENTIALS'):
        import json
        cred_json = json.loads(os.environ['FIREBASE_CREDENTIALS'])
        cred = credentials.Certificate(cred_json)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'file-recovery-system-5d7e9.appspot.com'
        })
        USE_FIREBASE = True
        logging.info("Firebase initialized successfully from environment variable")
    
    # Fall back to local file (local development)
    elif os.path.exists('serviceAccountKey.json'):
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'file-recovery-system-5d7e9.appspot.com'
        })
        USE_FIREBASE = True
        logging.info("Firebase initialized successfully from local file")

    else:
        logging.warning("Firebase credentials not found, using local storage")

except Exception as e:
    logging.warning(f"Firebase initialization failed: {e}, using local storage")

if os.environ.get('VERCEL'):
    UPLOAD_FOLDER = "/tmp/uploads"
    TRASH_FOLDER = "/tmp/trash"
else:
    UPLOAD_FOLDER = "uploads"
    TRASH_FOLDER = "trash"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRASH_FOLDER"] = TRASH_FOLDER

# Only create directories if not using Firebase
if not USE_FIREBASE:
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(TRASH_FOLDER, exist_ok=True)
        logging.info(f"Created local storage directories: {UPLOAD_FOLDER}, {TRASH_FOLDER}")
    except OSError as e:
        # On Vercel without Firebase, this will fail - that's expected
        if os.environ.get('VERCEL'):
            logging.error(f"CRITICAL: Running on Vercel without Firebase credentials! Local storage will not work. Error: {e}")
            logging.error("Please add FIREBASE_CREDENTIALS environment variable in Vercel dashboard.")
        else:
            logging.error(f"Could not create local directories: {e}")



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blob = bucket.blob(f"uploads/{file.filename}")
            file.stream.seek(0)
            blob.upload_from_string(file.read(), content_type=file.content_type)
            logging.info(f"File {file.filename} uploaded to Firebase successfully.")
        else:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            logging.info(f"File {file.filename} uploaded locally successfully.")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        return jsonify({"error": "Failed to upload file"}), 500
    
    return jsonify({"message": f"{file.filename} uploaded successfully"}), 201

@app.route('/files', methods=['GET'])
def list_files():
    search_query = request.args.get('search', '').lower()
    sort_by = request.args.get('sort_by', 'name')

    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blobs = bucket.list_blobs(prefix='uploads/')
            files = [
                {
                    "name": blob.name.replace('uploads/', ''),
                    "size": blob.size,
                    "type": blob.name.split('.')[-1] if '.' in blob.name else "Unknown",
                    "date_modified": blob.updated.strftime('%Y-%m-%d %H:%M:%S') if blob.updated else "Unknown"
                }
                for blob in blobs if blob.name != 'uploads/'
            ]
        else:
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
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            src_blob = bucket.blob(f"uploads/{filename}")
            if src_blob.exists():
                dest_blob = bucket.blob(f"trash/{filename}")
                bucket.copy_blob(src_blob, bucket, f"trash/{filename}")
                src_blob.delete()
                logging.info(f"File {filename} moved to trash.")
                return jsonify({"message": f"{filename} moved to trash.", "status": "deleted"}), 200
            else:
                return jsonify({"error": "File not found"}), 404
        else:
            src_path = os.path.join(UPLOAD_FOLDER, filename)
            dest_path = os.path.join(TRASH_FOLDER, filename)
            if os.path.exists(src_path):
                shutil.move(src_path, dest_path)
                logging.info(f"File {filename} moved to trash.")
                return jsonify({"message": f"{filename} moved to trash.", "status": "deleted"}), 200
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logging.error(f"Error moving file to trash: {e}")
        return jsonify({"error": "Failed to move file to trash"}), 500

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

    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            old_blob = bucket.blob(f"uploads/{old_name}")
            if not old_blob.exists():
                return jsonify({"error": "File not found"}), 404
            
            new_blob = bucket.blob(f"uploads/{new_name}")
            if new_blob.exists():
                return jsonify({"error": "A file with the new name already exists"}), 409
            
            bucket.copy_blob(old_blob, bucket, f"uploads/{new_name}")
            old_blob.delete()
            logging.info(f"File renamed from {old_name} to {new_name}.")
        else:
            old_path = os.path.join(UPLOAD_FOLDER, old_name)
            new_path = os.path.join(UPLOAD_FOLDER, new_name)
            
            if not os.path.exists(old_path):
                return jsonify({"error": "File not found"}), 404
            
            if os.path.exists(new_path):
                return jsonify({"error": "A file with the new name already exists"}), 409
            
            os.rename(old_path, new_path)
            logging.info(f"File renamed from {old_name} to {new_name}.")
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        return jsonify({"error": "Failed to rename file"}), 500

    return jsonify({"message": f"File renamed from {old_name} to {new_name}"}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blob = bucket.blob(f"uploads/{filename}")
            if blob.exists():
                file_data = blob.download_as_bytes()
                return send_file(
                    BytesIO(file_data),
                    as_attachment=True,
                    download_name=filename
                )
            else:
                return jsonify({"error": "File not found"}), 404
        else:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
    
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blob = bucket.blob(f"uploads/{file.filename}")
            file.stream.seek(0)
            blob.upload_from_string(file.read(), content_type=file.content_type)
            logging.info(f"File {file.filename} uploaded to Firebase successfully.")
        else:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            logging.info(f"File {file.filename} uploaded locally successfully.")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        return jsonify({"error": "Failed to upload file"}), 500
    
    return jsonify({"message": f"{file.filename} uploaded successfully"}), 201

@app.route('/files', methods=['GET'])
def list_files():
    search_query = request.args.get('search', '').lower()
    sort_by = request.args.get('sort_by', 'name')

    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blobs = bucket.list_blobs(prefix='uploads/')
            files = [
                {
                    "name": blob.name.replace('uploads/', ''),
                    "size": blob.size,
                    "type": blob.name.split('.')[-1] if '.' in blob.name else "Unknown",
                    "date_modified": blob.updated.strftime('%Y-%m-%d %H:%M:%S') if blob.updated else "Unknown"
                }
                for blob in blobs if blob.name != 'uploads/'
            ]
        else:
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
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            src_blob = bucket.blob(f"uploads/{filename}")
            if src_blob.exists():
                dest_blob = bucket.blob(f"trash/{filename}")
                bucket.copy_blob(src_blob, bucket, f"trash/{filename}")
                src_blob.delete()
                logging.info(f"File {filename} moved to trash.")
                return jsonify({"message": f"{filename} moved to trash.", "status": "deleted"}), 200
            else:
                return jsonify({"error": "File not found"}), 404
        else:
            src_path = os.path.join(UPLOAD_FOLDER, filename)
            dest_path = os.path.join(TRASH_FOLDER, filename)
            if os.path.exists(src_path):
                shutil.move(src_path, dest_path)
                logging.info(f"File {filename} moved to trash.")
                return jsonify({"message": f"{filename} moved to trash.", "status": "deleted"}), 200
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logging.error(f"Error moving file to trash: {e}")
        return jsonify({"error": "Failed to move file to trash"}), 500

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

    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            old_blob = bucket.blob(f"uploads/{old_name}")
            if not old_blob.exists():
                return jsonify({"error": "File not found"}), 404
            
            new_blob = bucket.blob(f"uploads/{new_name}")
            if new_blob.exists():
                return jsonify({"error": "A file with the new name already exists"}), 409
            
            bucket.copy_blob(old_blob, bucket, f"uploads/{new_name}")
            old_blob.delete()
            logging.info(f"File renamed from {old_name} to {new_name}.")
        else:
            old_path = os.path.join(UPLOAD_FOLDER, old_name)
            new_path = os.path.join(UPLOAD_FOLDER, new_name)
            
            if not os.path.exists(old_path):
                return jsonify({"error": "File not found"}), 404
            
            if os.path.exists(new_path):
                return jsonify({"error": "A file with the new name already exists"}), 409
            
            os.rename(old_path, new_path)
            logging.info(f"File renamed from {old_name} to {new_name}.")
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        return jsonify({"error": "Failed to rename file"}), 500

    return jsonify({"message": f"File renamed from {old_name} to {new_name}"}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        if USE_FIREBASE:
            bucket = storage.bucket()
            blob = bucket.blob(f"uploads/{filename}")
            if blob.exists():
                file_data = blob.download_as_bytes()
                return send_file(
                    BytesIO(file_data),
                    as_attachment=True,
                    download_name=filename
                )
            else:
                return jsonify({"error": "File not found"}), 404
        else:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True)
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": "Failed to download file"}), 500

@app.route('/create-file', methods=['POST'])
def create_file():
    data = request.get_json()
    filename = data.get('filename')
    content = data.get('content', '')

    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    try:
        if USE_FIREBASE:
            # Upload to Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(f"uploads/{filename}")
            blob.upload_from_string(content, content_type='text/plain')
            logging.info(f"File {filename} created in Firebase successfully.")
        else:
            # Fallback to local storage
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            with open(file_path, 'w') as f:
                f.write(content)
            logging.info(f"File {filename} created locally successfully.")
        
        return jsonify({"message": "File created successfully!"}), 201
    except Exception as e:
        logging.error(f"Error creating file: {e}")
        return jsonify({"error": f"Error creating file: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if os.environ.get('VERCEL'):
        app.run(debug=False)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
