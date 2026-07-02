from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class DriverStatus(StrEnum):
    WORKING = "работает"
    VACATION = "отпуск"
    SICK = "больничный"
    FIRED = "уволен"


class VehicleStatus(StrEnum):
    LINE = "на линии"
    REPAIR = "ремонт"
    RESERVE = "резерв"
    RETIRED = "списан"


class WaybillStatus(StrEnum):
    CREATED = "создан"
    ISSUED = "выдан"
    CLOSED = "закрыт"
    CANCELLED = "аннулирован"


class UserRole(StrEnum):
    ADMIN = "Администратор"
    DISPATCHER = "Диспетчер"
    DUTY_PLANNER = "Нарядчик"
    MECHANIC = "Механик"
    MEDIC = "Медицинский работник"
    ACCOUNTANT = "Бухгалтер"
    MANAGER = "Руководитель"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DISPATCHER)
    is_active: Mapped[bool] = mapped_column(default=True)


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    personnel_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(32))
    license_category: Mapped[str | None] = mapped_column(String(32))
    license_no: Mapped[str | None] = mapped_column(String(64))
    license_valid_until: Mapped[date | None] = mapped_column(Date)
    medical_certificate: Mapped[str | None] = mapped_column(String(128))
    medical_valid_until: Mapped[date | None] = mapped_column(Date)
    column: Mapped[str | None] = mapped_column(String(32))
    work_schedule: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[DriverStatus] = mapped_column(Enum(DriverStatus), default=DriverStatus.WORKING)
    note: Mapped[str | None] = mapped_column(Text)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    garage_no: Mapped[str] = mapped_column(String(32), index=True)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    vin: Mapped[str | None] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    bus_type: Mapped[str | None] = mapped_column(String(64))
    capacity: Mapped[int | None] = mapped_column(Integer)
    sts_no: Mapped[str | None] = mapped_column(String(64))
    diagnostic_card_no: Mapped[str | None] = mapped_column(String(64))
    diagnostic_valid_until: Mapped[date | None] = mapped_column(Date)
    fuel_rate: Mapped[float] = mapped_column(Float, default=0)
    fuel_type: Mapped[str] = mapped_column(String(32), default="ДТ")
    fuel_balance: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[VehicleStatus] = mapped_column(Enum(VehicleStatus), default=VehicleStatus.RESERVE)
    total_mileage: Mapped[float] = mapped_column(Float, default=0)
    period_start_mileage: Mapped[float] = mapped_column(Float, default=0)
    note: Mapped[str | None] = mapped_column(Text)


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    service_type: Mapped[str] = mapped_column(String(64), default="городской")
    distance_km: Mapped[float] = mapped_column(Float, default=0)
    trips_count: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    checkpoints: Mapped[str | None] = mapped_column(Text)
    planned_mileage: Mapped[float] = mapped_column(Float, default=0)
    note: Mapped[str | None] = mapped_column(Text)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("route_id", "number", name="uq_run_route_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    number: Mapped[str] = mapped_column(String(32))
    depot_out_time: Mapped[time] = mapped_column(Time)
    work_start_time: Mapped[time] = mapped_column(Time)
    work_end_time: Mapped[time] = mapped_column(Time)
    depot_in_time: Mapped[time] = mapped_column(Time)
    planned_mileage: Mapped[float] = mapped_column(Float, default=0)
    planned_trips: Mapped[int] = mapped_column(Integer, default=0)
    required_bus_type: Mapped[str | None] = mapped_column(String(64))

    route: Mapped[Route] = relationship()


class Duty(Base):
    __tablename__ = "duties"

    id: Mapped[int] = mapped_column(primary_key=True)
    duty_date: Mapped[date] = mapped_column(Date, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    shift: Mapped[int] = mapped_column(Integer, default=1)
    planned_out_time: Mapped[time] = mapped_column(Time)
    planned_in_time: Mapped[time] = mapped_column(Time)
    planned_mileage: Mapped[float] = mapped_column(Float, default=0)
    planned_trips: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="план")
    note: Mapped[str | None] = mapped_column(Text)

    route: Mapped[Route] = relationship()
    run: Mapped[Run] = relationship()
    driver: Mapped[Driver] = relationship()
    vehicle: Mapped[Vehicle] = relationship()


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"
    __table_args__ = (UniqueConstraint("work_date", "driver_id", "shift", name="uq_schedule_driver_date_shift"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    column: Mapped[str | None] = mapped_column(String(32))
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    shift: Mapped[int] = mapped_column(Integer, default=1)
    planned_out_time: Mapped[time] = mapped_column(Time)
    planned_in_time: Mapped[time] = mapped_column(Time)
    planned_mileage: Mapped[float] = mapped_column(Float, default=0)
    planned_trips: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="план")
    note: Mapped[str | None] = mapped_column(Text)

    route: Mapped[Route] = relationship()
    run: Mapped[Run] = relationship()
    driver: Mapped[Driver] = relationship()
    vehicle: Mapped[Vehicle] = relationship()


class NumberSequence(Base):
    __tablename__ = "number_sequences"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(255), default="Основная")
    year: Mapped[int] = mapped_column(Integer, index=True)
    prefix: Mapped[str] = mapped_column(String(32), default="ПЛ")
    next_value: Mapped[int] = mapped_column(Integer, default=1)


class Waybill(Base):
    __tablename__ = "waybills"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date] = mapped_column(Date)
    organization: Mapped[str] = mapped_column(String(255), default="ВЕРХНЕВОЛЖСКОЕ АТП ООО")
    duty_id: Mapped[int | None] = mapped_column(ForeignKey("duties.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    planned_out_time: Mapped[time] = mapped_column(Time)
    planned_in_time: Mapped[time] = mapped_column(Time)
    actual_out_time: Mapped[time | None] = mapped_column(Time)
    actual_in_time: Mapped[time | None] = mapped_column(Time)
    odometer_out: Mapped[float] = mapped_column(Float, default=0)
    odometer_in: Mapped[float] = mapped_column(Float, default=0)
    mileage: Mapped[float] = mapped_column(Float, default=0)
    fuel_out: Mapped[float] = mapped_column(Float, default=0)
    fuel_issued: Mapped[float] = mapped_column(Float, default=0)
    fuel_in: Mapped[float] = mapped_column(Float, default=0)
    norm_fuel: Mapped[float] = mapped_column(Float, default=0)
    fact_fuel: Mapped[float] = mapped_column(Float, default=0)
    medical_check: Mapped[str] = mapped_column(String(64), default="допущен")
    technical_check: Mapped[str] = mapped_column(String(64), default="исправен")
    dispatcher_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[WaybillStatus] = mapped_column(Enum(WaybillStatus), default=WaybillStatus.CREATED)
    responsible: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    duty: Mapped[Duty | None] = relationship()
    driver: Mapped[Driver] = relationship()
    vehicle: Mapped[Vehicle] = relationship()
    route: Mapped[Route] = relationship()
    run: Mapped[Run] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(128), default="system")
    action: Mapped[str] = mapped_column(String(128))
    entity: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    details: Mapped[str | None] = mapped_column(Text)
