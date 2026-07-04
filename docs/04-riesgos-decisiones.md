# Decisiones tecnicas y riesgos

## Decisiones clave

### 1. TT motors + L298N no se usan para piernas
**Por que**: TT motors son de rotacion continua (ruedas), no dan control de posicion angular preciso que necesita una articulacion de pierna. Torque tambien insuficiente y mal distribuido para soportar peso corporal en una pierna.
**Que hacer con ellos**: quedan reservados para un futuro rover/base rodante, o como carrito de pruebas temporal para validar el ESP32 nuevo antes de tener piernas armadas (fase 0).

### 2. Servos elegidos para piernas: MG996R (o equivalente metal gear economico)
**Por que**: economicos (~$3-5 c/u), torque suficiente (~9-11 kg·cm @6V) para un bipedo de 40-80cm liviano (impreso 3D), disponibilidad alta, ampliamente documentados en proyectos DIY similares.
**Alternativa descartada**: SG90 (plastico, ~1.8kg·cm) — insuficiente para articulaciones que cargan peso (cadera, rodilla, tobillo). Sirve solo para pan/tilt de cabeza (uso actual, no cambia).
**Alternativa mas cara**: Dynamixel — mejor control (feedback de posicion, bus serie), pero 10-20x mas caro por unidad. Descartado por presupuesto ajustado, se puede migrar despues si el proyecto escala.

### 3. Cantidad de DOF por pierna: 4 (opcion economica) vs 6 (opcion completa)
Ver detalle y tradeoff en [mecanica/diseno-estructural.md](../mecanica/diseno-estructural.md). Default recomendado: **4 DOF/pierna (8 total)** para fase 1, dejar cadera-yaw y tobillo-roll como upgrade fase futura si el balance con 4 DOF resulta insuficiente.

### 4. Un ESP32 nuevo dedicado a locomocion, en vez de reusar Wemos D1 mini existente
**Por que**: el D1 mini (ESP8266) ya esta ocupado con cabeza (OLED+mic+amp+2 servos) y tiene menos pines/menor performance que ESP32. El loop de balance necesita I2C rapido (IMU) + I2C a PCA9685 sin competir con audio/display.

### 5. PCA9685 como driver de servos (nuevo, a comprar)
**Por que**: ESP32 no tiene 12 salidas PWM de hardware libres y estables simultaneamente de forma comoda: PCA9685 da 16 canales PWM dedicados via I2C, barato (~$2), estandar en proyectos de robotica con muchos servos.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Servos MG996R insuficientes en torque real (spec inflada, comun en clones baratos) | Alto — no se sostiene parado | Comprar 1-2 de mas para testear antes de pedir el lote completo; dejar margen de rediseño mecanico (reducir peso/palanca) |
| Cada de tension al mover varios servos a la vez (brownout del ESP32) | Alto — reinicios random | Rail de servos separado de rail logica (ver electronica/presupuesto-energia.md), capacitor grande en rail servos |
| Peso de estructura impresa en 3D mayor al estimado | Medio — mas torque necesario | Iterar diseno con infill bajo, materiales livianos, pesar cada pieza impresa |
| MPU-6050 con drift/ruido (clones baratos son comunes) | Medio — balance inestable | Filtro complementario o Kalman simple en firmware, calibracion en frio al encender |
| Scope creep: agregar brazos/manipulacion antes de caminar bien | Alto — proyecto nunca termina | Fuera de alcance explicito (ver vision-alcance.md), revisar backlog antes de agregar features |
| Tiempo de desarrollo subestimado (hobby, tiempo parcial) | Medio | Fases con criterio de salida claro, se puede pausar entre fases sin perder progreso |
