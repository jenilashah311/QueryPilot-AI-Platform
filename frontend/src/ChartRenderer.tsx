import React, { useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatAxisNumber } from "./chartUtils";

export type ChartConfig = {
  x_axis?: string;
  y_axis?: string | string[];
  value_col?: string;
  column?: string;
  title?: string;
  format?: string;
  count?: number;
};

type ChartRendererProps = {
  chart_type: string;
  chart_config: ChartConfig;
  rows: Record<string, any>[];
  columns: string[];
  onChartTypeChange?: (type: string) => void;
};

const COLORS = [
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
  "#f97316",
  "#6366f1",
];

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;
  const pt = payload[0]?.payload || {};
  const raw = payload[0]?.value ?? pt.value;
  const num = typeof raw === "number" ? raw : Number(raw);
  const formatted =
    Number.isFinite(num) && typeof num === "number" ? formatAxisNumber(num) : String(raw ?? "");

  return (
    <div
      style={{
        background: "#141a22",
        border: "1px solid #243044",
        borderRadius: 10,
        padding: "0.55rem 0.7rem",
        boxShadow: "0 14px 40px rgba(0,0,0,0.35)",
        color: "#e8ecf2",
      }}
    >
      <div style={{ fontSize: 12, marginBottom: 4, color: "#c4b5fd" }}>
        {label ? `${label}` : ""}
      </div>
      <div style={{ fontWeight: 800, fontSize: 13 }}>
        {formatted}
      </div>
    </div>
  );
};

const MetricChart: React.FC<{
  rows: Record<string, any>[];
  config: ChartConfig;
}> = ({ rows, config }) => {
  const value = useMemo(() => {
    if (!rows.length || !config.value_col) return 0;
    const col = config.value_col;
    const val = rows[0][col];
    return typeof val === "number" ? val : Number(val) || 0;
  }, [rows, config.value_col]);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        flexDirection: "column",
      }}
    >
      <div style={{ fontSize: 48, fontWeight: "bold", color: "#8b5cf6", marginBottom: 12 }}>
        {formatAxisNumber(value)}
      </div>
      <div style={{ fontSize: 14, color: "#9fb0c8" }}>
        {config.title || config.value_col}
      </div>
    </div>
  );
};

const TagsChart: React.FC<{
  rows: Record<string, any>[];
  config: ChartConfig;
}> = ({ rows, config }) => {
  const col = config.column || "";
  const items = useMemo(() => {
    if (!col) return [];
    const seen = new Map<string, number>();
    for (const row of rows.slice(0, config.count || 50)) {
      const val = String(row[col] || "");
      if (val) seen.set(val, (seen.get(val) || 0) + 1);
    }
    return Array.from(seen.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 30);
  }, [rows, col, config.count]);

  const maxCount = Math.max(...items.map((x) => x[1]), 1);

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.75rem",
        padding: "1rem",
        alignItems: "flex-start",
        overflow: "auto",
      }}
    >
      {items.map(([tag, count], idx) => {
        const scale = Math.log(count) / Math.log(maxCount);
        const fontSize = 10 + scale * 16;
        const opacity = 0.6 + scale * 0.4;
        return (
          <div
            key={idx}
            style={{
              fontSize,
              color: COLORS[idx % COLORS.length],
              opacity,
              padding: "0.25rem 0.5rem",
              border: `1px solid ${COLORS[idx % COLORS.length]}40`,
              borderRadius: 4,
              cursor: "default",
            }}
          >
            {tag} ({count})
          </div>
        );
      })}
    </div>
  );
};

