
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api";


export async function uploadCsv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${API_BASE_URL}/upload/csv`,
    formData
  );

  return response.data;
}


export async function askDatasetQuestion(
  datasetId,
  question,
  planner = "ai",
  signal
) {
  if (!["ai", "rule"].includes(planner)) {
    throw new Error("Invalid analysis planner selected.");
  }

  const endpoint =
    planner === "ai"
      ? "/analysis/execute"
      : "/analysis/question";

  const response = await axios.post(
    `${API_BASE_URL}${endpoint}`,
    {
      dataset_id: datasetId,
      question: question.trim(),
    },
    { signal }
  );

  return response.data;
}


export async function reviewDatasetInsight(
  datasetId,
  question,
  analysisId,
  signal
) {
  if (!analysisId) {
    throw new Error(
      "A verified analysis ID is required."
    );
  }

  const response = await axios.post(
    `${API_BASE_URL}/analysis/insights/review`,
    {
      dataset_id: datasetId,
      question: question.trim(),
      analysis_id: analysisId,
    },
    { signal }
  );

  return response.data;
}


export function getAnalysisError(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || "Validation error")
      .join(", ");
  }

  if (error.response?.status === 502) {
    return "AI planning service is unavailable. Please try again.";
  }

  if (error.response?.status === 503) {
    return "AI planning service is not configured.";
  }

  if (!error.response) {
    return "Cannot connect to the backend. Check that FastAPI is running.";
  }

  return error.message || "Analysis failed. Please try again.";
}

export async function listAnalysisHistory(signal) {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/history`,
    {
      params: { limit: 50 },
      signal,
    }
  );

  return response.data;
}


export async function getSavedAnalysis(
  analysisId,
  signal
) {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/history/${encodeURIComponent(analysisId)}`,
    { signal }
  );

  return response.data;
}

export async function listSavedBusinessReports(signal) {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/reports`,
    {
      params: { limit: 50 },
      signal,
    }
  );

  return response.data;
}


export async function getSavedBusinessReport(
  reportId,
  signal
) {
  const response = await axios.get(
    `${API_BASE_URL}/analysis/reports/${encodeURIComponent(reportId)}`,
    { signal }
  );

  return response.data;
}
