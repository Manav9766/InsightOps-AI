import { useState } from "react";
import { askDatasetQuestion } from "../api/client";

function QuestionBox({ datasetId, onAnalysisResult }) {
  const [question, setQuestion] = useState(
    "Which region has the highest revenue?"
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    if (!datasetId) {
      setError("Please upload a dataset first.");
      return;
    }

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    try {
      setError("");
      setIsAnalyzing(true);

      const result = await askDatasetQuestion(datasetId, question);
      onAnalysisResult(result);
    } catch (err) {
      const message =
        err.response?.data?.detail || "Failed to analyze the dataset.";
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <section className="card">
      <h2>Ask a Business Question</h2>
      <p className="muted">
        The system creates an analysis plan and runs pandas calculations.
      </p>

      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        rows="3"
        placeholder="Ask a question about the dataset..."
      />

      <button onClick={handleAnalyze} disabled={isAnalyzing || !datasetId}>
        {isAnalyzing ? "Analyzing..." : "Analyze"}
      </button>

      {error && <p className="error">{error}</p>}
    </section>
  );
}

export default QuestionBox;