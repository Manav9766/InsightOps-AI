import { askDatasetQuestion } from "../api/client";

function QuestionBox({
  datasetId,
  question,
  setQuestion,
  onAnalysisResult,
}) {
  async function handleAnalyze() {
    if (!datasetId) {
      alert("Please upload a dataset first.");
      return;
    }

    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    try {
      const result = await askDatasetQuestion(datasetId, question);
      onAnalysisResult(result);
    } catch (err) {
      const message =
        err.response?.data?.detail || "Failed to analyze the dataset.";
      alert(message);
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

      <button onClick={handleAnalyze} disabled={!datasetId}>
        Analyze
      </button>
    </section>
  );
}

export default QuestionBox;