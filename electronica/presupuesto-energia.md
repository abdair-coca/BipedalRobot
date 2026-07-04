# Presupuesto energetico

## Rails de alimentacion (separados, no compartir tierra ruidosa entre ambos sin capacitor/regulador)

### Rail 1 — Servos de piernas (alta corriente, ruidoso)
- 8x MG996R: stall current ~1.5-2A c/u en pico, tipico en movimiento ~0.5-0.9A c/u.
- Peor caso teorico (los 8 en stall simultaneo): ~12-16A — **no diseñar para este caso**, es improbable con buen firmware (evitar comandar todos los servos contra un tope a la vez).
- Diseño realista: 3-4 servos en movimiento simultaneo tipico durante un paso -> ~3-6A pico.
- **Fuente recomendada**: bateria 2S LiFePO4 6.4V con capacidad continua >5A, o pack 4xAA NiMH (4.8V) para version mas economica si el torque alcanza.
- Capacitor de 1000-2200uF en los terminales de alimentacion del PCA9685/servos para absorber picos rapidos.

### Rail 2 — Logica (ESP32, ESP8266, MPU-6050, PCA9685 logica I2C)
- ESP32 DevKit: ~160-260mA activo (WiFi transmitiendo, pico).
- ESP8266 (Wemos D1 mini): ~80-170mA activo con WiFi.
- MPU-6050: ~4mA.
- OLED SH1106: ~10-20mA.
- MAX9814 + PAM8403: ~10-100mA dependiendo de volumen.
- **Total rail logica**: <600mA en el peor caso realista.
- **Fuente recomendada**: regulador buck 5V/3A alimentado desde la misma bateria principal (o bateria separada chica), NO desde el rail de servos directo (evita brownouts que resetean el ESP32 al mover servos).

## Por que separar rails

Servos moviendose generan caidas de tension bruscas en la fuente. Si ESP32/ESP8266 comparten esa misma fuente sin regulacion propia, un movimiento brusco de servo puede resetear el microcontrolador (sintoma tipico: el robot "reinicia solo" al caminar). Separar rails (con tierra comun, pero regulacion independiente) es la solucion estandar en robotica con servos.

## Autonomia estimada

- Bateria 2S LiFePO4 ~1500-2000mAh: con consumo promedio de marcha (~2-3A promedio, no pico) da aprox. **30-45 min de uso activo** — mas que suficiente para demos/pruebas.
- Pack 4xAA NiMH ~2000mAh: similar orden de magnitud pero menor corriente maxima sostenida, valido si los servos no exigen picos altos simultaneos.

## Checklist antes de energizar todo junto

1. Medir voltaje real de bateria antes de conectar (evitar sobretension a servos/logica).
2. Probar rail logica solo (sin servos) primero.
3. Probar 1 servo solo en rail de servos, verificar que no cae tension en rail logica.
4. Recien despues conectar los 8-12 servos juntos al PCA9685.
