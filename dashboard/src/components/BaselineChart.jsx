"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { colors } from "../lib/colors";
import { formatBn } from "../lib/formatters";

// Modelled is the brand teal; official is the neutral reference. They sit far
// apart in lightness, so the pair stays distinct under colour-vision deficiency.
const MODEL_COLOR = colors.primary[600];
const OFFICIAL_COLOR = colors.border.dark;

const BAR_SIZE = 14;
const BAR_GAP = 2;

// Axis labels only; the table below carries the full scheme names.
const SHORT_LABELS = {
  universal: "Universal 15h",
  extended: "Working-parent",
  targeted: "2-year-old offer",
  tfc: "Tax-Free Childcare",
};

const MEASURES = {
  spending: {
    label: "Spending (£bn)",
    model: (row) => row.model_spending_bn,
    official: (row) => row.official_spending_bn,
    scale: 1,
    tick: (value) => (Number(value) === 0 ? "0" : `£${Number(value).toFixed(1)}bn`),
    exact: (value) => formatBn(value),
  },
  children: {
    label: "Children (m)",
    model: (row) => row.model_caseload,
    official: (row) => row.official_caseload,
    scale: 1e6,
    tick: (value) => (Number(value) === 0 ? "0" : `${Number(value).toFixed(1)}m`),
    exact: (value) => Math.round(value * 1e6).toLocaleString("en-GB"),
  },
};

function isNumber(value) {
  return value !== null && value !== undefined && Number.isFinite(Number(value));
}

function formatRatio(ratio) {
  return `${ratio.toFixed(2)}×`;
}

// The ratio sits once per pair, just past the longer of the two bars, centred
// between them. Each bar's label renders only when that bar is the longer one.
function ratioLabel(isModel) {
  function RatioLabel({ x, y, width, height, index, data }) {
    const row = data[index];
    if (!row || row.ratio === null) return null;
    const modelIsLonger = row.modelled >= row.official;
    if (isModel !== modelIsLonger) return null;
    const centreY = isModel ? y + height + BAR_GAP / 2 : y - BAR_GAP / 2;
    return (
      <text
        x={x + width + 6}
        y={centreY}
        dominantBaseline="central"
        fontSize={12}
        fontWeight={600}
        fill={colors.gray[700]}
      >
        {formatRatio(row.ratio)}
      </text>
    );
  }
  return RatioLabel;
}

function ChartTooltip({ active, payload, measure }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-sm">
      <div className="mb-1 font-semibold text-slate-900">{row.fullName}</div>
      <div className="flex items-center gap-2 text-slate-700">
        <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: MODEL_COLOR }} />
        Modelled: <span className="tabular-nums">{measure.exact(row.modelled)}</span>
      </div>
      <div className="flex items-center gap-2 text-slate-700">
        <span
          className="inline-block h-2.5 w-2.5 rounded-sm"
          style={{ background: OFFICIAL_COLOR }}
        />
        Official: <span className="tabular-nums">{measure.exact(row.official)}</span>
      </div>
      {row.ratio !== null ? (
        <div className="mt-1 text-slate-500">
          Modelled / official: <span className="tabular-nums">{formatRatio(row.ratio)}</span>
        </div>
      ) : null}
    </div>
  );
}

export default function BaselineChart({ programmes, children }) {
  const [measureKey, setMeasureKey] = useState("spending");
  const measure = MEASURES[measureKey];

  const rows = programmes
    .filter((row) => isNumber(measure.model(row)) || isNumber(measure.official(row)))
    .map((row) => {
      const model = measure.model(row);
      const official = measure.official(row);
      const modelled = isNumber(model) ? Number(model) / measure.scale : 0;
      const officialValue = isNumber(official) ? Number(official) / measure.scale : 0;
      return {
        key: row.programme,
        name: SHORT_LABELS[row.programme] || row.label,
        fullName: row.label,
        modelled,
        official: officialValue,
        ratio:
          isNumber(model) && isNumber(official) && Number(official) !== 0
            ? Number(model) / Number(official)
            : null,
      };
    });

  const height = rows.length * (BAR_SIZE * 2 + BAR_GAP + 20) + 40;

  return (
    <div className="mb-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-slate-900">
          Modelled against official, by scheme
        </h3>
        <div
          role="group"
          aria-label="Measure"
          className="inline-flex rounded-lg border border-slate-200 p-0.5 text-xs font-semibold"
        >
          {Object.entries(MEASURES).map(([key, option]) => {
            const selected = key === measureKey;
            return (
              <button
                key={key}
                type="button"
                aria-pressed={selected}
                onClick={() => setMeasureKey(key)}
                className={`rounded-md px-3 py-1.5 transition-colors ${
                  selected
                    ? "bg-[color:var(--pe-color-primary-600)] text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mb-2 flex flex-wrap gap-4 text-xs text-slate-600">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: MODEL_COLOR }} />
          Modelled
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-sm"
            style={{ background: OFFICIAL_COLOR }}
          />
          Official
        </span>
        <span className="text-slate-500">Label: modelled ÷ official</span>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={rows}
          layout="vertical"
          barSize={BAR_SIZE}
          barGap={BAR_GAP}
          margin={{ left: 0, right: 48, top: 4, bottom: 4 }}
        >
          <CartesianGrid horizontal={false} stroke={colors.border.light} />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: colors.gray[500] }}
            tickFormatter={measure.tick}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={112}
            tick={{ fontSize: 12, fill: colors.gray[700] }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: colors.gray[50] }}
            content={<ChartTooltip measure={measure} />}
          />
          <Bar
            dataKey="modelled"
            name="Modelled"
            fill={MODEL_COLOR}
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          >
            <LabelList content={(props) => ratioLabel(true)({ ...props, data: rows })} />
          </Bar>
          <Bar
            dataKey="official"
            name="Official"
            fill={OFFICIAL_COLOR}
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          >
            <LabelList content={(props) => ratioLabel(false)({ ...props, data: rows })} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {children ? <div className="mt-5 border-t border-slate-200 pt-4">{children}</div> : null}
    </div>
  );
}
