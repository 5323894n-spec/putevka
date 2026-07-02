from datetime import date, time

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, get_db
from .exports import duties_workbook, single_waybill_workbook, waybills_workbook
from .models import Driver, Duty, Route, Run, ScheduleEntry, Vehicle, Waybill, WaybillStatus
from .schemas import DriverIn, DriverOut, DutyIn, DutyOut, RouteIn, RouteOut, RunIn, RunOut, ScheduleEntryIn, ScheduleEntryOut, VehicleIn, VehicleOut, WarningOut, WaybillCloseIn, WaybillOut
from .services import build_warnings, close_waybill, create_waybill_from_duty


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Путевые листы пассажирского транспорта", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def seed(db: Session) -> None:
    if db.scalar(select(Driver).limit(1)):
        return
    driver = Driver(
        personnel_no="01120",
        full_name="Сушков Сергей Борисович",
        license_category="D",
        license_no="99 15 571371",
        license_valid_until=date(2028, 2, 14),
        medical_certificate="МС-001",
        medical_valid_until=date(2027, 7, 2),
        column="АК3",
    )
    vehicle = Vehicle(
        plate_no="О778СР69",
        garage_no="10269",
        brand="ЛиАЗ",
        model="429260",
        bus_type="городской",
        capacity=72,
        diagnostic_card_no="ДК-10269",
        diagnostic_valid_until=date(2027, 7, 2),
        fuel_rate=43,
        fuel_balance=200,
        total_mileage=125430,
    )
    route = Route(number="10", name="Ж.Д БОЛЬНИЦА - ХИМИНСТИТУТ", service_type="городской", planned_mileage=180, trips_count=10)
    db.add_all([driver, vehicle, route])
    db.flush()
    run = Run(route_id=route.id, number="801", depot_out_time=time(4, 24), work_start_time=time(4, 40), work_end_time=time(13, 10), depot_in_time=time(13, 24), planned_mileage=180, planned_trips=10, required_bus_type="городской")
    db.add(run)
    db.flush()
    db.add(Duty(duty_date=date.today(), route_id=route.id, run_id=run.id, driver_id=driver.id, vehicle_id=vehicle.id, shift=1, planned_out_time=time(4, 24), planned_in_time=time(13, 24), planned_mileage=180, planned_trips=10))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    with next(get_db()) as db:
        seed(db)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def create_entity(db: Session, model, payload):
    entity = model(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@app.get("/drivers", response_model=list[DriverOut])
def list_drivers(db: Session = Depends(get_db)):
    return db.scalars(select(Driver).order_by(Driver.full_name)).all()


@app.post("/drivers", response_model=DriverOut)
def create_driver(payload: DriverIn, db: Session = Depends(get_db)):
    return create_entity(db, Driver, payload)


@app.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.scalars(select(Vehicle).order_by(Vehicle.garage_no)).all()


@app.post("/vehicles", response_model=VehicleOut)
def create_vehicle(payload: VehicleIn, db: Session = Depends(get_db)):
    return create_entity(db, Vehicle, payload)


@app.get("/routes", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)):
    return db.scalars(select(Route).order_by(Route.number)).all()


@app.post("/routes", response_model=RouteOut)
def create_route(payload: RouteIn, db: Session = Depends(get_db)):
    return create_entity(db, Route, payload)


@app.get("/runs", response_model=list[RunOut])
def list_runs(db: Session = Depends(get_db)):
    return db.scalars(select(Run).order_by(Run.number)).all()


@app.post("/runs", response_model=RunOut)
def create_run(payload: RunIn, db: Session = Depends(get_db)):
    return create_entity(db, Run, payload)


@app.get("/duties", response_model=list[DutyOut])
def list_duties(duty_date: date | None = None, db: Session = Depends(get_db)):
    query = select(Duty).options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run)).order_by(Duty.planned_out_time)
    if duty_date:
        query = query.where(Duty.duty_date == duty_date)
    return db.scalars(query).all()


@app.post("/duties", response_model=DutyOut)
def create_duty(payload: DutyIn, db: Session = Depends(get_db)):
    duty = Duty(**payload.model_dump())
    db.add(duty)
    db.commit()
    return db.scalar(select(Duty).options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run)).where(Duty.id == duty.id))


@app.get("/schedule", response_model=list[ScheduleEntryOut])
def list_schedule(year: int, month: int, column: str | None = None, db: Session = Depends(get_db)):
    query = (
        select(ScheduleEntry)
        .options(joinedload(ScheduleEntry.driver), joinedload(ScheduleEntry.vehicle), joinedload(ScheduleEntry.route), joinedload(ScheduleEntry.run))
        .where(ScheduleEntry.work_date >= date(year, month, 1))
        .order_by(ScheduleEntry.work_date, ScheduleEntry.planned_out_time)
    )
    if month == 12:
        query = query.where(ScheduleEntry.work_date < date(year + 1, 1, 1))
    else:
        query = query.where(ScheduleEntry.work_date < date(year, month + 1, 1))
    if column:
        query = query.where(ScheduleEntry.column == column)
    return db.scalars(query).all()


@app.post("/schedule", response_model=ScheduleEntryOut)
def create_schedule_entry(payload: ScheduleEntryIn, db: Session = Depends(get_db)):
    entry = ScheduleEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    return db.scalar(
        select(ScheduleEntry)
        .options(joinedload(ScheduleEntry.driver), joinedload(ScheduleEntry.vehicle), joinedload(ScheduleEntry.route), joinedload(ScheduleEntry.run))
        .where(ScheduleEntry.id == entry.id)
    )


