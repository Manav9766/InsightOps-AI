
function QuestionBox({
  datasetId,
  question,
  setQuestion,
  plannerMode,
  setPlannerMode,
  onAnalyze,
  isAnalyzing,
  error,
}) {
  function handleSubmit(event) {
    event.preventDefault();
    onAnalyze();
  }

  return (
    <section className="card">
      <h2>Ask a Business Question</h2>

      <p className="muted">
        Select an analysis mode and ask a question about
        your uploaded dataset.
      </p>

      <div className="planner-section">
        <h3>Analysis Mode</h3>

        <div
          className="planner-mode-switch"
          role="group"
          aria-label="Analysis mode"
        >
          <button
            type="button"
            className={`planner-mode-button ${
              plannerMode === "ai" ? "active" : ""
            }`}
            aria-pressed={plannerMode === "ai"}
            disabled={isAnalyzing}
            onClick={() => setPlannerMode("ai")}
          >
            AI Planner
          </button>

          <button
            type="button"
            className={`planner-mode-button ${
              plannerMode === "rule" ? "active" : ""
            }`}
            aria-pressed={plannerMode === "rule"}
            disabled={isAnalyzing}
            onClick={() => setPlannerMode("rule")}
          >
            Rule-based
          </button>
        </div>

        <p className="muted planner-description">
          {plannerMode === "ai"
            ? "OpenAI interprets your question and generates a validated analysis plan. Pandas performs the calculations."
            : "Uses the existing rule-based planner without making an OpenAI API request."}
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <label htmlFor="business-question">
          <strong>Your Question</strong>
        </label>

        <textarea
          id="business-question"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          rows={3}
          placeholder="Ask a question about the dataset..."
          disabled={isAnalyzing}
        />

        <button
          type="submit"
          disabled={
            isAnalyzing ||
            !datasetId ||
            !question.trim()
          }
        >
          {isAnalyzing
            ? "Analyzing..."
            : "Analyze"}
        </button>

        {isAnalyzing && (
          <p className="muted" role="status">
            {plannerMode === "ai"
              ? "Generating AI plan and running pandas analysis..."
              : "Running pandas analysis..."}
          </p>
        )}

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
    </section>
  );
}

export default QuestionBox;
