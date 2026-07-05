# Roadmap por fases

## Fase 0 — Prep y validacion de electronica (1-2 semanas)
- Validar ESP32 DevKit + PCA9685 + 1-2 servos de prueba (loop basico de PWM).
- Validar lectura de MPU-6050 (angulos pitch/roll estables, sin drift grave).
- Confirmar que subsistema de cabeza (Wemos D1 mini + OLED + mic + amp) sigue funcionando standalone.
- Salida: banco de pruebas electronico funcionando en mesa (sin estructura fisica aun).

## Fase 1 — Mecanica de piernas (2-4 semanas)
- Definir DOF final por pierna (ver [mecanica/diseno-estructural.md](../mecanica/diseno-estructural.md)).
- Diseñar y validar el modelo 3D completo antes de imprimir (ver [mecanica/plan-diseno-3d.md](../mecanica/plan-diseno-3d.md)).
- Modelar/imprimir o cortar piezas de piernas + torso.
- Montar 12 servos + estructura, sin electronica final aun (solo prueba mecanica de rango de movimiento a mano).
- Salida: estructura bipeda armada, se puede mover manualmente cada articulacion.

## Fase 2 — Balance estatico (2-3 semanas)
- Firmware: loop de lectura IMU + PID simple sobre tobillos/cadera.
- Robot se sostiene parado sin caerse, corrige perturbaciones chicas (empujones leves).
- Salida: robot parado solo >30s sin asistencia.

## Fase 3 — Marcha estatica (3-5 semanas)
- Generar secuencia de pasos precalculada (cinematica inversa simple, ver [software/control-marcha.md](../software/control-marcha.md)).
- Ajustar timing y balance de peso entre piernas durante el paso.
- Salida: robot camina 3-5 pasos en linea recta sin caerse.

## Fase 4 — Integracion con cabeza/robotCreeper (1-2 semanas)
- Conectar Motion Controller <-> Wemos D1 mini <-> ESP32-CAM via WiFi.
- Sincronizar expresiones de cara con estado de movimiento (parado/caminando/caido).
- Salida: robot completo, cuerpo + cabeza funcionando juntos.

## Fase 5 — Pulido y demo (1-2 semanas)
- Cableado prolijo, fijacion de baterias, carcasa/cosmetica basica.
- Grabar video demo, actualizar documentacion con fotos/resultados reales.
- Salida: demo presentable para portfolio.

## Notas
- Tiempos son estimados trabajando part-time (hobby/portfolio), ajustar segun disponibilidad real.
- Cada fase tiene su propio criterio de "salida" — no se avanza de fase sin cumplirlo, evita acumular deuda tecnica que despues es dificil debuggear (mecanica + balance mal hecho es muy dificil de diagnosticar en capas superiores).
