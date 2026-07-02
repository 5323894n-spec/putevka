from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Driver, Duty, NumberSequence, Vehicle, VehicleStatus, Waybill, WaybillStatus


def allocate_waybill_number(db: Session, organization: str, work_date: date) -> str:
    sequence = db.scalar(
        select(NumberSequence).where(
            NumberSequence.organization == organization,
            NumberSequence.year == work_date.year,
        )
    )
    if sequence is None:
        sequence = NumberSequence(organization=organization, year=work_date.year, prefix="ПЛ", next_value=1)
        db.add(sequence)
        db.flush()
    number = f"{sequence.prefix}-{sequence.year}-{sequence.next_value:06d}"
    sequence.next_value += 1
    return number


def build_warnings(db: Session, target_date: date) -> list[dict]:
    warnings: list[dict] = []
    for driver in db.scalars(select(Driver)).all():
        if driver.status.value != "работает":
            continue
        if driver.license_valid_until and driver.license_valid_until < target_date:
            warnings.append({"level": "critical", "message": "Истек срок водительского удостоверения", "entity": "driver", "entity_id": driver.id})
        if driver.medical_valid_until and driver.medical_valid_until < target_date:
            warnings.append({"level": "critical", "message": "Истек срок медсправки", "entity": "driver", "entity_id": driver.id})
    for vehicle in db.scalars(select(Vehicle)).all():
        if vehicle.diagnostic_valid_until and vehicle.diagnostic_valid_until < target_date:
            warnings.append({"level": "critical", "message": "Истекла диагностическая карта", "entity": "vehicle", "entity_id": vehicle.id})
        if vehicle.status == VehicleStatus.REPAIR:
            warnings.append({"level": "warning", "message": "Автобус находится в ремонте", "entity": "vehicle", "entity_id": vehicle.id})
        if vehicle.fuel_balance < 0:
            warnings.append({"level": "critical", "message": "Отрицательный остаток топлива", "entity": "vehicle", "entity_id": vehicle.id})
    duplicate_drivers = db.execute(
        select(Duty.driver_id, func.count(Duty.id)).where(Duty.duty_date == target_date).group_by(Duty.driver_id).having(func.count(Duty.id) > 1)
    ).all()
    for driver_id, _ in duplicate_drivers:
        warnings.append({"level": "warning", "message": "Водитель назначен более одного раза за день", "entity": "driver", "entity_id": driver_id})
    duplicate_vehicles = db.execute(
        select(Duty.vehicle_id, func.count(Duty.id)).where(Duty.duty_date == target_date).group_by(Duty.vehicle_id).having(func.count(Duty.id) > 1)
    ).all()
    for vehicle_id, _ in duplicate_vehicles:
        warnings.append({"level": "warning", "message": "Автобус назначен более одного раза за день", "entity": "vehicle", "entity_id": vehicle_id})
    return warnings


def create_waybill_from_duty(db: Session, duty: Duty, organization: str = "ВЕРХНЕВОЛЖСКОЕ АТП ООО") -> Waybill:
    existing = db.scalar(select(Waybill).where(Waybill.duty_id == duty.id, Waybill.status != WaybillStatus.CANCELLED))
    if existing:
        return existing
    vehicle = duty.vehicle
    mileage = duty.planned_mileage or duty.run.planned_mileage
    waybill = Waybill(
        number=allocate_waybill_number(db, organization, duty.duty_date),
        issue_date=date.today(),
        work_date=duty.duty_date,
        valid_from=duty.duty_date,
        valid_to=duty.duty_date,
        organization=organization,
        duty_id=duty.id,
        driver_id=duty.driver_id,
        vehicle_id=duty.vehicle_id,
        route_id=duty.route_id,
        run_id=duty.run_id,
        planned_out_time=duty.planned_out_time,
        planned_in_time=duty.planned_in_time,
        odometer_out=vehicle.total_mileage,
        odometer_in=vehicle.total_mileage + mileage,
        mileage=mileage,
        fuel_out=vehicle.fuel_balance,
        fuel_issued=0,
        fuel_in=max(vehicle.fuel_balance - (mileage * vehicle.fuel_rate / 100), 0),
        norm_fuel=mileage * vehicle.fuel_rate / 100,
        fact_fuel=0,
        responsible="Диспетчер",
    )
    db.add(waybill)
    return waybill


def close_waybill(waybill: Waybill, odometer_in: float, fuel_issued: float, fuel_in: float) -> None:
    waybill.odometer_in = odometer_in
    waybill.fuel_issued = fuel_issued
    waybill.fuel_in = fuel_in
    waybill.mileage = max(odometer_in - waybill.odometer_out, 0)
    waybill.norm_fuel = waybill.mileage * waybill.vehicle.fuel_rate / 100
    waybill.fact_fuel = waybill.fuel_out + fuel_issued - fuel_in
    waybill.status = WaybillStatus.CLOSED
    waybill.vehicle.total_mileage = odometer_in
    waybill.vehicle.fuel_balance = fuel_in

