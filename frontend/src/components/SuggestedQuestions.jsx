function formatColumnName(columnName) {
  return columnName.replaceAll("_", " ");
}

function SuggestedQuestions({ profile, onSelectQuestion }) {
  if (!profile) return null;

  const metricColumns = profile.metric_columns || [];
  const categoricalColumns = profile.categorical_columns || [];

  const primaryMetric = metricColumns.includes("revenue")
    ? "revenue"
    : metricColumns[0];

  const suggestions = [];

  if (primaryMetric && categoricalColumns.length > 0) {
    categoricalColumns.forEach((column) => {
      suggestions.push({
        label: `Which ${formatColumnName(column)} has the highest ${formatColumnName(
          primaryMetric
        )}?`,
        value: `Which ${column} has the highest ${primaryMetric}?`,
      });
    });
  }

  if (primaryMetric) {
    suggestions.push({
      label: `What is the total ${formatColumnName(primaryMetric)}?`,
      value: `What is the total ${primaryMetric}?`,
    });

    suggestions.push({
      label: `What is the average ${formatColumnName(primaryMetric)}?`,
      value: `What is the average ${primaryMetric}?`,
    });
  }

  suggestions.push({
    label: "Show missing values",
    value: "Show missing values",
  });

  suggestions.push({
    label: "Give me a summary of this dataset",
    value: "Give me a summary of this dataset",
  });

  return (
    <section className="card">
      <h2>Suggested Questions</h2>
      <p className="muted">
        Start with one of these questions based on the uploaded dataset.
      </p>

      <div className="suggestion-grid">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.value}
            type="button"
            className="suggestion-button"
            onClick={() => onSelectQuestion(suggestion.value)}
          >
            {suggestion.label}
          </button>
        ))}
      </div>
    </section>
  );
}

export default SuggestedQuestions;