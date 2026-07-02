import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { Alert, App as AntApp, Button, Card, Col, DatePicker, Descriptions, Flex, Form, Input, InputNumber, Layout, Menu, Modal, Row, Select, Space, Statistic, Table, Tabs, Tag, TimePicker, Typography, message } from "antd";
import { CarOutlined, DashboardOutlined, DatabaseOutlined, DownloadOutlined, FileDoneOutlined, FileExcelOutlined, MedicineBoxOutlined, PrinterOutlined, ReloadOutlined, ScheduleOutlined, TeamOutlined, ToolOutlined } from "@ant-design/icons";
import dayjs, { Dayjs } from "dayjs";
import "antd/dist/reset.css";
import "./styles.css";
import { api } from "./api";
import type { Driver, Duty, Route, Run, ScheduleEntry, Vehicle, Warning, Waybill } from "./types";

const { Header, Sider, Content } = Layout;

function statusColor(status: string) {
  if (status === "закрыт") return "green";
  if (status === "аннулирован") return "red";
  if (status === "выдан") return "blue";
  return "default";
}

function App() {
  const [active, setActive] = useState("dashboard");
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([]);
  const [duties, setDuties] = useState<Duty[]>([]);
  const [waybills, setWaybills] = useState<Waybill[]>([]);
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [selectedWaybill, setSelectedWaybill] = useState<Waybill | null>(null);
  const [closingWaybill, setClosingWaybill] = useState<Waybill | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const targetDate = date.format("YYYY-MM-DD");

  async function load() {
    setLoading(true);
    try {
      const [nextDrivers, nextVehicles, nextDuties, nextWaybills, nextWarnings] = await Promise.all([
        api.drivers(),
        api.vehicles(),
        api.duties(targetDate),
        api.waybills(targetDate),
        api.warnings(targetDate),
      ]);
      setDrivers(nextDrivers);
      setVehicles(nextVehicles);
      setDuties(nextDuties);
      setWaybills(nextWaybills);
      setWarnings(nextWarnings);
      const [nextRoutes, nextRuns] = await Promise.all([api.routes(), api.runs()]);
      setRoutes(nextRoutes);
      setRuns(nextRuns);
      setSchedule(await api.schedule(date.year(), date.month() + 1));
    } catch (error) {
      message.error("Не удалось загрузить данные API");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [targetDate]);

  const stats = useMemo(() => ({
    onLine: vehicles.filter((item) => item.status === "на линии" || duties.some((duty) => duty.vehicle_id === item.id)).length,
    dutyDrivers: new Set(duties.map((item) => item.driver_id)).size,
    issued: waybills.length,
    closed: waybills.filter((item) => item.status === "закрыт").length,
    open: waybills.filter((item) => item.status !== "закрыт" && item.status !== "аннулирован").length,
  }), [vehicles, duties, waybills]);

  async function generateWaybills() {
    setLoading(true);
    try {
      await api.createWaybillsForDate(targetDate);
      message.success("Путевые листы сформированы");
      await load();
    } catch {
      message.error("Не удалось сформировать путевые листы");
    } finally {
      setLoading(false);
    }
  }

  async function submitClose(values: { odometer_in: number; fuel_issued?: number; fuel_in: number }) {
    if (!closingWaybill) return;
    await api.closeWaybill(closingWaybill.id, values);
    setClosingWaybill(null);
    form.resetFields();
    message.success("Путевой лист закрыт");
    await load();
  }

  const menu = [
    { key: "dashboard", icon: <DashboardOutlined />, label: "Панель" },
    { key: "database", icon: <DatabaseOutlined />, label: "База данных" },
    { key: "schedule", icon: <ScheduleOutlined />, label: "График месяца" },
    { key: "duties", icon: <ScheduleOutlined />, label: "Наряд" },
    { key: "waybills", icon: <FileDoneOutlined />, label: "Путевые листы" },
    { key: "fleet", icon: <CarOutlined />, label: "Автобусы" },
    { key: "drivers", icon: <TeamOutlined />, label: "Водители" },
    { key: "fuel", icon: <ToolOutlined />, label: "Топливо" },
  ];

  return (
    <AntApp>
      <Layout className="shell">
        <Sider width={238} className="side">
          <div className="brand">Путевые листы</div>
          <Menu mode="inline" selectedKeys={[active]} items={menu} onClick={(event) => setActive(event.key)} />
        </Sider>
        <Layout>
          <Header className="topbar">
            <Space>
              <DatePicker value={date} onChange={(value) => value && setDate(value)} format="DD.MM.YYYY" />
              <Button icon={<ReloadOutlined />} onClick={load} loading={loading} />
            </Space>
            <Space>
              <Button icon={<FileExcelOutlined />} href={api.exportUrl(`/exports/duties.xlsx?duty_date=${targetDate}`)}>Наряд</Button>
              <Button icon={<DownloadOutlined />} href={api.exportUrl("/exports/waybills.xlsx")}>Журнал</Button>
            </Space>
          </Header>
          <Content className="content">
            {active === "dashboard" && <Dashboard stats={stats} warnings={warnings} />}
            {active === "database" && <Database drivers={drivers} vehicles={vehicles} routes={routes} runs={runs} onCreate={load} />}
            {active === "schedule" && <MonthlySchedule schedule={schedule} drivers={drivers} vehicles={vehicles} routes={routes} runs={runs} month={date} selectedDate={targetDate} onCreate={load} />}
            {active === "duties" && <Duties duties={duties} drivers={drivers} vehicles={vehicles} routes={routes} runs={runs} targetDate={targetDate} loading={loading} onCreate={load} onGenerate={generateWaybills} />}
            {active === "waybills" && <Waybills waybills={waybills} loading={loading} onPrint={setSelectedWaybill} onClose={setClosingWaybill} />}
            {active === "fleet" && <Fleet vehicles={vehicles} onCreate={load} />}
            {active === "drivers" && <Drivers drivers={drivers} onCreate={load} />}
            {active === "fuel" && <Fuel waybills={waybills} />}
          </Content>
        </Layout>
      </Layout>
      <Modal open={!!selectedWaybill} onCancel={() => setSelectedWaybill(null)} footer={<Button icon={<PrinterOutlined />} onClick={() => window.print()}>Печать</Button>} width={980}>
        {selectedWaybill && <PrintableWaybill waybill={selectedWaybill} />}
      </Modal>
      <Modal open={!!closingWaybill} onCancel={() => setClosingWaybill(null)} title="Закрытие путевого листа" onOk={form.submit} okText="Закрыть">
        <Form form={form} layout="vertical" onFinish={submitClose} initialValues={{ odometer_in: closingWaybill?.odometer_in, fuel_issued: 0, fuel_in: closingWaybill?.fuel_in }}>
          <Form.Item name="odometer_in" label="Одометр при заезде" rules={[{ required: true }]}>
            <InputNumber min={0} className="wide" />
          </Form.Item>
          <Form.Item name="fuel_issued" label="Выдано топлива">
            <InputNumber min={0} className="wide" />
          </Form.Item>
          <Form.Item name="fuel_in" label="Остаток топлива при заезде" rules={[{ required: true }]}>
            <InputNumber min={0} className="wide" />
          </Form.Item>
        </Form>
      </Modal>
    </AntApp>
  );
}

function MonthlySchedule({ schedule, drivers, vehicles, routes, runs, month, selectedDate, onCreate }: { schedule: ScheduleEntry[]; drivers: Driver[]; vehicles: Vehicle[]; routes: Route[]; runs: Run[]; month: Dayjs; selectedDate: string; onCreate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    const run = runs.find((item) => item.id === values.run_id);
    await api.createScheduleEntry({
      ...values,
      work_date: values.work_date && dayjs.isDayjs(values.work_date) ? values.work_date.format("YYYY-MM-DD") : selectedDate,
      planned_out_time: values.planned_out_time && dayjs.isDayjs(values.planned_out_time) ? values.planned_out_time.format("HH:mm:ss") : run?.depot_out_time,
      planned_in_time: values.planned_in_time && dayjs.isDayjs(values.planned_in_time) ? values.planned_in_time.format("HH:mm:ss") : run?.depot_in_time,
      planned_mileage: values.planned_mileage ?? run?.planned_mileage ?? 0,
      planned_trips: values.planned_trips ?? run?.planned_trips ?? 0,
      status: "план",
    });
    setOpen(false);
    form.resetFields();
    message.success("Назначение добавлено в график");
    onCreate();
  }

  async function buildDuty() {
    await api.createDutiesFromSchedule(selectedDate);
    message.success("Наряд сформирован из графика");
    onCreate();
  }

  return (
    <Card
      title={`График работы на ${month.format("MMMM YYYY")}`}
      extra={<Space><Button onClick={() => setOpen(true)}>Добавить назначение</Button><Button type="primary" onClick={buildDuty}>Сформировать наряд за дату</Button></Space>}
    >
      <Table rowKey="id" dataSource={schedule} pagination={{ pageSize: 12 }} columns={[
        { title: "Дата", dataIndex: "work_date", sorter: (a, b) => a.work_date.localeCompare(b.work_date) },
        { title: "Колонна", dataIndex: "column" },
        { title: "Маршрут", render: (_, item) => `${item.route.number} ${item.route.name}` },
        { title: "Выпуск", dataIndex: ["run", "number"] },
        { title: "Смена", dataIndex: "shift", width: 80 },
        { title: "Водитель", render: (_, item) => `${item.driver.full_name} (${item.driver.personnel_no})` },
        { title: "Автобус / ГРЗ", render: (_, item) => `${item.vehicle.plate_no} / ${item.vehicle.garage_no}` },
        { title: "Выезд", dataIndex: "planned_out_time" },
        { title: "Заезд", dataIndex: "planned_in_time" },
        { title: "Пробег", dataIndex: "planned_mileage" },
      ]} />
      <Modal title="Назначение в месячный график" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить" width={760}>
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ work_date: dayjs(selectedDate), shift: 1, planned_out_time: dayjs("08:00", "HH:mm"), planned_in_time: dayjs("17:00", "HH:mm") }}>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="work_date" label="Дата" rules={[{ required: true }]}><DatePicker className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="column" label="Колонна"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="route_id" label="Маршрут" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={routes.map((item) => ({ value: item.id, label: `${item.number} ${item.name}` }))} /></Form.Item></Col>
            <Col span={12}><Form.Item name="run_id" label="Выпуск" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={runs.map((item) => ({ value: item.id, label: `${item.number} (${routes.find((route) => route.id === item.route_id)?.number ?? ""})` }))} /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="driver_id" label="Водитель" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={drivers.map((item) => ({ value: item.id, label: `${item.full_name} (${item.personnel_no})` }))} /></Form.Item></Col>
            <Col span={12}><Form.Item name="vehicle_id" label="Автобус / ГРЗ" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={vehicles.map((item) => ({ value: item.id, label: `${item.plate_no} / ${item.garage_no}` }))} /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={6}><Form.Item name="shift" label="Смена"><InputNumber min={1} max={4} className="wide" /></Form.Item></Col>
            <Col span={6}><Form.Item name="planned_out_time" label="Выезд"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={6}><Form.Item name="planned_in_time" label="Заезд"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={6}><Form.Item name="planned_trips" label="Рейсы"><InputNumber min={0} className="wide" /></Form.Item></Col>
          </Row>
          <Form.Item name="planned_mileage" label="Плановый пробег"><InputNumber min={0} className="wide" /></Form.Item>
          <Form.Item name="note" label="Примечание"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

function Database({ drivers, vehicles, routes, runs, onCreate }: { drivers: Driver[]; vehicles: Vehicle[]; routes: Route[]; runs: Run[]; onCreate: () => void }) {
  return (
    <Tabs
      className="database-tabs"
      items={[
        { key: "drivers", label: "Водители", children: <Drivers drivers={drivers} onCreate={onCreate} /> },
        { key: "vehicles", label: "Транспорт и ГРЗ", children: <Fleet vehicles={vehicles} onCreate={onCreate} /> },
        { key: "routes", label: "Маршруты", children: <Routes routes={routes} onCreate={onCreate} /> },
        { key: "runs", label: "Выпуски", children: <Runs runs={runs} routes={routes} onCreate={onCreate} /> },
      ]}
    />
  );
}

function Dashboard({ stats, warnings }: { stats: Record<string, number>; warnings: Warning[] }) {
  return (
    <Space direction="vertical" size={16} className="wide">
      <Row gutter={[12, 12]}>
        <Col xs={24} md={8} xl={4}><Card><Statistic title="Автобусы на линии" value={stats.onLine} prefix={<CarOutlined />} /></Card></Col>
        <Col xs={24} md={8} xl={5}><Card><Statistic title="Водители в наряде" value={stats.dutyDrivers} prefix={<TeamOutlined />} /></Card></Col>
        <Col xs={24} md={8} xl={5}><Card><Statistic title="Выписано листов" value={stats.issued} prefix={<FileDoneOutlined />} /></Card></Col>
        <Col xs={24} md={8} xl={5}><Card><Statistic title="Закрыто" value={stats.closed} /></Card></Col>
        <Col xs={24} md={8} xl={5}><Card><Statistic title="Незакрыто" value={stats.open} /></Card></Col>
      </Row>
      <Card title="Предупреждения">
        {warnings.length === 0 ? <Alert type="success" message="Критичных предупреждений нет" /> : warnings.map((item, index) => (
          <Alert key={`${item.entity}-${item.entity_id}-${index}`} type={item.level === "critical" ? "error" : "warning"} message={item.message} showIcon className="alert" />
        ))}
      </Card>
    </Space>
  );
}

function Duties({ duties, drivers, vehicles, routes, runs, targetDate, loading, onCreate, onGenerate }: { duties: Duty[]; drivers: Driver[]; vehicles: Vehicle[]; routes: Route[]; runs: Run[]; targetDate: string; loading: boolean; onCreate: () => void; onGenerate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    const run = runs.find((item) => item.id === values.run_id);
    await api.createDuty({
      ...values,
      duty_date: targetDate,
      planned_out_time: values.planned_out_time && dayjs.isDayjs(values.planned_out_time) ? values.planned_out_time.format("HH:mm:ss") : run?.depot_out_time,
      planned_in_time: values.planned_in_time && dayjs.isDayjs(values.planned_in_time) ? values.planned_in_time.format("HH:mm:ss") : run?.depot_in_time,
      planned_mileage: values.planned_mileage ?? run?.planned_mileage ?? 0,
      planned_trips: values.planned_trips ?? run?.planned_trips ?? 0,
      status: "план",
    });
    setOpen(false);
    form.resetFields();
    message.success("Строка наряда создана");
    onCreate();
  }

  return (
    <Card title="Ежедневный наряд" extra={<Space><Button onClick={() => setOpen(true)}>Добавить строку</Button><Button type="primary" icon={<FileDoneOutlined />} onClick={onGenerate}>Выписать путевые листы</Button></Space>}>
      <Table loading={loading} rowKey="id" dataSource={duties} pagination={false} columns={[
        { title: "Маршрут", render: (_, item) => `${item.route.number} ${item.route.name}` },
        { title: "Выпуск", dataIndex: ["run", "number"] },
        { title: "Смена", dataIndex: "shift", width: 80 },
        { title: "ТС", render: (_, item) => `${item.vehicle.plate_no} / ${item.vehicle.garage_no}` },
        { title: "Водитель", dataIndex: ["driver", "full_name"] },
        { title: "Таб.", dataIndex: ["driver", "personnel_no"] },
        { title: "Выезд", dataIndex: "planned_out_time" },
        { title: "Возврат", dataIndex: "planned_in_time" },
        { title: "Пробег", dataIndex: "planned_mileage" },
      ]} />
      <Modal title="Новая строка наряда" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить">
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ shift: 1, planned_out_time: dayjs("08:00", "HH:mm"), planned_in_time: dayjs("17:00", "HH:mm") }}>
          <Form.Item name="route_id" label="Маршрут" rules={[{ required: true }]}>
            <Select options={routes.map((item) => ({ value: item.id, label: `${item.number} ${item.name}` }))} />
          </Form.Item>
          <Form.Item name="run_id" label="Выпуск" rules={[{ required: true }]}>
            <Select options={runs.map((item) => ({ value: item.id, label: item.number }))} />
          </Form.Item>
          <Form.Item name="driver_id" label="Водитель" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={drivers.map((item) => ({ value: item.id, label: `${item.full_name} (${item.personnel_no})` }))} />
          </Form.Item>
          <Form.Item name="vehicle_id" label="Автобус" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={vehicles.map((item) => ({ value: item.id, label: `${item.plate_no} / ${item.garage_no}` }))} />
          </Form.Item>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="shift" label="Смена"><InputNumber min={1} max={4} className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="planned_out_time" label="Выезд"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="planned_in_time" label="Заезд"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="planned_mileage" label="Плановый пробег"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="planned_trips" label="Количество рейсов"><InputNumber min={0} className="wide" /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </Card>
  );
}

