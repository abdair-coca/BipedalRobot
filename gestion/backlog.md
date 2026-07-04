# Backlog

Organizado por fase (ver [docs/03-roadmap-fases.md](../docs/03-roadmap-fases.md)). Marcar con `[x]` al completar.

## Fase 0 — Prep y validacion de electronica
- [ ] Armar banco de pruebas: ESP32 + PCA9685 + 1 servo MG996R
- [ ] Escribir firmware minimo: mover 1 servo entre 2 angulos via PCA9685
- [ ] Conectar MPU-6050, leer y loguear angulos crudos por serial
- [ ] Implementar filtro complementario basico sobre IMU
- [ ] Confirmar Wemos D1 mini + OLED + mic + amp siguen funcionando standalone (regresion)
- [ ] Comprar 2 servos MG996R sueltos y testear torque real con carga aproximada

## Fase 1 — Mecanica de piernas
- [ ] Definir DOF final (default: 4/pierna, ver mecanica/diseno-estructural.md)
- [ ] Modelar piezas (CAD) o cortar carton pluma/MDF segun material elegido
- [ ] Imprimir/cortar piezas de pierna izquierda (prototipo)
- [ ] Validar rango de movimiento sin choques mecanicos
- [ ] Replicar para pierna derecha
- [ ] Montar torso, fijar piernas, dejar espacio para bateria y PCA9685
- [ ] Pesar robot completo armado (sin electronica final)

## Fase 2 — Balance estatico
- [ ] Implementar PID de balance (cadera-roll + tobillo-pitch) sobre lectura IMU
- [ ] Calibrar offsets de servo (trim por canal)
- [ ] Calibrar offset IMU en frio
- [ ] Probar parado libre, medir tiempo sin caerse
- [ ] Probar resistencia a perturbacion leve (empujon)
- [ ] Implementar deteccion de caida (estado `fallen`)

## Fase 3 — Marcha estatica
- [ ] Definir poses clave del ciclo de paso (ver software/control-marcha.md)
- [ ] Implementar interpolacion entre poses (`gait.cpp`)
- [ ] Ajustar timing empiricamente
- [ ] Ajustar amplitud de transferencia de peso
- [ ] Integrar correccion PID en tiempo real sobre la secuencia de marcha
- [ ] Lograr 3-5 pasos consecutivos sin caerse

## Fase 4 — Integracion con cabeza
- [ ] Implementar ESP-NOW entre Motion Controller y Head Node
- [ ] Head Node reacciona a estado (`idle`/`walking`/`fallen`) con expresion en OLED
- [ ] Validar que cabeza no interfiere con balance (peso, cableado)

## Fase 5 — Pulido y demo
- [ ] Cableado prolijo, fijar bateria(s)
- [ ] Cosmetica basica (carcasa simple si aplica)
- [ ] Grabar video demo
- [ ] Actualizar READMEs con fotos/resultados reales
- [ ] Revisar y cerrar riesgos abiertos (docs/04-riesgos-decisiones.md)
