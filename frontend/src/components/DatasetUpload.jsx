import { useState } from "react";
import { uploadCsv } from "../api/client";

function DatasetUpload({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  async function handleUpload() {
    if (!selectedFile) {
      setError("Please select a CSV file first.");
      return;
    }

    try {
      setError("");
      setIsUploading(true);

      const result = await uploadCsv(selectedFile);
      onUploadSuccess(result);
    } catch (err) {
      const message =
        err.response?.data?.detail || "Failed to upload CSV file.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="card">
      <h2>Upload Dataset</h2>
      <p className="muted">Upload a CSV file to profile and analyze it.</p>

      <div className="upload-row">
        <input
          type="file"
          accept=".csv"
          onChange={(event) => setSelectedFile(event.target.files[0])}
        />

        <button onClick={handleUpload} disabled={isUploading}>
          {isUploading ? "Uploading..." : "Upload CSV"}
        </button>
      </div>

      {selectedFile && (
        <p className="muted">Selected file: {selectedFile.name}</p>
      )}

      {error && <p className="error">{error}</p>}
    </section>
  );
}

export default DatasetUpload;