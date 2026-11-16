import ResultChart from "./ResultChart";
function AnalysisResult({ result }) {
  if (!result) return null;

  const evaluationStatus = result.evaluation?.status;

  if (evaluationStatus === "failed") {
    return (
      <section className="card">
        <h2>Analysis Result</h2>

        <div className="review-warning" role="alert">
          <strong>Calculation verification failed</strong>

          <p>
            The computed result did not pass independent
            verification. Its answer, chart, and supporting
            table have been withheld.
          </p>
        </div>
      </section>
    );
  }

  const tableRows = result.table || [];
  const tableColumns = tableRows.length > 0 ? Object.keys(tableRows[0]) : [];

  return (
    <section className="card">
      <h2>Analysis Result</h2>

      <p
        className={
          evaluationStatus === "passed"
            ? "review-calculation-passed"
            : "review-calculation-unverified"
        }
      >
        {evaluationStatus === "passed"
          ? "Independent calculation verification passed."
          : "This calculation has not been independently verified."}
      </p>

      <div className="result-box">
        <h3>Computed Answer</h3>
        <p>{result.answer}</p>
      </div>
      <ResultChart chart={result.chart} />
      <div className="result-box">
        <h3>Analysis Plan</h3>
        <p>
          <strong>Type:</strong> {result.analysis_plan?.analysis_type}
        </p>

        <ol>
          {result.analysis_plan?.steps?.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
      </div>

      {tableRows.length > 0 && (
        <div className="result-box">
          <h3>Supporting Table</h3>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {tableColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {tableRows.map((row, index) => (
                  <tr key={index}>
                    {tableColumns.map((column) => (
                      <td key={column}>{String(row[column])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="result-box">
        <h3>Calculation Trace</h3>
        <pre>{JSON.stringify(result.calculation_trace, null, 2)}</pre>
      </div>
    </section>
  );
}

export default AnalysisResult;
