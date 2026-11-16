const SECTION_CONFIG = [
  {
    key: "headline",
    title: "Headline",
  },
  {
    key: "observation",
    title: "Observation",
  },
  {
    key: "business_implication",
    title: "Business Implication",
  },
];


function InsightReviewPanel({
  analysisReady,
  enabled,
  loading,
  review,
  error,
  onReview,
}) {
  if (!analysisReady) return null;

  const calculationPassed =
    review?.calculation_evaluation?.status === "passed";

  const claimsPassed =
    review?.claim_verification?.status === "passed";

  const narrativeStatus =
    review?.narrative_review?.status;

  const sections =
    review?.narrative_review?.sections || [];

  const verifiedFacts =
    review?.claim_verification?.verified_facts || [];

  const allSectionsReviewed =
    SECTION_CONFIG.every(({ key }) =>
      sections.some(
        (section) =>
          section.section === key &&
          ["supported", "hypothesis", "unsupported"].includes(
            section.verdict
          )
      )
    );

  const hasUnsupportedSections =
    sections.some(
      (section) => section.verdict === "unsupported"
    );

  const canDisplayNarrative =
    calculationPassed &&
    claimsPassed &&
    allSectionsReviewed &&
    !hasUnsupportedSections &&
    ["supported", "qualified"].includes(narrativeStatus);

  const draftWithheld =
    Boolean(review) && !canDisplayNarrative;

  return (
    <section className="card insight-review-panel">
      <h2>Evidence-Grounded AI Insights</h2>

      <p className="muted">
        Generate a business insight with calculation
        verification, structured claim checks, and
        AI-assisted narrative review.
      </p>

      <p className="muted">
        This request runs a fresh analysis of your dataset.
        Its evidence is displayed separately from the
        earlier chart.
      </p>

      {!enabled && (
        <p className="review-warning">
          Insight review currently requires an AI-planned
          ranking, monthly trend, or correlation analysis
          with verified calculations.
        </p>
      )}

      <button
        type="button"
        onClick={onReview}
        disabled={!enabled || loading}
      >
        {loading
          ? "Reviewing Insight..."
          : "Generate Reviewed Insight"}
      </button>

      {loading && (
        <p className="muted" role="status">
          Generating an insight and checking its claims.
          This may take a moment.
        </p>
      )}

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {review && (
        <>
          <div className="review-summary">
            <h3>Verification Summary</h3>

            <div className="review-status-row">
              <span>Calculation verification</span>

              <span
                className={`review-badge ${
                  calculationPassed
                    ? "review-badge--safe"
                    : "review-badge--bad"
                }`}
              >
                {calculationPassed
                  ? "Passed"
                  : "Not passed"}
              </span>
            </div>

            <div className="review-status-row">
              <span>Structured factual claims</span>

              <span
                className={`review-badge ${
                  claimsPassed
                    ? "review-badge--safe"
                    : "review-badge--bad"
                }`}
              >
                {claimsPassed
                  ? "Passed"
                  : "Failed"}
              </span>
            </div>

            <div className="review-status-row">
              <span>AI narrative assessment</span>

              <span
                className={`review-badge ${
                  narrativeStatus === "supported"
                    ? "review-badge--safe"
                    : narrativeStatus === "qualified"
                    ? "review-badge--caution"
                    : "review-badge--bad"
                }`}
              >
                {narrativeStatus || "Not reviewed"}
              </span>
            </div>
          </div>

          {claimsPassed && verifiedFacts.length > 0 && (
            <div className="result-box">
              <h3>Verified Numerical Facts</h3>

              <ul className="review-facts">
                {verifiedFacts.map((fact, index) => (
                  <li key={`${fact.claim_index}-${index}`}>
                    <strong>Verified:</strong>{" "}
                    {fact.statement}

                    <span className="review-evidence">
                      Evidence: {fact.evidence_id}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {draftWithheld && (
            <div
              className="review-warning"
              role="alert"
            >
              <strong>
                Insight narrative withheld
              </strong>

              <p>
                The structured claims did not all pass,
                the reviewer flagged unsupported content,
                or the review result is incomplete.
                This draft should not be presented as
                an approved business insight.
              </p>
            </div>
          )}

          {canDisplayNarrative && (
            <div className="result-box">
              <h3>Reviewed Business Insight</h3>

              <p className="muted">
                These narrative classifications are
                AI-assisted assessments. They do not
                constitute independent factual proof.
              </p>

              {SECTION_CONFIG.map(({ key, title }) => {
                const section = sections.find(
                  (item) => item.section === key
                );

                if (!section) return null;

                const isHypothesis =
                  section.verdict === "hypothesis";

                return (
                  <article
                    key={key}
                    className="review-section"
                  >
                    <div className="review-section-header">
                      <h4>{title}</h4>

                      <span
                        className={`review-badge ${
                          isHypothesis
                            ? "review-badge--caution"
                            : "review-badge--safe"
                        }`}
                      >
                        {isHypothesis
                          ? "Hypothesis"
                          : "AI-reviewed: supported"}
                      </span>
                    </div>

                    <p>
                      {review.insight_draft?.[key]}
                    </p>

                    {isHypothesis && (
                      <p className="review-hypothesis-note">
                        This statement is a hypothesis,
                        not an established business fact.
                      </p>
                    )}

                    <p className="muted">
                      <strong>Review rationale:</strong>{" "}
                      {section.reason}
                    </p>

                    {section.evidence_ids.length > 0 && (
                      <p className="review-evidence">
                        Evidence:{" "}
                        {section.evidence_ids.join(", ")}
                      </p>
                    )}

                    {isHypothesis &&
                      section.suggested_rewrite && (
                        <div className="review-suggestion">
                          <strong>
                            Suggested cautious wording
                            (not independently verified):
                          </strong>

                          <p>
                            {section.suggested_rewrite}
                          </p>
                        </div>
                      )}
                  </article>
                );
              })}

              {review.insight_draft?.limitations?.length > 0 && (
                <div className="review-section">
                  <h4>Analysis Limitations</h4>

                  <ul>
                    {review.insight_draft.limitations.map(
                      (limitation, index) => (
                        <li key={index}>
                          {limitation}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          <p className="review-publication-notice">
            Preview only. This insight has not been
            approved for publication or export.
          </p>
        </>
      )}
    </section>
  );
}

export default InsightReviewPanel;