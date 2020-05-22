# Google Cloud IoT integration

Send command to device:

```json
{
  "service": "cover.close_cover",
  "data": {
    "entity_id": "cover.office_window"
  }
}
```

Requires [mqtt_refresh](https://github.com/r00tat/homeassistant_mqtt_refresh) to work.