function Waybills({ waybills, loading, onPrint, onClose }: { waybills: Waybill[]; loading: boolean; onPrint: (item: Waybill) => void; onClose: (item: Waybill) => void }) {
  return (
    <Card title="Журнал путевых листов">
      <Table loading={loading} rowKey="id" dataSource={waybills} columns={[
        { title: "Номер", dataIndex: "number" },
        { title: "Дата", dataIndex: "work_date" },
        { title: "Водитель", dataIndex: ["driver", "full_name"] },
        { title: "Автобус", render: (_, item) => `${item.vehicle.plate_no} / ${item.vehicle.garage_no}` },
        { title: "Маршрут", dataIndex: ["route", "number"] },
        { title: "Выпуск", dataIndex: ["run", "number"] },
        { title: "Пробег", dataIndex: "mileage" },
        { title: "Топливо", render: (_, item) => `${item.fuel_out} → ${item.fuel_in}` },
        { title: "Статус", render: (_, item) => <Tag color={statusColor(item.status)}>{item.status}</Tag> },
        { title: "", render: (_, item) => <Space><Button icon={<PrinterOutlined />} onClick={() => onPrint(item)} /><Button href={api.exportUrl(`/exports/waybills/${item.id}/template.xls`)}>Шаблон XLS</Button><Button disabled={item.status === "закрыт"} onClick={() => onClose(item)}>Закрыть</Button></Space> },
      ]} />
    </Card>
  );
}

