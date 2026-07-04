# Tests de componentes

Seccion para probar hardware/codigo de forma aislada, **antes** de integrar al firmware final del bipedo. Cada test valida un componente o subsistema especifico (sensor, driver, control) con el hardware que ya esta disponible, sin depender de que la mecanica final este lista.

## Por que esta seccion existe

El bipedo tiene piezas que tardan (mecanica, servos nuevos). Mientras tanto se puede validar codigo/electronica critica reusando hardware ya disponible (ej: L298N + TT motors, que no van en las piernas pero sirven de plataforma de pruebas). Esto reduce riesgo: cuando llegue el momento de integrar todo, el codigo de sensores/control ya esta probado por separado.

## Convencion de cada test

Cada test vive en su propia carpeta `test-NN-nombre-descriptivo/` con:
- `README.md` — objetivo, hardware requerido, wiring, como correrlo, criterio de exito/fallo, troubleshooting.
- Codigo fuente (`.ino` u otro) — listo para flashear, con comentarios donde el "por que" no es obvio (constantes de calibracion, tuning, seguridad).

## Indice de tests

| # | Test | Componente probado | Estado |
|---|---|---|---|
| 01 | [mpu6050-balance-ruedas](test-01-mpu6050-balance-ruedas/) | MPU-6050 + PID de balance, usando L298N + TT motors como plataforma provisoria (controlador: ESP8266/Wemos D1 mini, Arduino) | Sensor+sentido validados, en tuning |
| 02 | [calibracion-pid](test-02-calibracion-pid/) | Mismo hardware que 01, firmware con comandos por Serial para tunear KP/KI/KD/SETPOINT_ANGLE en vivo sin reflashear, con guardado en EEPROM | Listo para usar |

## Relacion con el firmware final

La logica de lectura de IMU + filtro complementario + PID probada aca es la misma que despues se traslada a `firmware/motion-controller/imu.*` y `balance.*` (ver [firmware/arquitectura-firmware.md](../firmware/arquitectura-firmware.md)), solo que actuando sobre motores de rueda en vez de servos de pierna. Validar el loop de balance en ruedas primero es mas rapido/barato que esperar a tener las piernas armadas para descubrir si el PID o la lectura de IMU tienen problemas.
