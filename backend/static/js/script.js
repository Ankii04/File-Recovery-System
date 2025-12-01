document.addEventListener("DOMContentLoaded", () => {
    viewFiles();
    viewTrash();
    toggleFileAction();

    document.getElementById("refreshButton").addEventListener("click", refreshFileList);
    document.getElementById("recycleBinButton").addEventListener("click", () => {
        viewTrash();
        toggleTrashView(true);
    });
});

const truncateFileName = (name, maxLength = 20) => name.length > maxLength ? name.substring(0, 17) + '...' : name;

function updateFileName() {
    let fileInput = document.getElementById("fileInput");
    document.getElementById("selectedFileName").textContent = fileInput.files.length ? truncateFileName(fileInput.files[0].name) : "No file chosen";
}

async function uploadFile() {
    let fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) return alert("Please select a file to upload!");

    let formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        let response = await fetch('/upload', { method: 'POST', body: formData });
        let data = await response.json();
        alert(data.message || data.error);
        refreshFileList();
        document.getElementById("selectedFileName").textContent = "No file chosen";
    } catch (error) {
        console.error(error);
    }
}

function toggleFileAction() {
    let action = document.getElementById("fileAction").value;
    document.getElementById("uploadSection").classList.add("hidden");
    document.getElementById("createSection").classList.add("hidden");

    if (action === "upload") document.getElementById("uploadSection").classList.remove("hidden");
    else if (action === "create") document.getElementById("createSection").classList.remove("hidden");
}

async function createFile() {
    let filename = document.getElementById("fileNameInput").value.trim();
    let content = document.getElementById("fileContentInput").value;

    if (!filename) return alert("Filename is required!");

    try {
        let response = await fetch('/create-file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, content })
        });

        let result = await response.json();
        if (!response.ok) throw new Error(result.error || "Failed to create file");

        alert(result.message);
        refreshFileList();
        document.getElementById("fileNameInput").value = "";
        document.getElementById("fileContentInput").value = "";
    } catch (error) {
        console.error("Error creating file:", error);
        alert(error.message);
    }
}

async function downloadFile(filename) {
    try {
        let response = await fetch(`/download/${filename}`);
        if (!response.ok) throw new Error("Download failed");

        let blob = await response.blob();
        let link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    } catch (error) {
        alert(error.message);
    }
}

async function viewFiles() {
    try {
        let searchQuery = document.getElementById("searchInput").value;
        let sortBy = document.getElementById("sortOptions").value;

        let response = await fetch(`/files?search=${searchQuery}&sort_by=${sortBy}`);
        let files = await response.json();

        let fileListDiv = document.getElementById("fileList").querySelector('ul');
        fileListDiv.innerHTML = "";

        if (!Array.isArray(files)) {
            console.error("Server returned error:", files);
            if (files.error) {
                fileListDiv.innerHTML = `<li style="color: red;">Error: ${files.error}</li>`;
            }
            return;
        }

        if (files.length === 0) {
            fileListDiv.innerHTML = "<li>No files found.</li>";
            return;
        }

        files.forEach(file => {
            let fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
            let truncatedName = truncateFileName(file.name);

            let li = document.createElement("li");
            li.innerHTML = `
                ${truncatedName} (${file.type}, ${fileSizeMB} MB) 
                <button onclick="downloadFile('${file.name}')">Download</button>
                <button onclick="renameFile('${file.name}')">Rename</button>
                <button onclick="deleteFile('${file.name}')">Delete</button>
            `;
            fileListDiv.appendChild(li);
        });

    } catch (error) {
        console.error("Error fetching files:", error);
    }
}

async function renameFile(oldFilename) {
    let newFilename = prompt(`Rename "${oldFilename}" to:`);
    if (!newFilename) return;

    let response = await fetch('/rename', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_name: oldFilename, new_name: newFilename })
    });

    let result = await response.json();
    alert(result.message || result.error);
    if (response.ok) refreshFileList();
}

async function deleteFile(filename) {
    if (!filename) return console.warn("No file selected for deletion.");

    let confirmDelete = confirm(`Are you sure you want to delete "${filename}"?`);
    if (!confirmDelete) return;

    let response = await fetch(`/delete/${filename}`, { method: 'DELETE' });
    let result = await response.json();

    alert(result.message || result.error);
    if (response.ok) refreshFileList();
}

async function viewTrash() {
    try {
        let response = await fetch('/trash');
        let files = await response.json();

        let trashListUl = document.getElementById('trashList').querySelector('ul');

        if (!Array.isArray(files)) {
            console.error("Server returned error:", files);
            if (files.error) {
                trashListUl.innerHTML = `<li style="color: red;">Error: ${files.error}</li>`;
            }
            return;
        }

        if (files.length === 0) {
            trashListUl.innerHTML = "<li>Trash is empty.</li>";
            return;
        }

        trashListUl.innerHTML = files.map(file => `
            <li>
                ${truncateFileName(file.name)} (${(file.size / (1024 * 1024)).toFixed(2)} MB) 
                <button class="restore-btn" onclick="restoreFile('${file.name}')">Restore</button>
                <button class="delete-permanent-btn" onclick="deletePermanent('${file.name}')">Delete Permanently</button>
            </li>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function restoreFile(filename) {
    try {
        let response = await fetch(`/restore/${filename}`, { method: 'PUT' });
        let data = await response.json();
        alert(data.message || data.error);
        refreshFileList();
    } catch (error) {
        console.error(error);
    }
}

async function deletePermanent(filename) {
    if (!confirm(`Are you sure you want to permanently delete "${filename}"?`)) return;

    try {
        let response = await fetch(`/delete-permanent/${filename}`, { method: 'DELETE' });
        let data = await response.json();
        alert(data.message || data.error);
        viewTrash();
    } catch (error) {
        console.error(error);
    }
}

function toggleTrashView(visible) {
    document.getElementById('trashList').style.display = visible ? 'block' : 'none';
}

function refreshFileList() {
    viewFiles();
    viewTrash();
}
