import { useState } from "react";

import DatasetUpload from "./components/DatasetUpload";
import DatasetProfile from "./components/DatasetProfile";
import DatasetPreview from "./components/DatasetPreview";
import SuggestedQuestions from "./components/SuggestedQuestions";
import QuestionBox from "./components/QuestionBox";
import AnalysisResult from "./components/AnalysisResult";

function App() {
  const [theme, setTheme] = useState(document.documentElement.dataset.theme);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    setTheme(nextTheme);
    try {
      localStorage.setItem("insightops-theme", nextTheme);
    } catch {
      // Theme switching still works when browser storage is unavailable.
    }
  }

  const [dataset, setDataset] = useState(null);
  const [profile, setProfile] = useState(null);
  const [question, setQuestion] = useState(
    "Which region has the highest revenue?"
  );
  const [analysisResult, setAnalysisResult] = useState(null);

  function handleUploadSuccess(uploadResponse) {
    setDataset(uploadResponse.dataset);
    setProfile(uploadResponse.profile);
    setAnalysisResult(null);

    const metricColumns = uploadResponse.profile?.metric_columns || [];
    const categoricalColumns = uploadResponse.profile?.categorical_columns || [];

    const primaryMetric = metricColumns.includes("revenue")
      ? "revenue"
      : metricColumns[0];

    const primaryCategory = categoricalColumns.includes("region")
      ? "region"
      : categoricalColumns[0];

    if (primaryMetric && primaryCategory) {
      setQuestion(`Which ${primaryCategory} has the highest ${primaryMetric}?`);
    }
  }

  return (
    <main className="app-container">
      <header className="hero">
        <div className="hero-toolbar">
          <p className="eyebrow">InsightOps AI</p>
          <button
            type="button"
            className="theme-toggle"
            aria-label="Dark mode"
            aria-pressed={theme === "dark"}
            onClick={toggleTheme}
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </div>
        <h1>Agentic Data Analyst & Business Intelligence Platform</h1>
        <p>
          Upload a dataset, inspect its profile, ask a business question, and
          get a pandas-backed computed answer with an analysis plan.
        </p>
      </header>

      <DatasetUpload onUploadSuccess={handleUploadSuccess} />

      <DatasetProfile dataset={dataset} profile={profile} />

      <DatasetPreview rows={profile?.preview_rows} />

      <SuggestedQuestions
        profile={profile}
        onSelectQuestion={setQuestion}
      />

      <QuestionBox
        datasetId={dataset?.dataset_id}
        question={question}
        setQuestion={setQuestion}
        onAnalysisResult={setAnalysisResult}
      />

      <AnalysisResult result={analysisResult} />
    </main>
  );
}

export default App;