function Fleet({ vehicles, onCreate }: { vehicles: Vehicle[]; onCreate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    await api.createVehicle({
      ...values,
      diagnostic_valid_until: values.diagnostic_valid_until && dayjs.isDayjs(values.diagnostic_valid_until) ? values.diagnostic_valid_until.format("YYYY-MM-DD") : undefined,
      status: values.status ?? "резерв",
      fuel_type: values.fuel_type ?? "ДТ",
      fuel_rate: values.fuel_rate ?? 0,
      fuel_balance: values.fuel_balance ?? 0,
      total_mileage: values.total_mileage ?? 0,
      period_start_mileage: values.period_start_mileage ?? 0,
    });
    setOpen(false);
    form.resetFields();
    message.success("Автобус добавлен");
    onCreate();
  }

  return (
    <Card title="Автобусы" extra={<Button onClick={() => setOpen(true)}>Добавить автобус</Button>}>
      <Table rowKey="id" dataSource={vehicles} columns={[
        { title: "Госномер", dataIndex: "plate_no" },
        { title: "Гаражный", dataIndex: "garage_no" },
        { title: "Марка", render: (_, item) => `${item.brand} ${item.model ?? ""}` },
        { title: "Диагностика до", dataIndex: "diagnostic_valid_until" },
        { title: "Норма", render: (_, item) => `${item.fuel_rate} л/100` },
        { title: "Остаток", dataIndex: "fuel_balance" },
        { title: "Статус", dataIndex: "status" },
      ]} />
      <Modal title="Новый автобус" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить">
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ brand: "ЛиАЗ", fuel_type: "ДТ", status: "резерв", fuel_rate: 43, fuel_balance: 0 }}>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="plate_no" label="Госномер" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="garage_no" label="Гаражный номер" rules={[{ required: true }]}><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="brand" label="Марка" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="model" label="Модель"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="diagnostic_valid_until" label="Диагностическая карта до"><DatePicker className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="status" label="Статус"><Select options={["на линии", "ремонт", "резерв", "списан"].map((value) => ({ value, label: value }))} /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="fuel_rate" label="Норма л/100"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="fuel_balance" label="Остаток топлива"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="total_mileage" label="Пробег"><InputNumber min={0} className="wide" /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </Card>
  );
}

