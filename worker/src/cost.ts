// Reads the API pipeline's cost records: state/cost/<YYYY-MM>.jsonl in the content repo, one
// CostRecord per run (schema/cost-record.schema.json, written by pipeline record-cost).

import { isObject, parseJson } from "./encoding";

export const COST_KEY = /^state\/cost\/(\d{4}-\d{2})\.jsonl$/;

export function costKey(month: string): string {
  return `state/cost/${month}.jsonl`;
}

export interface MonthCost {
  spend: number;
  runs: number;
  // Field wire value to pages built (full and quick together).
  pages: Record<string, number>;
  // Field wire value to the part of the month's spend put on that field.
  costByField: Record<string, number>;
}

// What one run counts for: its reported cost when complete, and the larger of its reported cost
// and its per-run cap when incomplete, because a cut-off run's result can be missing or zeroed.
// This is the rule cost.build in pipeline/src/paperboy_pipeline/cost.py writes into spend_usd,
// and spend_usd is what budget-gate sums. schema/fixtures/cost/ holds records and totals both
// test suites check, so the two stay in agreement.
export function runSpend(record: { complete: boolean; total_cost_usd: number | null; budget_cap_usd: number }): number {
  const reported = record.total_cost_usd ?? 0;
  return record.complete ? reported : Math.max(reported, record.budget_cap_usd);
}

function byField(kinds: unknown): Record<string, number> | null {
  if (!isObject(kinds)) return null;
  const out: Record<string, number> = {};
  for (const kind of ["full", "quick"]) {
    const counts = kinds[kind];
    if (!isObject(counts)) return null;
    for (const [field, n] of Object.entries(counts)) {
      if (!Number.isInteger(n) || (n as number) < 0) return null;
      out[field] = (out[field] ?? 0) + (n as number);
    }
  }
  return out;
}

// Null when any line is not JSON or lacks a field this reads; the page then says the month's
// cost cannot be read, as budget-gate stops on an unreadable month rather than guess.
export function parseMonth(text: string): MonthCost | null {
  const month: MonthCost = { spend: 0, runs: 0, pages: {}, costByField: {} };
  for (const line of text.split("\n")) {
    if (line.trim() === "") continue;
    const record = parseJson(line);
    if (!isObject(record)) return null;
    const { complete, total_cost_usd, budget_cap_usd } = record;
    if (typeof complete !== "boolean" || typeof budget_cap_usd !== "number") return null;
    if (total_cost_usd !== null && typeof total_cost_usd !== "number") return null;
    const pages = byField(record.pages);
    const taken = byField(record.taken);
    if (!pages || !taken) return null;
    const spend = runSpend({ complete, total_cost_usd, budget_cap_usd });
    month.spend += spend;
    month.runs++;
    for (const [field, n] of Object.entries(pages)) month.pages[field] = (month.pages[field] ?? 0) + n;
    // The record has no cost per field, so a run's spend is split over the papers it was handed,
    // evenly per paper. A run handed nothing is in the month's total but on no field.
    const handed = Object.values(taken).reduce((a, b) => a + b, 0);
    if (handed > 0) {
      for (const [field, n] of Object.entries(taken)) month.costByField[field] = (month.costByField[field] ?? 0) + (spend * n) / handed;
    }
  }
  return month;
}
