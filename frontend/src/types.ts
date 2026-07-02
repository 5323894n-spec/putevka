export type Driver = {
  id: number;
  personnel_no: string;
  full_name: string;
  phone?: string;
  license_category?: string;
  license_no?: string;
  license_valid_until?: string;
  medical_valid_until?: string;
  column?: string;
  status: string;
};

export type Vehicle = {
  id: number;
  plate_no: string;
  garage_no: string;
  brand: string;
  model?: string;
  bus_type?: string;
  diagnostic_valid_until?: string;
  fuel_rate: number;
  fuel_balance: number;
  status: string;
  total_mileage: number;
};

export type Route = {
  id: number;
  number: string;
  name: string;
  service_type: string;
  planned_mileage: number;
  trips_count: number;
};

export type Run = {
  id: number;
  route_id: number;
  number: string;
  depot_out_time: string;
  work_start_time: string;
  work_end_time: string;
  depot_in_time: string;
  planned_mileage: number;
  planned_trips: number;
  required_bus_type?: string;
};

export type Duty = {
  id: number;
  duty_date: string;
  route_id: number;
  run_id: number;
  driver_id: number;
  vehicle_id: number;
  shift: number;
  planned_out_time: string;
  planned_in_time: string;
  planned_mileage: number;
  planned_trips: number;
  status: string;
  note?: string;
  driver: Driver;
  vehicle: Vehicle;
  route: Route;
  run: Run;
};

export type ScheduleEntry = {
  id: number;
  work_date: string;
  column?: string;
  route_id: number;
  run_id: number;
  driver_id: number;
  vehicle_id: number;
  shift: number;
  planned_out_time: string;
  planned_in_time: string;
  planned_mileage: number;
  planned_trips: number;
  status: string;
  note?: string;
  driver: Driver;
  vehicle: Vehicle;
  route: Route;
  run: Run;
};

export type Waybill = {
  id: number;
  number: string;
  issue_date: string;
  work_date: string;
  valid_from: string;
  valid_to: string;
  organization: string;
  planned_out_time: string;
  planned_in_time: string;
  actual_out_time?: string;
  actual_in_time?: string;
  odometer_out: number;
  odometer_in: number;
  mileage: number;
  fuel_out: number;
  fuel_issued: number;
  fuel_in: number;
  norm_fuel: number;
  fact_fuel: number;
  medical_check: string;
  technical_check: string;
  dispatcher_note?: string;
  status: string;
  responsible?: string;
  driver: Driver;
  vehicle: Vehicle;
  route: Route;
  run: Run;
};

export type Warning = {
  level: "critical" | "warning" | "info";
  message: string;
  entity: string;
  entity_id?: number;
};
