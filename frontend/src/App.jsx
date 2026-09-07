import { useState } from "react";

import DatasetUpload from "./components/DatasetUpload";
import DatasetProfile from "./components/DatasetProfile";
import DatasetPreview from "./components/DatasetPreview";
import SuggestedQuestions from "./components/SuggestedQuestions";
import QuestionBox from "./components/QuestionBox";
import AnalysisResult from "./components/AnalysisResult";

function App() {
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
        <p className="eyebrow">InsightOps AI</p>
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