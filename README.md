# ControlRoom API

**ControlRoom API** — учебный headless REST API для программной инженерии управляющих систем.  
Проект моделирует небольшую систему управления помещениями: аудитории, датчики, исполнительные устройства, правила автоматики, команды и аварийные уведомления.

Проект специально сделан не как фронтенд-приложение, а как API-сервис, который можно запустить, протестировать и показать через Swagger.

---

## Что умеет проект

- вести справочник помещений;
- подключать к помещениям датчики и исполнительные устройства;
- принимать показания датчиков;
- хранить правила автоматики;
- автоматически создавать команды устройствам при срабатывании правил;
- автоматически создавать alerts при выходе параметров за порог;
- отдавать сводку по системе;
- поддерживать CRUD и search-эндпоинты;
- работать на SQLite без отдельного сервера БД;
- запускаться локально или через Docker.

Пример логики управляющей системы:

> Если датчик температуры в аудитории показывает значение выше 26 °C, API создает alert и добавляет команду кондиционеру перейти в режим охлаждения.

---

## Стек

- Python 3.11+
- FastAPI
- Pydantic
- SQLite
- Pytest
- Docker / Docker Compose
- GitHub Actions CI

---

## Быстрый запуск

### 1. Установка зависимостей

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 2. Запуск API

```bash
uvicorn app.main:app --reload
```

После запуска:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Healthcheck: http://127.0.0.1:8000/health

---

## Заполнение демо-данными

```bash
python -m app.seed
```

Команда пересоздает локальную базу `controlroom.sqlite3` и добавляет:

- несколько помещений;
- устройства;
- датчики;
- правила автоматики;
- стартовые показания.

---

## Запуск через Docker

```bash
docker compose up --build
```

Swagger будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

---

## Тесты

```bash
pytest -q
```

В тестах проверяется:

- доступность healthcheck;
- создание помещения и устройства;
- поиск помещений;
- автоматическое срабатывание правила при записи показания датчика;
- создание команды и alert после срабатывания правила.

---

## Основные сущности

### Room

Помещение, которым управляет система.

Поля:

- `id`
- `name`
- `floor`
- `purpose`
- `target_temperature`
- `created_at`

### Device

Исполнительное устройство: кондиционер, вентиляция, освещение и так далее.

Поля:

- `id`
- `room_id`
- `name`
- `device_type`
- `status`
- `mode`
- `power_kw`
- `last_command_at`

### Sensor

Датчик, привязанный к помещению.

Поля:

- `id`
- `room_id`
- `name`
- `sensor_type`
- `unit`
- `is_active`

### SensorReading

Показание датчика.

Поля:

- `id`
- `sensor_id`
- `value`
- `measured_at`

### ControlRule

Правило автоматики.

Пример:

```json
{
  "room_id": 1,
  "name": "Охлаждение лаборатории при перегреве",
  "metric_type": "temperature",
  "operator": ">",
  "threshold_value": 26,
  "target_device_type": "climate",
  "command_type": "set_mode",
  "command_payload": {
    "mode": "cooling",
    "target_temperature": 22
  },
  "is_enabled": true
}
```

### ControlCommand

Команда устройству. Может быть создана вручную оператором или автоматически правилом.

### Alert

Уведомление о нарушении контрольного условия.

---

## Формат ответа API

API использует единый формат ответа:

```json
{
  "data": {},
  "errors": [],
  "meta": {}
}
```

Пример успешного ответа:

```json
{
  "data": {
    "id": 1,
    "name": "Лаборатория автоматики 301",
    "floor": 3,
    "purpose": "laboratory",
    "target_temperature": 22.0,
    "created_at": "2026-05-08 12:00:00"
  },
  "errors": [],
  "meta": {
    "created": true
  }
}
```

---

## Основные эндпоинты

### Помещения

```text
GET    /api/v1/rooms
POST   /api/v1/rooms
GET    /api/v1/rooms/{room_id}
PATCH  /api/v1/rooms/{room_id}
DELETE /api/v1/rooms/{room_id}
POST   /api/v1/rooms:search
```

### Устройства

```text
GET    /api/v1/devices
POST   /api/v1/devices
GET    /api/v1/devices/{device_id}
PATCH  /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}
POST   /api/v1/devices:search
POST   /api/v1/devices/{device_id}/commands
GET    /api/v1/commands
```

### Датчики и показания

```text
GET    /api/v1/sensors
POST   /api/v1/sensors
GET    /api/v1/sensors/{sensor_id}
PATCH  /api/v1/sensors/{sensor_id}
DELETE /api/v1/sensors/{sensor_id}
POST   /api/v1/sensors:search
POST   /api/v1/sensors/{sensor_id}/readings
GET    /api/v1/sensors/{sensor_id}/readings
```

### Правила автоматики

```text
GET    /api/v1/rules
POST   /api/v1/rules
GET    /api/v1/rules/{rule_id}
PATCH  /api/v1/rules/{rule_id}
DELETE /api/v1/rules/{rule_id}
POST   /api/v1/rules:search
```

### Уведомления и сводка

```text
GET    /api/v1/alerts
GET    /api/v1/alerts/{alert_id}
PATCH  /api/v1/alerts/{alert_id}
POST   /api/v1/alerts:search
GET    /api/v1/overview
```

---

## Пример сценария через curl

### Создать помещение

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rooms \
  -H "Content-Type: application/json" \
  -d '{"name":"Лаборатория 305","floor":3,"purpose":"laboratory"}'
```

### Создать устройство

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"name":"Кондиционер 305","device_type":"climate"}'
```

### Создать датчик

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sensors \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"name":"Температура 305","sensor_type":"temperature","unit":"°C"}'
```

### Создать правило автоматики

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "room_id":1,
    "name":"Включить охлаждение при перегреве",
    "metric_type":"temperature",
    "operator":">",
    "threshold_value":25,
    "target_device_type":"climate",
    "command_type":"set_mode",
    "command_payload":{"mode":"cooling","target_temperature":22}
  }'
```

### Передать показание датчика

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sensors/1/readings \
  -H "Content-Type: application/json" \
  -d '{"value":28.4}'
```

В ответе в `meta` будет видно, сработало ли правило:

```json
{
  "created": true,
  "triggered_rules": 1,
  "generated_alerts": 1,
  "generated_commands": 1
}
```

---

## Структура проекта

```text
controlroom_api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── responses.py
│   ├── schemas.py
│   ├── seed.py
│   ├── services.py
│   └── routers/
│       ├── alerts.py
│       ├── common.py
│       ├── devices.py
│       ├── overview.py
│       ├── rooms.py
│       ├── rules.py
│       └── sensors.py
├── tests/
│   └── test_api.py
├── docs/
│   └── api_examples.md
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Возможные доработки

- авторизация операторов;
- роли администратора, инженера и наблюдателя;
- журналирование всех действий;
- интеграция с MQTT;
- экспорт отчетов;
- хранение временных рядов в отдельной БД;
- веб-интерфейс диспетчера.
