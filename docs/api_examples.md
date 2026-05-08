# API examples

Набор коротких примеров для ручной проверки API после запуска сервера.

## 1. Healthcheck

```bash
curl http://127.0.0.1:8000/health
```

## 2. Создание помещения

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rooms \
  -H "Content-Type: application/json" \
  -d '{"name":"Аудитория 101","floor":1,"purpose":"lecture","target_temperature":22}'
```

## 3. Создание исполнительного устройства

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"name":"Кондиционер 101","device_type":"climate","status":"online","mode":"auto","power_kw":1.4}'
```

## 4. Создание датчика

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sensors \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"name":"Датчик температуры 101","sensor_type":"temperature","unit":"°C","is_active":true}'
```

## 5. Создание правила автоматики

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rules \
  -H "Content-Type: application/json" \
  -d '{
    "room_id":1,
    "name":"Охлаждение при температуре выше нормы",
    "metric_type":"temperature",
    "operator":">",
    "threshold_value":25,
    "target_device_type":"climate",
    "command_type":"set_mode",
    "command_payload":{"mode":"cooling","target_temperature":21},
    "is_enabled":true
  }'
```

## 6. Передача показания датчика

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sensors/1/readings \
  -H "Content-Type: application/json" \
  -d '{"value":28.2}'
```

## 7. Проверка созданных команд

```bash
curl http://127.0.0.1:8000/api/v1/commands
```

## 8. Проверка созданных alerts

```bash
curl http://127.0.0.1:8000/api/v1/alerts
```

## 9. Сводка

```bash
curl http://127.0.0.1:8000/api/v1/overview
```
