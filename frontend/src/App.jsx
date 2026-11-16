
import { useEffect, useRef, useState } from "react";

import DatasetUpload from "./components/DatasetUpload";
import DatasetProfile from "./components/DatasetProfile";
import DatasetPreview from "./components/DatasetPreview";
import SuggestedQuestions from "./components/SuggestedQuestions";
import QuestionBox from "./components/QuestionBox";
import AnalysisResult from "./components/AnalysisResult";
import InsightReviewPanel from "./components/InsightReviewPanel";

import {
  askDatasetQuestion,
  reviewDatasetInsight,
  getAnalysisError,
} from "./api/client";


function App() {
  const [dataset, setDataset] = useState(null);
  const [profile, setProfile] = useState(null);

  const [question, setQuestion] = useState("");
  const [plannerMode, setPlannerMode] = useState("ai");

  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const [insightReview, setInsightReview] = useState(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [insightError, setInsightError] = useState("");

  const insightRequest = useRef(null);
  const activeRequest = useRef(null);


  useEffect(() => {
    return () => {
      activeRequest.current?.abort();
      insightRequest.current?.abort();
    };
  }, []);


  function cancelActiveInsightReview() {
    insightRequest.current?.abort();

    insightRequest.current = null;

    setIsReviewing(false);
    setInsightReview(null);
    setInsightError("");
  }


  function cancelActiveAnalysis() {
    cancelActiveInsightReview();

    activeRequest.current?.abort();
    activeRequest.current = null;
    setIsAnalyzing(false);
  }


  function handleUploadSuccess(uploadResponse) {
    cancelActiveAnalysis();

    setDataset(uploadResponse.dataset);
    setProfile(uploadResponse.profile);

    setAnalysisResult(null);
    setError("");

    const metricColumns =
      uploadResponse.profile?.metric_columns || [];

    const categoricalColumns =
      uploadResponse.profile?.categorical_columns || [];

    const primaryMetric =
      metricColumns.includes("revenue")
        ? "revenue"
        : metricColumns[0];

    const primaryCategory =
      categoricalColumns.includes("region")
        ? "region"
        : categoricalColumns[0];

    if (primaryMetric && primaryCategory) {
      setQuestion(
        `Which ${primaryCategory} has the highest ${primaryMetric}?`
      );
    } else if (primaryMetric) {
      setQuestion(`What is the total ${primaryMetric}?`);
    } else {
      setQuestion("Give me a summary of this dataset");
    }
  }


  function handleQuestionChange(newQuestion) {
    cancelActiveAnalysis();

    setQuestion(newQuestion);
    setAnalysisResult(null);
    setError("");
  }


  function handlePlannerModeChange(newMode) {
    if (isAnalyzing) return;

    cancelActiveInsightReview();

    setPlannerMode(newMode);
    setAnalysisResult(null);
    setError("");
  }


  async function handleAnalyze() {
    if (isAnalyzing) return;

    if (!dataset?.dataset_id) {
      setError("Please upload a dataset first.");
      return;
    }

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    cancelActiveInsightReview();

    const controller = new AbortController();
    activeRequest.current = controller;

    setIsAnalyzing(true);
    setError("");
    setAnalysisResult(null);

    try {
      const result = await askDatasetQuestion(
        dataset.dataset_id,
        question.trim(),
        plannerMode,
        controller.signal
      );

      if (activeRequest.current === controller) {
        setAnalysisResult(result);
      }

    } catch (err) {
      if (
        !controller.signal.aborted &&
        activeRequest.current === controller
      ) {
        setError(getAnalysisError(err));
      }

    } finally {
      if (activeRequest.current === controller) {
        activeRequest.current = null;
        setIsAnalyzing(false);
      }
    }
  }


  const supportedInsightTypes = [
    "groupby_aggregation_desc",
    "groupby_aggregation_asc",
    "time_trend",
    "correlation",
  ];

  const canReviewInsight =
    Boolean(analysisResult) &&
    plannerMode === "ai" &&
    analysisResult.evaluation?.status === "passed" &&
    supportedInsightTypes.includes(
      analysisResult.analysis_plan?.analysis_type
    );


  async function handleReviewInsight() {
    if (!canReviewInsight || isReviewing) {
      return;
    }

    const controller = new AbortController();

    insightRequest.current = controller;

    setIsReviewing(true);
    setInsightError("");
    setInsightReview(null);

    try {
      const result = await reviewDatasetInsight(
        dataset.dataset_id,
        question.trim(),
        controller.signal
      );

      if (insightRequest.current === controller) {
        setInsightReview(result);
      }

    } catch (err) {
      if (
        !controller.signal.aborted &&
        insightRequest.current === controller
      ) {
        setInsightError(getAnalysisError(err));
      }

    } finally {
      if (insightRequest.current === controller) {
        insightRequest.current = null;
        setIsReviewing(false);
      }
    }
  }


  return (
    <main className="app-container">
      <header className="hero">
        <p className="eyebrow">InsightOps AI</p>

        <h1>
          Agentic Data Analyst & Business Intelligence Platform
        </h1>

        <p>
          Upload a dataset, inspect its profile, ask
          business questions, and receive computed
          results backed by pandas.
        </p>
      </header>

      <DatasetUpload
        onUploadSuccess={handleUploadSuccess}
      />

      <DatasetProfile
        dataset={dataset}
        profile={profile}
      />

      <DatasetPreview
        rows={profile?.preview_rows}
      />

      <SuggestedQuestions
        profile={profile}
        onSelectQuestion={handleQuestionChange}
      />

      <QuestionBox
        datasetId={dataset?.dataset_id}
        question={question}
        setQuestion={handleQuestionChange}
        plannerMode={plannerMode}
        setPlannerMode={handlePlannerModeChange}
        onAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
        error={error}
      />

      <AnalysisResult
        result={analysisResult}
      />

      <InsightReviewPanel
        analysisReady={Boolean(analysisResult)}
        enabled={canReviewInsight}
        loading={isReviewing}
        review={insightReview}
        error={insightError}
        onReview={handleReviewInsight}
      />
    </main>
  );
}

export default App;
