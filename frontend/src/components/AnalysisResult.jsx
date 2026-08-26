function AnalysisResult({ result }) {
  if (!result) return null;

  const tableRows = result.table || [];
  const tableColumns = tableRows.length > 0 ? Object.keys(tableRows[0]) : [];

  return (
    <section className="card">
      <h2>Analysis Result</h2>

      <div className="result-box">
        <h3>Computed Answer</h3>
        <p>{result.answer}</p>
      </div>

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