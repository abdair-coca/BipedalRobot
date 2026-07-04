# BOM (Bill of Materials)

Precios estimados en USD, referencia AliExpress/proveedor economico. Ajustar segun mercado local.

## Ya disponible (heredado de robotCreeper)

| Componente | Rol en el bipedo | Cantidad | Estado |
|---|---|---|---|
| ESP32 DevKit v1 | Puede usarse como Motion Controller nuevo | 1 | Integrado (reasignar rol) |
| ESP32-CAM | Vision Node, sin cambios | 1 | Integrado |
| SH1106 OLED 1.3" I2C | Cara del robot, sin cambios | 1 | Integrado |
| MAX9814 microfono | Entrada de voz, sin cambios | 1 | Integrado |
| PAM8403 amplificador | Salida de audio, sin cambios | 1 | Integrado |
| Servos pan/tilt (x2) | Cuello/cabeza, sin cambios | 2 | Integrado |
| Wemos D1 mini (ESP8266) | Head Node (OLED+mic+amp+pan/tilt) | 1 | Integrado |
| MPU-6050 | IMU para balance del torso — **uso nuevo** | 1 | Integrado |
| L298N driver | No aplica a piernas, reservar para otro proyecto | 1 | No usado en este proyecto |
| Motores TT (x4) | No aplica a piernas, reservar para otro proyecto | 4 | No usado en este proyecto |
| Baterias 2-5V | Reusar si alcanzan corriente, si no ver abajo | ? | Evaluar en campo |

## A comprar (piernas + locomocion)

| Componente | Rol | Cantidad | Precio est. c/u | Subtotal |
|---|---|---|---|---|
| Servo MG996R (metal gear) | Articulaciones de piernas (cadera, rodilla, tobillo) | 8-12 | ~$3.50 | $28-42 |
| PCA9685 (driver PWM 16ch I2C) | Control de todos los servos de pierna desde 1 solo bus I2C | 1 | ~$2.00 | $2.00 |
| ESP32 DevKit v1 (segundo, si el existente se deja libre para otra cosa) | Motion Controller dedicado | 0-1 | ~$4.00 | $0-4 |
| Bateria 2S LiFePO4 6.4V (o pack 4xAA NiMH 4.8-5V como alternativa mas barata) | Rail de servos (alta corriente) | 1 | ~$8-12 | $8-12 |
| Regulador buck 5V/3A (para rail logica separado) | Alimentar ESP32/ESP8266/sensores sin ruido de servos | 1 | ~$1.50 | $1.50 |
| Capacitor electrolitico grande (1000-2200uF, 16V) | Amortiguar picos de corriente en rail servos | 1-2 | ~$0.50 | $0.50-1 |
| Rodamientos/bujes chicos (opcional, mejora durabilidad de articulaciones) | Cadera/rodilla | 4-8 | ~$0.30 | $1.20-2.40 |
| Filamento PLA (estructura impresa) o carton pluma/MDF liviano (alternativa mas barata aun) | Estructura piernas + torso | ~0.5-1kg | ~$15-20/kg | $8-20 |
| Tornilleria M2/M3 variada | Ensamblaje | 1 kit | ~$3 | $3 |

**Subtotal a comprar (estimado, 8 DOF / 12 DOF)**: ~$52-88 (8 DOF) a ~$66-102 (12 DOF), dependiendo de cantidad de servos y eleccion de bateria/estructura.

## Notas de economia

- Empezar con **8 servos (4 DOF/pierna)** reduce costo ~$14-21 vs 12, y es el default recomendado (ver [docs/04-riesgos-decisiones.md](../docs/04-riesgos-decisiones.md)).
- Estructura en carton pluma/MDF o PLA con infill bajo (15-20%) es mas barata y mas liviana que aluminio — prioridad para bipedo economico.
- Pack 4xAA NiMH recargable es la opcion mas barata para rail de servos si el torque/corriente alcanza en pruebas; LiFePO4 es mejor opcion si se necesita mas corriente sostenida.
- Comprar 1-2 servos sueltos primero para testear torque real antes de pedir el lote completo (ver riesgo en docs/04-riesgos-decisiones.md).
