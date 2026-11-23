
import { useCallback, useEffect, useRef, useState } from "react";

import AnalysisResult from "./AnalysisResult";

import {
  listAnalysisHistory,
  getSavedAnalysis,
  getAnalysisError,
} from "../api/client";


function AnalysisHistory() {
  const [records, setRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);

  const [loading, setLoading] = useState(false);
  const [opening, setOpening] = useState(false);

  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  const listRequest = useRef(null);
  const detailRequest = useRef(null);


  const loadHistory = useCallback(async () => {
    listRequest.current?.abort();

    const controller = new AbortController();
    listRequest.current = controller;

    setLoading(true);
    setError("");

    try {
      const response = await listAnalysisHistory(
        controller.signal
      );

      if (listRequest.current === controller) {
        setRecords(response.items || []);
      }

    } catch (err) {
      if (
        !controller.signal.aborted &&
        listRequest.current === controller
      ) {
        setError(getAnalysisError(err));
      }

    } finally {
      if (listRequest.current === controller) {
        listRequest.current = null;
        setLoading(false);
      }
    }
  }, []);


  useEffect(() => {
    const loadTimer = window.setTimeout(
      loadHistory,
      0
    );

    return () => {
      window.clearTimeout(loadTimer);
      listRequest.current?.abort();
      detailRequest.current?.abort();
    };
  }, [loadHistory]);


  async function handleOpenAnalysis(analysisId) {
    detailRequest.current?.abort();

    const controller = new AbortController();
    detailRequest.current = controller;

    setOpening(true);
    setDetailError("");
    setSelectedRecord(null);

    try {
      const result = await getSavedAnalysis(
        analysisId,
        controller.signal
      );

      if (detailRequest.current === controller) {
        setSelectedRecord(result);
      }

    } catch (err) {
      if (
        !controller.signal.aborted &&
        detailRequest.current === controller
      ) {
        setDetailError(getAnalysisError(err));
      }

    } finally {
      if (detailRequest.current === controller) {
        detailRequest.current = null;
        setOpening(false);
      }
    }
  }


  function formatDate(value) {
    if (!value) return "Unknown";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  }


  return (
    <section className="card analysis-history">
      <div className="history-header">
        <div>
          <h2>Analysis History</h2>

          <p className="muted">
            Browse previously saved verified analyses.
            Reopen results without rerunning OpenAI
            or pandas calculations.
          </p>
        </div>

        <button
          type="button"
          onClick={loadHistory}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh History"}
        </button>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && records.length === 0 && (
        <p className="muted">
          No saved analyses found. Complete an AI
          analysis to create your first history record.
        </p>
      )}

      {records.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Question</th>
                <th>Analysis Type</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {records.map((record) => (
                <tr key={record.analysis_id}>
                  <td>
                    {formatDate(record.created_at)}
                  </td>

                  <td>{record.question}</td>

                  <td>{record.analysis_type}</td>

                  <td>
                    <span
                      className={`review-badge ${
                        record.evaluation_status === "passed"
                          ? "review-badge--safe"
                          : "review-badge--bad"
                      }`}
                    >
                      {record.evaluation_status}
                    </span>
                  </td>

                  <td>
                    <button
                      type="button"
                      disabled={opening}
                      onClick={() =>
                        handleOpenAnalysis(
                          record.analysis_id
                        )
                      }
                    >
                      Open Result
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {opening && (
        <p className="muted" role="status">
          Loading saved analysis...
        </p>
      )}

      {detailError && (
        <p className="error" role="alert">
          {detailError}
        </p>
      )}

      {selectedRecord && (
        <div className="history-detail">
          <h3>Saved Analysis</h3>

          <p className="muted">
            Created: {formatDate(selectedRecord.created_at)}
          </p>

          <p className="muted">
            This is a read-only historical result.
            No new AI analysis has been performed.
          </p>

          <AnalysisResult
            result={selectedRecord.analysis}
          />
        </div>
      )}
    </section>
  );
}

export default AnalysisHistory;
