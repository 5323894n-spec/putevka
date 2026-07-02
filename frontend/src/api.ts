import type { Driver, Duty, Route, Run, ScheduleEntry, Vehicle, Warning, Waybill } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  drivers: () => request<Driver[]>("/drivers"),
  createDriver: (payload: unknown) => request<Driver>("/drivers", { method: "POST", body: JSON.stringify(payload) }),
  vehicles: () => request<Vehicle[]>("/vehicles"),
  createVehicle: (payload: unknown) => request<Vehicle>("/vehicles", { method: "POST", body: JSON.stringify(payload) }),
  routes: () => request<Route[]>("/routes"),
  createRoute: (payload: unknown) => request<Route>("/routes", { method: "POST", body: JSON.stringify(payload) }),
  runs: () => request<Run[]>("/runs"),
  createRun: (payload: unknown) => request<Run>("/runs", { method: "POST", body: JSON.stringify(payload) }),
  duties: (date?: string) => request<Duty[]>(`/duties${date ? `?duty_date=${date}` : ""}`),
  createDuty: (payload: unknown) => request<Duty>("/duties", { method: "POST", body: JSON.stringify(payload) }),
  schedule: (year: number, month: number) => request<ScheduleEntry[]>(`/schedule?year=${year}&month=${month}`),
  createScheduleEntry: (payload: unknown) => request<ScheduleEntry>("/schedule", { method: "POST", body: JSON.stringify(payload) }),
  createDutiesFromSchedule: (date: string) => request<Duty[]>(`/duties/from-schedule/${date}`, { method: "POST" }),
  waybills: (date?: string) => request<Waybill[]>(`/waybills${date ? `?work_date=${date}` : ""}`),
  warnings: (date?: string) => request<Warning[]>(`/warnings${date ? `?target_date=${date}` : ""}`),
  createWaybillsForDate: (date: string) => request<Waybill[]>(`/waybills/from-date/${date}`, { method: "POST" }),
  closeWaybill: (id: number, payload: unknown) => request<Waybill>(`/waybills/${id}/close`, { method: "PATCH", body: JSON.stringify(payload) }),
  exportUrl: (path: string) => `${API_URL}${path}`,
};
