# Arquitectura de sistema

## Vision general (nodos)

```
                     ┌───────────────────────────┐
                     │     ESP32 DevKit v1        │
                     │   "Motion Controller"      │
                     │  (NUEVO - cerebro locomocion)│
                     ├───────────────────────────┤
                     │ - Lee MPU-6050 (I2C)       │
                     │ - Loop de balance          │
                     │ - Genera trayectorias      │
                     │ - Controla PCA9685 (I2C)   │
                     │   -> 12x servo piernas      │
                     └───────────┬───────────────┘
                                 │ WiFi (ESP-NOW o MQTT local)
                 ┌───────────────┼───────────────────┐
                 │                                   │
     ┌───────────▼───────────┐           ┌───────────▼───────────┐
     │ Wemos D1 mini (ESP8266)│           │   ESP32-CAM            │
     │  "Head Node" (existente)│           │  "Vision Node" (existente)│
     ├────────────────────────┤           ├────────────────────────┤
     │ - OLED SH1106 (cara)   │           │ - Streaming/captura     │
     │ - MAX9814 mic          │           │ - Reconocimiento (fase 2)│
     │ - PAM8403 + speaker    │           └────────────────────────┘
     │ - 2x servo pan/tilt    │
     │   (cuello/cabeza)      │
     └────────────────────────┘
```

## Por que 3 microcontroladores y no 1

- Ya existen 2 (Wemos D1 mini, ESP32-CAM) corriendo el subsistema de cabeza de robotCreeper — no se reescribe lo que ya funciona.
- El loop de balance (leer IMU + corregir servos) necesita correr rapido y sin bloqueos de red/camara -> se aisla en su propio ESP32 dedicado.
- Comunicacion entre nodos es de bajo trafico (comandos: "mirar arriba", "decir frase", "expresion feliz") -> WiFi local alcanza, no hace falta bus fisico entre cabeza y cuerpo (mas facil de ensamblar mecanicamente).

## Main loop del Motion Controller (ESP32 nuevo)

1. Leer IMU (angulo pitch/roll del torso).
2. Calcular correccion (PID simple sobre tobillos/cadera).
3. Actualizar posiciones objetivo de los 12 servos via PCA9685.
4. Si hay comando de marcha activo, avanzar siguiente frame de la secuencia de pasos precalculada.
5. Publicar estado (parado/caminando/caido) a Wemos D1 mini para que la cara reaccione (ej: cara de esfuerzo al caminar, cara de "auch" si se cae).

## Alimentacion (resumen, detalle en electronica/presupuesto-energia.md)

- Rail servos (piernas): bateria dedicada 6-7.4V, alta corriente.
- Rail logica (ESP32, ESP8266, sensores): 5V/3.3V regulado, separado del rail de servos.
- Cabeza (pan/tilt + OLED + audio): puede compartir rail de logica, son cargas chicas.

## Que pasa con el hardware que NO se usa en el bipedo

- **L298N + 4x TT motors**: no aplican a piernas (son para ruedas). Se guardan para otro proyecto (rover) o como base de pruebas temporal del ESP32 nuevo antes de tener piernas armadas. Ver [04-riesgos-decisiones.md](04-riesgos-decisiones.md).
