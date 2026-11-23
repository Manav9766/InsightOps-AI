
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import InsightReviewPanel from "./InsightReviewPanel";

import {
  listSavedBusinessReports,
  getSavedBusinessReport,
  getAnalysisError,
} from "../api/client";


function formatDate(value) {
  if (!value) return "Unknown";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}


function SavedBusinessReports({ refreshToken = 0 }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  const [loading, setLoading] = useState(false);
  const [opening, setOpening] = useState(false);

  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  const listRequest = useRef(null);
  const detailRequest = useRef(null);


  const loadReports = useCallback(async () => {
    listRequest.current?.abort();

    const controller = new AbortController();
    listRequest.current = controller;

    setLoading(true);
    setError("");

    try {
      const data = await listSavedBusinessReports(
        controller.signal
      );

      if (
        listRequest.current === controller &&
        !controller.signal.aborted
      ) {
        setReports(
          Array.isArray(data.items) ? data.items : []
        );
      }
    } catch (err) {
      if (
        listRequest.current === controller &&
        !controller.signal.aborted
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
      loadReports,
      0
    );

    return () => {
      window.clearTimeout(loadTimer);
      listRequest.current?.abort();
      detailRequest.current?.abort();
    };
  }, [loadReports, refreshToken]);


  async function handleOpenReport(reportId) {
    detailRequest.current?.abort();

    const controller = new AbortController();
    detailRequest.current = controller;

    setOpening(true);
    setDetailError("");
    setSelectedReport(null);

    try {
      const data = await getSavedBusinessReport(
        reportId,
        controller.signal
      );

      if (
        detailRequest.current === controller &&
        !controller.signal.aborted
      ) {
        setSelectedReport(data);
      }
    } catch (err) {
      if (
        detailRequest.current === controller &&
        !controller.signal.aborted
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


  return (
    <section className="card saved-business-reports">
      <div className="saved-reports-header">
        <div>
          <h2>Saved Business Reports</h2>

          <p className="muted">
            Browse previous AI-reviewed business insights,
            including their verified facts, narrative
            assessments, evidence coverage and limitations.
          </p>
        </div>

        <button
          type="button"
          onClick={loadReports}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh Reports"}
        </button>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && reports.length === 0 && (
        <p className="muted">
          No saved business reports yet. Run an AI
          analysis and generate a reviewed insight
          to create your first saved report.
        </p>
      )}

      {reports.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Created</th>
                <th>Report Title</th>
                <th>Review</th>
                <th>Publication</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {reports.map((report) => (
                <tr key={report.report_id}>
                  <td>{formatDate(report.created_at)}</td>

                  <td>{report.title}</td>

                  <td>
                    <span
                      className={`review-badge ${
                        report.review_status === "supported"
                          ? "review-badge--safe"
                          : report.review_status === "qualified"
                          ? "review-badge--caution"
                          : "review-badge--bad"
                      }`}
                    >
                      {report.review_status}
                    </span>
                  </td>

                  <td>
                    <span className="muted">
                      Not published
                    </span>
                  </td>

                  <td>
                    <button
                      type="button"
                      onClick={() =>
                        handleOpenReport(report.report_id)
                      }
                      disabled={opening}
                    >
                      Open Report
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
          Loading saved business report...
        </p>
      )}

      {detailError && (
        <p className="error" role="alert">
          {detailError}
        </p>
      )}

      {selectedReport && (
        <div className="saved-report-detail">
          <h3>{selectedReport.title}</h3>

          <p className="muted">
            Created: {formatDate(selectedReport.created_at)}
          </p>

          <p className="muted">
            Report ID: {selectedReport.report_id}
          </p>

          <p className="muted">
            Original analysis ID:{" "}
            {selectedReport.analysis_id}
          </p>

          <InsightReviewPanel
            analysisReady={true}
            enabled={false}
            loading={false}
            review={selectedReport.report}
            error=""
            readOnly={true}
          />
        </div>
      )}
    </section>
  );
}

export default SavedBusinessReports;