function Drivers({ drivers, onCreate }: { drivers: Driver[]; onCreate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    await api.createDriver({
      ...values,
      license_valid_until: values.license_valid_until && dayjs.isDayjs(values.license_valid_until) ? values.license_valid_until.format("YYYY-MM-DD") : undefined,
      medical_valid_until: values.medical_valid_until && dayjs.isDayjs(values.medical_valid_until) ? values.medical_valid_until.format("YYYY-MM-DD") : undefined,
      status: values.status ?? "работает",
    });
    setOpen(false);
    form.resetFields();
    message.success("Водитель добавлен");
    onCreate();
  }

  async function remove(driver: Driver) {
    try {
      await api.deleteDriver(driver.id);
      message.success("Водитель удален");
      onCreate();
    } catch {
      message.error("Не удалось удалить водителя: он может использоваться в графике, наряде или путевых листах");
    }
  }

  return (
    <Card title="Водители" extra={<Button onClick={() => setOpen(true)}>Добавить водителя</Button>}>
      <Table rowKey="id" dataSource={drivers} columns={[
        { title: "ФИО", dataIndex: "full_name" },
        { title: "Табельный", dataIndex: "personnel_no" },
        { title: "Кат.", dataIndex: "license_category" },
        { title: "ВУ", dataIndex: "license_no" },
        { title: "ВУ до", dataIndex: "license_valid_until" },
        { title: "Медсправка до", dataIndex: "medical_valid_until" },
        { title: "Колонна", dataIndex: "column" },
        { title: "Статус", dataIndex: "status" },
        {
          title: "",
          render: (_, item) => (
            <Button danger onClick={() => Modal.confirm({
              title: "Удалить водителя?",
              content: `${item.full_name} (${item.personnel_no})`,
              okText: "Удалить",
              okButtonProps: { danger: true },
              cancelText: "Отмена",
              onOk: () => remove(item),
            })}>
              Удалить
            </Button>
          ),
        },
      ]} />
      <Modal title="Новый водитель" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить">
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ license_category: "D", status: "работает" }}>
          <Form.Item name="full_name" label="ФИО" rules={[{ required: true }]}><Input /></Form.Item>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="personnel_no" label="Табельный номер" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="phone" label="Телефон"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="license_category" label="Категория"><Input /></Form.Item></Col>
            <Col span={16}><Form.Item name="license_no" label="Номер водительского удостоверения"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="license_valid_until" label="ВУ действует до"><DatePicker className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="medical_valid_until" label="Медсправка до"><DatePicker className="wide" /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="column" label="Колонна"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="status" label="Статус"><Select options={["работает", "отпуск", "больничный", "уволен"].map((value) => ({ value, label: value }))} /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </Card>
  );
}

