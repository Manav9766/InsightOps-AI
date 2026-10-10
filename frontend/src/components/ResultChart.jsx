import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function ResultChart({ chart }) {
  if (!chart || !chart.data || chart.data.length === 0) {
    return null;
  }

  if (chart.type === "bar") {
    return (
      <div className="result-box">
        <h3>{chart.title}</h3>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chart.x_key} />
              <YAxis />
              <Tooltip />
              <Bar dataKey={chart.y_key} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  if (chart.type === "line") {
    return (
      <div className="result-box">
        <h3>{chart.title}</h3>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chart.x_key} />
              <YAxis />
              <Tooltip />

              <Line
                type="monotone"
                dataKey={chart.y_key}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  if (chart.type === "histogram") {
    return (
      <div className="result-box">
        <h3>{chart.title}</h3>

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey={chart.x_key}
                angle={-20}
                textAnchor="end"
                height={70}
              />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey={chart.y_key} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  return null;
}

export default ResultChart;