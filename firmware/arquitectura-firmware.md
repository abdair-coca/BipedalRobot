# Arquitectura de firmware

## Motion Controller (ESP32 DevKit, nuevo) — Arduino framework (C++)

### Librerias
- `Adafruit_PWMServoDriver` — control PCA9685.
- `MPU6050` (ej. Electronic Cats o I2Cdevlib) o lectura cruda + filtro propio — para IMU.
- `WiFi.h` + `esp_now.h` — comunicacion con Head Node.

### Estructura de modulos
```
firmware/motion-controller/
├── motion-controller.ino     # setup() + loop()
├── imu.h/.cpp                # lectura MPU-6050, filtro complementario, angulos pitch/roll
├── servo_driver.h/.cpp        # wrapper sobre PCA9685, mapeo angulo->pulso por canal
├── balance.h/.cpp             # PID de balance, correccion sobre cadera/tobillo
├── gait.h/.cpp                # secuencias de marcha precalculadas (lookup de poses por frame)
├── comms.h/.cpp                # ESP-NOW: enviar estado, recibir comandos
└── config.h                   # pines, direcciones I2C, limites de angulo por servo
```

### Loop principal (pseudo-codigo)
```cpp
void loop() {
  imu.update();                      // lee angulos actuales
  float correction = balance.pid(imu.pitch, imu.roll);

  if (gait.isWalking()) {
    gait.advanceFrame();             // siguiente pose de la secuencia de marcha
  }

  servo_driver.applyPose(gait.currentPose(), correction);
  comms.publishState(gait.state());  // idle/walking/fallen
  comms.checkIncoming();             // comandos externos si los hay

  delay(LOOP_INTERVAL_MS);           // ej. 20ms -> 50Hz
}
```

### Deteccion de caida (simple, fase 2)
- Si `abs(pitch) > UMBRAL` o `abs(roll) > UMBRAL` sostenido por N ciclos -> estado `fallen`, cortar marcha, opcionalmente relajar servos para no forzar motor contra el piso.

## Head Node (Wemos D1 mini, existente) — sin reescritura
- Se mantiene el firmware actual de robotCreeper.
- **Unico agregado**: listener ESP-NOW que recibe el estado (`idle`/`walking`/`fallen`) y dispara la expresion/animacion de cara correspondiente en el OLED.

## Vision Node (ESP32-CAM, existente) — sin cambios
- No requiere cambios para el alcance de este proyecto (fase 4 en adelante podria integrarse mas, ver docs/03-roadmap-fases.md).

## Calibracion

- **MPU-6050**: calibrar offset en frio al arrancar (robot parado quieto sobre superficie plana), guardar offsets en `config.h` o EEPROM.
- **Servos**: cada servo fisico tiene su propio offset de "centro" mecanico — mapear en `config.h` un array de trim por canal (`SERVO_TRIM[8]`) para no depender de que todos los servos esten fisicamente centrados igual.