function Routes({ routes, onCreate }: { routes: Route[]; onCreate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    await api.createRoute({
      ...values,
      start_time: values.start_time && dayjs.isDayjs(values.start_time) ? values.start_time.format("HH:mm:ss") : undefined,
      end_time: values.end_time && dayjs.isDayjs(values.end_time) ? values.end_time.format("HH:mm:ss") : undefined,
      service_type: values.service_type ?? "городской",
      distance_km: values.distance_km ?? 0,
      trips_count: values.trips_count ?? 0,
      planned_mileage: values.planned_mileage ?? 0,
    });
    setOpen(false);
    form.resetFields();
    message.success("Маршрут добавлен");
    onCreate();
  }

  return (
    <Card title="Маршруты" extra={<Button onClick={() => setOpen(true)}>Добавить маршрут</Button>}>
      <Table rowKey="id" dataSource={routes} columns={[
        { title: "Номер", dataIndex: "number" },
        { title: "Наименование", dataIndex: "name" },
        { title: "Вид сообщения", dataIndex: "service_type" },
        { title: "Протяженность", dataIndex: "distance_km" },
        { title: "Рейсы", dataIndex: "trips_count" },
        { title: "Плановый пробег", dataIndex: "planned_mileage" },
      ]} />
      <Modal title="Новый маршрут" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить">
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ service_type: "городской", distance_km: 0, trips_count: 0, planned_mileage: 0 }}>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="number" label="Номер" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={16}><Form.Item name="name" label="Наименование" rules={[{ required: true }]}><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="service_type" label="Вид сообщения">
            <Select options={["городской", "пригородный", "межмуниципальный"].map((value) => ({ value, label: value }))} />
          </Form.Item>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="distance_km" label="Протяженность"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="trips_count" label="Рейсы"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={8}><Form.Item name="planned_mileage" label="Плановый пробег"><InputNumber min={0} className="wide" /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="start_time" label="Начало работы"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="end_time" label="Окончание работы"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
          </Row>
          <Form.Item name="checkpoints" label="Контрольные точки"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