const TableChart: React.FC<{
  rows: Record<string, any>[];
  columns: string[];
}> = ({ rows, columns }) => {
  return (
    <div style={{ overflow: "auto", width: "100%", height: "100%" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 12,
        }}
      >
        <thead>
          <tr style={{ borderBottom: "1px solid #243044" }}>
            {columns.map((col) => (
              <th
                key={col}
                style={{
                  padding: "0.5rem",
                  textAlign: "left",
                  fontWeight: 600,
                  color: "#c4b5fd",
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, idx) => (
            <tr key={idx} style={{ borderBottom: "1px solid #1a2332" }}>
              {columns.map((col) => (
                <td
                  key={col}
                  style={{
                    padding: "0.5rem",
                    color: "#e8ecf2",
                  }}
                >
                  {String(row[col] ?? "—").slice(0, 50)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 20 && (
        <div
          style={{
            padding: "0.5rem",
            textAlign: "center",
            color: "#9fb0c8",
            fontSize: 11,
          }}
        >
          ... and {rows.length - 20} more rows
        </div>
      )}
    </div>
  );
};

export const ChartRenderer: React.FC<ChartRendererProps> = ({
  chart_type,
  chart_config,
  rows,
  columns,
}) => {
  const processedData = useMemo(() => {
    if (!rows.length) return [];

    const xKey = chart_config.x_axis || columns[0];
    const yKey = Array.isArray(chart_config.y_axis)
      ? chart_config.y_axis[0]
      : chart_config.y_axis || columns[1] || columns[0];

    return rows.map((row) => ({
      name: String(row[xKey] || "").slice(0, 32),
      value: Number(row[yKey]) || 0,
      raw: row,
    }));
  }, [rows, columns, chart_config.x_axis, chart_config.y_axis]);

  if (chart_type === "metric") {
    return <MetricChart rows={rows} config={chart_config} />;
  }

  if (chart_type === "tags") {
    return <TagsChart rows={rows} config={chart_config} />;
  }

  if (chart_type === "table" || !rows.length) {
    return <TableChart rows={rows} columns={columns} />;
  }

  const hasValues = processedData.some((d) => Number.isFinite(d.value));
  if (!hasValues) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "#9fb0c8",
        }}
      >
        No valid data for chart
      </div>
    );
  }

  if (chart_type === "pie") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={processedData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {processedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={ChartTooltip} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "scatter") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
          <XAxis
            dataKey="name"
            stroke="#9fb0c8"
            type="number"
            name={chart_config.x_axis}
          />
          <YAxis
            stroke="#9fb0c8"
            type="number"
            name={Array.isArray(chart_config.y_axis) ? chart_config.y_axis[0] : chart_config.y_axis}
            tickFormatter={(v: number) => formatAxisNumber(v)}
          />
          <Tooltip content={ChartTooltip} />
          <Scatter
            name={Array.isArray(chart_config.y_axis) ? chart_config.y_axis[0] : chart_config.y_axis}
            data={processedData}
            fill="#8b5cf6"
          />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "line") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={processedData} margin={{ top: 8, right: 12, left: 8, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
          <XAxis
            dataKey="name"
            stroke="#9fb0c8"
            angle={-30}
            textAnchor="end"
            height={38}
            tick={{ fontSize: processedData.length > 8 ? 10 : 11 }}
          />
          <YAxis
            stroke="#9fb0c8"
            tickFormatter={(v: number) => formatAxisNumber(v)}
            width={56}
          />
          <Tooltip content={ChartTooltip} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#8b5cf6"
            strokeWidth={2.5}
            dot={{ r: 3.5, stroke: "#8b5cf6", strokeWidth: 1.8, fill: "#0c0f14" }}
            activeDot={{ r: 4.5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  // Default to bar chart
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={processedData} margin={{ top: 8, right: 12, left: 8, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
        <XAxis
          dataKey="name"
          stroke="#9fb0c8"
          angle={-30}
          textAnchor="end"
          height={38}
          tick={{ fontSize: processedData.length > 8 ? 10 : 11 }}
        />
        <YAxis
          stroke="#9fb0c8"
          tickFormatter={(v: number) => formatAxisNumber(v)}
          width={56}
        />
        <Tooltip content={ChartTooltip} />
        <Bar dataKey="value" fill="#8b5cf6" radius={[6, 6, 0, 0]} maxBarSize={70} />
      </BarChart>
    </ResponsiveContainer>
  );
};
