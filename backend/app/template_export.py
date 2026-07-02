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


def _waybill_cells(waybill: Waybill) -> dict[tuple[int, int], object]:
    bus_name = f"{waybill.vehicle.brand} {waybill.vehicle.model or ''}".strip()
    period = f"{_date(waybill.valid_from)} - {_date(waybill.valid_to)}"
    route_name = f"{waybill.route.number} {waybill.route.name}".strip()
    driver = waybill.driver
    vehicle = waybill.vehicle
    first_shift = getattr(waybill.duty, "shift", 1) == 1 if waybill.duty else True
    row = 38 if first_shift else 40
    other_row = 40 if first_shift else 38
    economy = max(waybill.norm_fuel - waybill.fact_fuel, 0)
    overrun = max(waybill.fact_fuel - waybill.norm_fuel, 0)

    cells: dict[tuple[int, int], object] = {
        (1, 5): driver.column or "",
        (1, 27): vehicle.garage_no,
        (1, 139): vehicle.plate_no,
        (1, 199): _num(vehicle.fuel_rate),
        (6, 115): waybill.number,
        (7, 17): waybill.organization,
        (7, 57): period,
        (8, 74): bus_name,
        (9, 89): vehicle.plate_no,
        (9, 122): vehicle.garage_no,
        (10, 58): f"Вид сообщения: {waybill.route.service_type.title()}",
        (16, 57): driver.full_name,
        (16, 96): driver.personnel_no,
        (16, 111): driver.license_no or "",
        (16, 124): "",
        (17, 57): f"СНИЛС: {driver.snils}",
        (18, 57): driver.full_name,
        (18, 96): driver.personnel_no,
        (18, 111): driver.license_no or "",
        (18, 124): "",
        (19, 57): f"СНИЛС: {driver.snils}",
        (22, 58): route_name,
        (23, 58): "Вид перевозки: Регулярные перевозки пассажиров и багажа",
        (24, 58): f"{waybill.route.number} {waybill.route.name}",
        (24, 118): _num(vehicle.fuel_rate),
        (27, 116): waybill.run.number,
        (59, 183): vehicle.plate_no,
        (row, 72): _time(waybill.planned_out_time),
        (row, 88): _time(waybill.planned_in_time),
        (row, 105): _time(waybill.actual_out_time) or _date(waybill.work_date),
        (row, 120): _time(waybill.actual_in_time),
        (other_row, 72): "",
        (other_row, 88): "",
        (other_row, 105): "",
        (other_row, 120): "",
        (45, 23): _num(waybill.odometer_in),
        (47, 23): _num(waybill.odometer_out),
        (48, 170): _num(waybill.mileage),
        (54, 170): 0,
        (55, 170): waybill.run.planned_trips,
        (56, 170): waybill.run.planned_trips if waybill.status.value == "закрыт" else "",
        (12, 185): _num(waybill.fuel_out),
        (14, 185): _num(waybill.fuel_issued),
        (17, 185): _num(waybill.fuel_in),
        (23, 185): _num(waybill.norm_fuel),
        (25, 185): _num(waybill.fact_fuel),
        (27, 185): _num(economy),
        (29, 185): _num(overrun),
        (18, 10): waybill.work_date.strftime("%d.%m.%y"),
        (54, 24): waybill.medical_check,
        (55, 24): waybill.medical_check if waybill.status.value == "закрыт" else "",
        (42, 106): waybill.responsible or "",
    }
    return cells


def _render_with_xlutils(waybill: Waybill) -> bytes:
    try:
        import xlrd
        from xlutils.copy import copy
    except ImportError as exc:
        raise RuntimeError("xlrd and xlutils are required to render .xls templates on Linux") from exc

    source = xlrd.open_workbook(str(WAYBILL_TEMPLATE), formatting_info=True)
    workbook = copy(source)
    sheet = workbook.get_sheet(0)
    for (row, col), value in _waybill_cells(waybill).items():
        sheet.write(row - 1, col - 1, value)

    with NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
        output_path = Path(tmp.name)
    try:
        workbook.save(str(output_path))
        return output_path.read_bytes()
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass


def _render_with_excel_com(waybill: Waybill) -> bytes:
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("pywin32 is not available") from exc

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
        for (row, col), value in _waybill_cells(waybill).items():
            _set(sheet, row, col, value)
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


def render_waybill_xls_from_template(waybill: Waybill) -> bytes:
    if not WAYBILL_TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {WAYBILL_TEMPLATE}")

    try:
        return _render_with_excel_com(waybill)
    except RuntimeError:
        return _render_with_xlutils(waybill)
