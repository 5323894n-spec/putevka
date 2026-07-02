from datetime import date, time

from pydantic import BaseModel, ConfigDict

from .models import DriverStatus, VehicleStatus, WaybillStatus


class DriverIn(BaseModel):
    personnel_no: str
    full_name: str
    birth_date: date | None = None
    phone: str | None = None
    license_category: str | None = None
    license_no: str | None = None
    license_valid_until: date | None = None
    snils: str
    medical_certificate: str | None = None
    medical_valid_until: date | None = None
    column: str | None = None
    work_schedule: str | None = None
    status: DriverStatus = DriverStatus.WORKING
    note: str | None = None


class DriverOut(DriverIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class VehicleIn(BaseModel):
    plate_no: str
    garage_no: str
    brand: str
    model: str | None = None
    vin: str | None = None
    year: int | None = None
    bus_type: str | None = None
    capacity: int | None = None
    sts_no: str | None = None
    diagnostic_card_no: str | None = None
    diagnostic_valid_until: date | None = None
    fuel_rate: float = 0
    fuel_type: str = "ДТ"
    fuel_balance: float = 0
    status: VehicleStatus = VehicleStatus.RESERVE
    total_mileage: float = 0
    period_start_mileage: float = 0
    note: str | None = None


class VehicleOut(VehicleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RouteIn(BaseModel):
    number: str
    name: str
    service_type: str = "городской"
    distance_km: float = 0
    trips_count: int = 0
    start_time: time | None = None
    end_time: time | None = None
    checkpoints: str | None = None
    planned_mileage: float = 0
    note: str | None = None


class RouteOut(RouteIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RunIn(BaseModel):
    route_id: int
    number: str
    depot_out_time: time
    work_start_time: time
    work_end_time: time
    depot_in_time: time
    planned_mileage: float = 0
    planned_trips: int = 0
    required_bus_type: str | None = None


class RunOut(RunIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DutyIn(BaseModel):
    duty_date: date
    route_id: int
    run_id: int
    driver_id: int
    vehicle_id: int
    shift: int = 1
    planned_out_time: time
    planned_in_time: time
    planned_mileage: float = 0
    planned_trips: int = 0
    status: str = "план"
    note: str | None = None


class DutyOut(DutyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    driver: DriverOut
    vehicle: VehicleOut
    route: RouteOut
    run: RunOut


class ScheduleEntryIn(BaseModel):
    work_date: date
    column: str | None = None
    route_id: int
    run_id: int
    driver_id: int
    vehicle_id: int
    shift: int = 1
    planned_out_time: time
    planned_in_time: time
    planned_mileage: float = 0
    planned_trips: int = 0
    status: str = "план"
    note: str | None = None


class ScheduleEntryOut(ScheduleEntryIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    driver: DriverOut
    vehicle: VehicleOut
    route: RouteOut
    run: RunOut


class WaybillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: str
    issue_date: date
    work_date: date
    valid_from: date
    valid_to: date
    organization: str
    planned_out_time: time
    planned_in_time: time
    actual_out_time: time | None = None
    actual_in_time: time | None = None
    odometer_out: float
    odometer_in: float
    mileage: float
    fuel_out: float
    fuel_issued: float
    fuel_in: float
    norm_fuel: float
    fact_fuel: float
    medical_check: str
    technical_check: str
    dispatcher_note: str | None = None
    status: WaybillStatus
    responsible: str | None = None
    driver: DriverOut
    vehicle: VehicleOut
    route: RouteOut
    run: RunOut


class WaybillCloseIn(BaseModel):
    actual_out_time: time | None = None
    actual_in_time: time | None = None
    odometer_in: float
    fuel_issued: float = 0
    fuel_in: float
    dispatcher_note: str | None = None


class WarningOut(BaseModel):
    level: str
    message: str
    entity: str
    entity_id: int | None = None
