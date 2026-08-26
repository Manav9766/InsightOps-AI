import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export async function uploadCsv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(`${API_BASE_URL}/upload/csv`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

export async function askDatasetQuestion(datasetId, question) {
  const response = await axios.post(`${API_BASE_URL}/analysis/question`, {
    dataset_id: datasetId,
    question,
  });

  return response.data;
}