import { useState } from "react";

import DatasetUpload from "./components/DatasetUpload";
import DatasetProfile from "./components/DatasetProfile";
import DatasetPreview from "./components/DatasetPreview";
import QuestionBox from "./components/QuestionBox";
import AnalysisResult from "./components/AnalysisResult";

function App() {
  const [dataset, setDataset] = useState(null);
  const [profile, setProfile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  function handleUploadSuccess(uploadResponse) {
    setDataset(uploadResponse.dataset);
    setProfile(uploadResponse.profile);
    setAnalysisResult(null);
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

      <QuestionBox
        datasetId={dataset?.dataset_id}
        onAnalysisResult={setAnalysisResult}
      />

      <AnalysisResult result={analysisResult} />
    </main>
  );
}

export default App;