function Runs({ runs, routes, onCreate }: { runs: Run[]; routes: Route[]; onCreate: () => void }) {
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  async function submit(values: Record<string, unknown>) {
    await api.createRun({
      ...values,
      depot_out_time: values.depot_out_time && dayjs.isDayjs(values.depot_out_time) ? values.depot_out_time.format("HH:mm:ss") : "08:00:00",
      work_start_time: values.work_start_time && dayjs.isDayjs(values.work_start_time) ? values.work_start_time.format("HH:mm:ss") : "08:15:00",
      work_end_time: values.work_end_time && dayjs.isDayjs(values.work_end_time) ? values.work_end_time.format("HH:mm:ss") : "17:00:00",
      depot_in_time: values.depot_in_time && dayjs.isDayjs(values.depot_in_time) ? values.depot_in_time.format("HH:mm:ss") : "17:15:00",
      planned_mileage: values.planned_mileage ?? 0,
      planned_trips: values.planned_trips ?? 0,
    });
    setOpen(false);
    form.resetFields();
    message.success("Выпуск добавлен");
    onCreate();
  }

  return (
    <Card title="Выпуски" extra={<Button onClick={() => setOpen(true)}>Добавить выпуск</Button>}>
      <Table rowKey="id" dataSource={runs} columns={[
        { title: "Маршрут", render: (_, item) => routes.find((route) => route.id === item.route_id)?.number ?? item.route_id },
        { title: "Выпуск", dataIndex: "number" },
        { title: "Выезд из парка", dataIndex: "depot_out_time" },
        { title: "Начало", dataIndex: "work_start_time" },
        { title: "Окончание", dataIndex: "work_end_time" },
        { title: "Заезд", dataIndex: "depot_in_time" },
        { title: "Пробег", dataIndex: "planned_mileage" },
        { title: "Рейсы", dataIndex: "planned_trips" },
      ]} />
      <Modal title="Новый выпуск" open={open} onCancel={() => setOpen(false)} onOk={form.submit} okText="Сохранить">
        <Form form={form} layout="vertical" onFinish={submit} initialValues={{ depot_out_time: dayjs("08:00", "HH:mm"), work_start_time: dayjs("08:15", "HH:mm"), work_end_time: dayjs("17:00", "HH:mm"), depot_in_time: dayjs("17:15", "HH:mm"), planned_mileage: 0, planned_trips: 0 }}>
          <Form.Item name="route_id" label="Маршрут" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={routes.map((item) => ({ value: item.id, label: `${item.number} ${item.name}` }))} />
          </Form.Item>
          <Form.Item name="number" label="Номер выпуска" rules={[{ required: true }]}><Input /></Form.Item>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="depot_out_time" label="Выезд из парка"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="work_start_time" label="Начало работы"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="work_end_time" label="Окончание работы"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="depot_in_time" label="Заезд в парк"><TimePicker format="HH:mm" className="wide" /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="planned_mileage" label="Плановый пробег"><InputNumber min={0} className="wide" /></Form.Item></Col>
            <Col span={12}><Form.Item name="planned_trips" label="Плановое количество рейсов"><InputNumber min={0} className="wide" /></Form.Item></Col>
          </Row>
          <Form.Item name="required_bus_type" label="Требуемый тип автобуса"><Input /></Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

function Fuel({ waybills }: { waybills: Waybill[] }) {
  return (
    <Card title="Учет топлива">
      <Table rowKey="id" dataSource={waybills} columns={[
        { title: "Лист", dataIndex: "number" },
        { title: "Автобус", dataIndex: ["vehicle", "plate_no"] },
        { title: "Выезд", dataIndex: "fuel_out" },
        { title: "Выдано", dataIndex: "fuel_issued" },
        { title: "Заезд", dataIndex: "fuel_in" },
        { title: "Норма", dataIndex: "norm_fuel" },
        { title: "Факт", dataIndex: "fact_fuel" },
        { title: "Итог", render: (_, item) => {
          const diff = item.fact_fuel - item.norm_fuel;
          return <Tag color={diff > 5 ? "red" : "green"}>{diff > 0 ? "Перерасход" : "Экономия"} {Math.abs(diff).toFixed(1)}</Tag>;
        } },
      ]} />
    </Card>
  );
}

function PrintableWaybill({ waybill }: { waybill: Waybill }) {
  return (
    <div className="print-form">
      <Flex justify="space-between" align="start">
        <div>
          <Typography.Title level={3}>ПУТЕВОЙ ЛИСТ АВТОБУСА</Typography.Title>
          <Typography.Text strong>№ {waybill.number}</Typography.Text>
        </div>
        <div className="stamp">Место для штампа организации</div>
      </Flex>
      <Descriptions bordered column={2} size="small">
        <Descriptions.Item label="Организация" span={2}>{waybill.organization}</Descriptions.Item>
        <Descriptions.Item label="Период действия">{waybill.valid_from} - {waybill.valid_to}</Descriptions.Item>
        <Descriptions.Item label="Вид сообщения">{waybill.route.service_type}</Descriptions.Item>
        <Descriptions.Item label="Марка автобуса">{waybill.vehicle.brand} {waybill.vehicle.model}</Descriptions.Item>
        <Descriptions.Item label="Госномер">{waybill.vehicle.plate_no}</Descriptions.Item>
        <Descriptions.Item label="Гаражный номер">{waybill.vehicle.garage_no}</Descriptions.Item>
        <Descriptions.Item label="Водитель">{waybill.driver.full_name}</Descriptions.Item>
        <Descriptions.Item label="Табельный">{waybill.driver.personnel_no}</Descriptions.Item>
        <Descriptions.Item label="Водительское удостоверение">{waybill.driver.license_no}</Descriptions.Item>
        <Descriptions.Item label="Маршрут">{waybill.route.number} {waybill.route.name}</Descriptions.Item>
        <Descriptions.Item label="Выпуск">{waybill.run.number}</Descriptions.Item>
        <Descriptions.Item label="Выезд">{waybill.planned_out_time}</Descriptions.Item>
        <Descriptions.Item label="Заезд">{waybill.planned_in_time}</Descriptions.Item>
        <Descriptions.Item label="Одометр выезд">{waybill.odometer_out}</Descriptions.Item>
        <Descriptions.Item label="Одометр заезд">{waybill.odometer_in}</Descriptions.Item>
        <Descriptions.Item label="Пробег">{waybill.mileage}</Descriptions.Item>
        <Descriptions.Item label="Остаток топлива выезд">{waybill.fuel_out}</Descriptions.Item>
        <Descriptions.Item label="Выдано топлива">{waybill.fuel_issued}</Descriptions.Item>
        <Descriptions.Item label="Остаток топлива заезд">{waybill.fuel_in}</Descriptions.Item>
        <Descriptions.Item label="Расход по норме">{waybill.norm_fuel}</Descriptions.Item>
        <Descriptions.Item label="Фактический расход">{waybill.fact_fuel}</Descriptions.Item>
        <Descriptions.Item label={<Space><MedicineBoxOutlined /> Медосмотр</Space>}>{waybill.medical_check}</Descriptions.Item>
        <Descriptions.Item label={<Space><ToolOutlined /> Техконтроль</Space>}>{waybill.technical_check}</Descriptions.Item>
      </Descriptions>
      <div className="signatures">
        <span>Медицинский работник ____________</span>
        <span>Механик ____________</span>
        <span>Диспетчер ____________</span>
        <span>Водитель ____________</span>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
