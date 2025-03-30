# File Recovery System

## Overview
The **File Recovery System** is a web-based application built using **Flask** that allows users to upload and manage files efficiently. It includes a distributed file system for storing uploaded files.

---

## Features
- User-friendly file upload and recovery system
- Built using **Flask** for backend
- Organized **Distributed File System** to manage uploaded files
- Debug mode available for easy development
- Supports **virtual environments** for dependency management
- Provides a clear directory structure for uploaded files

---

## Prerequisites
Before running the project, ensure you have the following installed:
- **Python** (>=3.7)
- **pip** (Python package manager)
- **Virtual Environment**
- **Flask**

---

## Setup Instructions

### 1️⃣ Clone the Repository
```sh
 git clone https://github.com/Ankii04/File-Recovery-System.git
 cd File-Recovery-System
```

### 2️⃣ Activate the Virtual Environment
Navigate to the **backend** directory and activate the virtual environment:
- **For macOS/Linux:**
  ```sh
  source venv/bin/activate
  ```
- **For Windows (Command Prompt):**
  ```sh
  venv\Scripts\activate
  ```

### 3️⃣ Install Dependencies
Make sure you have Flask installed:
```sh
pip install flask
```

---

## Running the Project

### ✅ Start the Flask Server
Navigate to the **backend** directory and run:
```sh
flask --app backend.py run
```
To run in debug mode:
```sh
flask --app backend.py --debug run
```

---

## Upload File Location
All uploaded files are stored in:
```plaintext
File-Recovery-System/
  ├── distributed-file-system/
  │   ├── backend/
  │   │   ├── uploads/   # All uploaded files are saved here
```

### 📂 File Upload Process
1. Navigate to the `distributed-file-system` directory.
2. Enter the `backend` folder.
3. Go to the `uploads` directory to view uploaded files.

---

## Learning Git & GitHub

### Setting up the Virtual Environment
1. Navigate to the **backend** directory and run the following commands:
   - **For macOS/Linux:**
     ```sh
     source venv/bin/activate
     ```
   - **For Windows (Command Prompt):**
     ```sh
     venv\Scripts\activate
     ```

### Installing Flask
1. Go to the **backend** directory:
   ```sh
   pip install flask
   ```

### Running the Project
1. Navigate to the **backend** directory.
2. Run the following command:
   ```sh
   flask --app backend.py run
   ```
3. To run in debug mode, use:
   ```sh
   flask --app backend.py --debug run
   ```

### Upload Files Location
1. Go to the `distributed-file-system` directory.
2. Navigate to the `backend` folder.
3. Enter the `uploads` folder where all uploaded files are stored.

---

## Additional Notes
- The **virtual environment** ensures package dependencies remain isolated.
- The `uploads` folder serves as a dedicated location for user files.
- The project follows best practices for Flask application structure.

---

## Contributing
If you would like to contribute:
1. **Fork** the repository.
2. Create a **new branch** (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m "Added new feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a **Pull Request**.

---
# OS
Learning Git &amp; Github
To activate the virtual environment :
    1: Go to backend directory run these command:
        source venv/bin/activate  # For macOS/Linux
        venv\Scripts\activate     # For Windows (Command Prompt)    

initially install flask:
    1: Go to backend directory: 
        pip install flask


to run this project:
    1: Go to backend directory: 
    2: then run this command: flask --app backend.py run
        and to run in debug mode use this command: flask --app backend.py --debug run

Upload files location:
    1: Go to distributed-file-system
    2: then go to backend
    3: then uploads, here all uploaded files is visible


## License
This project is open-source and available under the **MIT License**.

---

## Contact
For any queries or suggestions, feel free to reach out!

📧 **Email:** ankit1841@gmail.com  
🔗 **GitHub:** [Ankii04](https://github.com/Ankii04)

