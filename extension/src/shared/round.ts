import type { WatchlistTask } from "./types";

export function buildRoundPlan(tasks: WatchlistTask[]): WatchlistTask[] {
  return tasks.filter((task) => Boolean(task.url)).slice(0, 5);
}