@app.post("/duties/from-schedule/{work_date}", response_model=list[DutyOut])
def create_duties_from_schedule(work_date: date, db: Session = Depends(get_db)):
    entries = db.scalars(
        select(ScheduleEntry)
        .options(joinedload(ScheduleEntry.driver), joinedload(ScheduleEntry.vehicle), joinedload(ScheduleEntry.route), joinedload(ScheduleEntry.run))
        .where(ScheduleEntry.work_date == work_date)
        .order_by(ScheduleEntry.planned_out_time)
    ).all()
    for entry in entries:
        existing = db.scalar(
            select(Duty).where(
                Duty.duty_date == entry.work_date,
                Duty.driver_id == entry.driver_id,
                Duty.vehicle_id == entry.vehicle_id,
                Duty.run_id == entry.run_id,
                Duty.shift == entry.shift,
            )
        )
        if existing:
            continue
        db.add(
            Duty(
                duty_date=entry.work_date,
                route_id=entry.route_id,
                run_id=entry.run_id,
                driver_id=entry.driver_id,
                vehicle_id=entry.vehicle_id,
                shift=entry.shift,
                planned_out_time=entry.planned_out_time,
                planned_in_time=entry.planned_in_time,
                planned_mileage=entry.planned_mileage,
                planned_trips=entry.planned_trips,
                status="из графика",
                note=entry.note,
            )
        )
    db.commit()
    return db.scalars(
        select(Duty)
        .options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run))
        .where(Duty.duty_date == work_date)
        .order_by(Duty.planned_out_time)
    ).all()


@app.get("/warnings", response_model=list[WarningOut])
def warnings(target_date: date | None = None, db: Session = Depends(get_db)):
    return build_warnings(db, target_date or date.today())


@app.post("/waybills/from-duty/{duty_id}", response_model=WaybillOut)
def generate_waybill(duty_id: int, db: Session = Depends(get_db)):
    duty = db.scalar(select(Duty).options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run)).where(Duty.id == duty_id))
    if not duty:
        raise HTTPException(status_code=404, detail="Наряд не найден")
    waybill = create_waybill_from_duty(db, duty)
    db.commit()
    return db.scalar(select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run)).where(Waybill.id == waybill.id))


@app.post("/waybills/from-date/{work_date}", response_model=list[WaybillOut])
def generate_waybills_for_date(work_date: date, db: Session = Depends(get_db)):
    duties = db.scalars(select(Duty).options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run)).where(Duty.duty_date == work_date)).all()
    waybills = [create_waybill_from_duty(db, duty) for duty in duties]
    db.commit()
    ids = [item.id for item in waybills]
    return db.scalars(select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run)).where(Waybill.id.in_(ids))).all()


@app.get("/waybills", response_model=list[WaybillOut])
def list_waybills(work_date: date | None = None, status: WaybillStatus | None = None, db: Session = Depends(get_db)):
    query = select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run)).order_by(Waybill.number)
    if work_date:
        query = query.where(Waybill.work_date == work_date)
    if status:
        query = query.where(Waybill.status == status)
    return db.scalars(query).all()


@app.patch("/waybills/{waybill_id}/close", response_model=WaybillOut)
def close(waybill_id: int, payload: WaybillCloseIn, db: Session = Depends(get_db)):
    waybill = db.scalar(select(Waybill).options(joinedload(Waybill.vehicle), joinedload(Waybill.driver), joinedload(Waybill.route), joinedload(Waybill.run)).where(Waybill.id == waybill_id))
    if not waybill:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
    close_waybill(waybill, payload.odometer_in, payload.fuel_issued, payload.fuel_in)
    waybill.actual_out_time = payload.actual_out_time
    waybill.actual_in_time = payload.actual_in_time
    waybill.dispatcher_note = payload.dispatcher_note
    db.commit()
    db.refresh(waybill)
    return waybill


@app.patch("/waybills/{waybill_id}/cancel", response_model=WaybillOut)
def cancel(waybill_id: int, db: Session = Depends(get_db)):
    waybill = db.scalar(select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run)).where(Waybill.id == waybill_id))
    if not waybill:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
    waybill.status = WaybillStatus.CANCELLED
    db.commit()
    return waybill


@app.get("/exports/duties.xlsx")
def export_duties(duty_date: date | None = None, db: Session = Depends(get_db)):
    query = select(Duty).options(joinedload(Duty.driver), joinedload(Duty.vehicle), joinedload(Duty.route), joinedload(Duty.run))
    if duty_date:
        query = query.where(Duty.duty_date == duty_date)
    content = duties_workbook(db.scalars(query).all())
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=duties.xlsx"})


@app.get("/exports/waybills.xlsx")
def export_waybills(db: Session = Depends(get_db)):
    query = select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run))
    content = waybills_workbook(db.scalars(query).all())
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=waybills.xlsx"})


@app.get("/exports/waybills/{waybill_id}.xlsx")
def export_waybill(waybill_id: int, db: Session = Depends(get_db)):
    waybill = db.scalar(select(Waybill).options(joinedload(Waybill.driver), joinedload(Waybill.vehicle), joinedload(Waybill.route), joinedload(Waybill.run)).where(Waybill.id == waybill_id))
    if not waybill:
        raise HTTPException(status_code=404, detail="Путевой лист не найден")
    content = single_waybill_workbook(waybill)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={waybill.number}.xlsx"})
