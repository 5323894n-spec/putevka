from pathlib import Path
from shutil import copyfile
from tempfile import NamedTemporaryFile

from .models import Waybill


BASE_DIR = Path(__file__).resolve().parents[2]
WAYBILL_TEMPLATE = BASE_DIR / "templates" / "путевой лист.xls"


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _date(value) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


def _time(value) -> str:
    return value.strftime("%H:%M") if value else ""


def _num(value: float | int | None) -> float | int | str:
    if value is None:
        return ""
    return round(value, 2)


def _set(sheet, row: int, col: int, value: object) -> None:
    sheet.Cells(row, col).Value = value


def render_waybill_xls_from_template(waybill: Waybill) -> bytes:
    if not WAYBILL_TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {WAYBILL_TEMPLATE}")

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("pywin32 is required to render the original .xls template") from exc

    with NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
        output_path = Path(tmp.name)
    copyfile(WAYBILL_TEMPLATE, output_path)

    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        try:
            workbook = excel.Workbooks.Open(str(output_path))
        except Exception:
            protected = excel.ProtectedViewWindows.Open(str(output_path))
            workbook = protected.Edit()
        sheet = workbook.Worksheets(1)

        bus_name = f"{waybill.vehicle.brand} {waybill.vehicle.model or ''}".strip()
        period = f"{_date(waybill.valid_from)} - {_date(waybill.valid_to)}"
        route_name = f"{waybill.route.number} {waybill.route.name}".strip()
        driver = waybill.driver
        vehicle = waybill.vehicle

        # Header and organization block. Coordinates are based on the uploaded
        # original form and preserve its merged cells and formatting.
        _set(sheet, 1, 5, driver.column or "")
        _set(sheet, 1, 27, vehicle.garage_no)
        _set(sheet, 1, 139, vehicle.plate_no)
        _set(sheet, 1, 199, _num(vehicle.fuel_rate))
        _set(sheet, 6, 115, waybill.number)
        _set(sheet, 7, 17, waybill.organization)
        _set(sheet, 7, 57, period)
        _set(sheet, 8, 74, bus_name)
        _set(sheet, 9, 89, vehicle.plate_no)
        _set(sheet, 9, 122, vehicle.garage_no)
        _set(sheet, 10, 58, f"Вид сообщения: {waybill.route.service_type.title()}")

        # Driver block.
        for row in (16, 18):
            _set(sheet, row, 57, driver.full_name)
            _set(sheet, row, 96, driver.personnel_no)
            _set(sheet, row, 111, driver.license_no or "")
            _set(sheet, row, 124, "")
        _set(sheet, 17, 57, "")
        _set(sheet, 19, 57, "")

        # Route and trip assignment.
        _set(sheet, 22, 58, route_name)
        _set(sheet, 23, 58, "Вид перевозки: Регулярные перевозки пассажиров и багажа")
        _set(sheet, 24, 58, f"{waybill.route.number} {waybill.route.name}")
        _set(sheet, 24, 118, _num(vehicle.fuel_rate))
        _set(sheet, 27, 116, waybill.run.number)
        _set(sheet, 59, 183, vehicle.plate_no)

        # Planned and actual departure/return. The template has separate lines
        # for first and second shifts, so the selected shift is filled and the
        # other sample line is cleared.
        first_shift = getattr(waybill.duty, "shift", 1) == 1 if waybill.duty else True
        row = 38 if first_shift else 40
        other_row = 40 if first_shift else 38
        _set(sheet, row, 72, _time(waybill.planned_out_time))
        _set(sheet, row, 88, _time(waybill.planned_in_time))
        _set(sheet, row, 105, _time(waybill.actual_out_time) or _date(waybill.work_date))
        _set(sheet, row, 120, _time(waybill.actual_in_time))
        for col in (72, 88, 105, 120):
            _set(sheet, other_row, col, "")

        # Odometer, mileage and fuel sections.
        _set(sheet, 45, 23, _num(waybill.odometer_in))
        _set(sheet, 47, 23, _num(waybill.odometer_out))
        _set(sheet, 48, 170, _num(waybill.mileage))
        _set(sheet, 54, 170, 0)
        _set(sheet, 55, 170, waybill.run.planned_trips)
        _set(sheet, 56, 170, waybill.run.planned_trips if waybill.status.value == "закрыт" else "")
        _set(sheet, 12, 185, _num(waybill.fuel_out))
        _set(sheet, 14, 185, _num(waybill.fuel_issued))
        _set(sheet, 17, 185, _num(waybill.fuel_in))
        _set(sheet, 23, 185, _num(waybill.norm_fuel))
        _set(sheet, 25, 185, _num(waybill.fact_fuel))
        economy = max(waybill.norm_fuel - waybill.fact_fuel, 0)
        overrun = max(waybill.fact_fuel - waybill.norm_fuel, 0)
        _set(sheet, 27, 185, _num(economy))
        _set(sheet, 29, 185, _num(overrun))

        # Medical and technical control marks.
        _set(sheet, 18, 10, waybill.work_date.strftime("%d.%m.%y"))
        _set(sheet, 54, 24, waybill.medical_check)
        _set(sheet, 55, 24, waybill.medical_check if waybill.status.value == "закрыт" else "")
        _set(sheet, 42, 106, waybill.responsible or "")

        workbook.Save()
        workbook.Close(SaveChanges=True)
        workbook = None
        return output_path.read_bytes()
    finally:
        if workbook is not None:
            workbook.Close(SaveChanges=False)
        excel.Quit()
        pythoncom.CoUninitialize()
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
