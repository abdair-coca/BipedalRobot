# Conexionado (pinout)

## Motion Controller — ESP32 DevKit v1 (nuevo)

### I2C bus (compartido: MPU-6050 + PCA9685)
| Señal | Pin ESP32 |
|---|---|
| SDA | GPIO 21 |
| SCL | GPIO 22 |
| MPU-6050 VCC | 3.3V |
| MPU-6050 GND | GND |
| MPU-6050 addr | 0x68 (default) |
| PCA9685 VCC (logica) | 5V (rail logica) |
| PCA9685 V+ (servos) | Rail servos (bateria, NO desde ESP32) |
| PCA9685 GND | GND comun con ESP32 y con rail servos |
| PCA9685 addr | 0x40 (default) |

### Canales PCA9685 -> servos (default 8 DOF, 4 por pierna)
| Canal | Articulacion |
|---|---|
| 0 | Cadera pitch (adelante/atras) - pierna izq |
| 1 | Cadera roll (lateral) - pierna izq |
| 2 | Rodilla pitch - pierna izq |
| 3 | Tobillo pitch - pierna izq |
| 4 | Cadera pitch (adelante/atras) - pierna der |
| 5 | Cadera roll (lateral) - pierna der |
| 6 | Rodilla pitch - pierna der |
| 7 | Tobillo pitch - pierna der |
| 8-11 | Libres — reservados para upgrade a 12 DOF (cadera yaw, tobillo roll) |

### UART/debug
| Señal | Pin ESP32 |
|---|---|
| USB serie (programacion/debug) | Puerto USB integrado |

## Head Node — Wemos D1 mini (ESP8266, existente, sin cambios)
| Componente | Pin D1 mini |
|---|---|
| OLED SH1106 SDA | D2 (GPIO4) |
| OLED SH1106 SCL | D1 (GPIO5) |
| MAX9814 salida analoga | A0 |
| PAM8403 entrada audio | Salida PWM/DAC (segun implementacion actual) |
| Servo pan | D5 (GPIO14) |
| Servo tilt | D6 (GPIO12) |

*(Mantener el pinout que ya tiene robotCreeper funcionando — esta tabla es referencia, no forzar cambio si el proyecto original usa otros pines.)*

## Vision Node — ESP32-CAM (existente, sin cambios)
- Sin modificaciones, sigue con su configuracion actual de camara + WiFi.

## Comunicacion entre nodos

**Protocolo recomendado**: ESP-NOW (WiFi peer-to-peer sin router, baja latencia, ideal para comandos cortos tipo "estado=caminando").

Alternativa mas simple de implementar si ya existe infraestructura WiFi local: UDP/MQTT sobre la misma red WiFi de casa.

| Mensaje | Direccion | Contenido |
|---|---|---|
| Estado de movimiento | Motion Controller -> Head Node | `idle` / `walking` / `fallen` |
| Comando de expresion | Head Node -> Motion Controller (opcional, fase futura) | ej. reaccion a algo que ve la camara |

## Tierra comun (GND)

Todos los nodos y ambos rails de alimentacion (servos y logica) deben compartir GND comun, aunque tengan fuentes de voltaje separadas. Sin GND comun el I2C y las señales digitales no funcionan.
