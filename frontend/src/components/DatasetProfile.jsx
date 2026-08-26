function DatasetProfile({ profile, dataset }) {
  if (!profile) return null;

  return (
    <section className="card">
      <h2>Dataset Profile</h2>

      {dataset && (
        <div className="info-grid">
          <div>
            <strong>Dataset ID</strong>
            <p>{dataset.dataset_id}</p>
          </div>
          <div>
            <strong>File Name</strong>
            <p>{dataset.original_filename}</p>
          </div>
        </div>
      )}

      <div className="info-grid">
        <div>
          <strong>Rows</strong>
          <p>{profile.rows}</p>
        </div>
        <div>
          <strong>Columns</strong>
          <p>{profile.columns}</p>
        </div>
        <div>
          <strong>Duplicate Rows</strong>
          <p>{profile.duplicate_rows}</p>
        </div>
      </div>

      <div className="column-section">
        <h3>Numeric Columns</h3>
        <p>{profile.numeric_columns?.join(", ") || "None"}</p>
      </div>

      <div className="column-section">
        <h3>Categorical Columns</h3>
        <p>{profile.categorical_columns?.join(", ") || "None"}</p>
      </div>

      <div className="column-section">
        <h3>Date-like Columns</h3>
        <p>{profile.date_like_columns?.join(", ") || "None"}</p>
      </div>

      <div className="column-section">
        <h3>Missing Values</h3>
        <table>
          <thead>
            <tr>
              <th>Column</th>
              <th>Missing Count</th>
              <th>Missing %</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(profile.missing_values || {}).map((column) => (
              <tr key={column}>
                <td>{column}</td>
                <td>{profile.missing_values[column]}</td>
                <td>{profile.missing_percentages[column]}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default DatasetProfile;