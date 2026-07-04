# Diseño estructural

## Dimension objetivo
40-80cm de alto total (torso + piernas + cabeza existente). Recomendado apuntar a **~50-60cm** para primera version: suficientemente grande para alojar componentes, suficientemente chico para minimizar torque necesario en servos economicos (menos alto = menos palanca = menos torque requerido).

## DOF por pierna — comparacion

### Opcion A (default recomendado): 4 DOF/pierna = 8 total
- Cadera pitch (adelante/atras)
- Cadera roll (lateral, clave para balance lateral)
- Rodilla pitch
- Tobillo pitch
**Ventaja**: mas barato (8 servos), mas simple de controlar y debuggear. Suficiente para marcha estatica basica.
**Limitacion**: sin cadera-yaw no gira facil sobre su eje; sin tobillo-roll el balance lateral fino depende solo de cadera-roll.

### Opcion B (upgrade futuro): 6 DOF/pierna = 12 total
Agrega cadera yaw + tobillo roll. Mejor marcha, giros mas naturales, mejor balance — pero mas caro, mas peso, mas complejo de calibrar. Dejar para fase posterior si Opcion A resulta limitada (ver docs/03-roadmap-fases.md fase 3).

## Materiales (de mas economico a mas robusto)

1. **Carton pluma / MDF liviano cortado**: mas barato, mas rapido de iterar, suficiente para prototipo funcional. Riesgo: menor durabilidad, flexion en piezas largas.
2. **PLA impreso 3D (infill 15-20%)**: buen balance costo/rigidez, permite piezas con encastres para servos (cuernos de servo, bisagras). Recomendado si hay acceso a impresora 3D.
3. **Aluminio/acrilico cortado laser**: mas robusto y durable, mas caro y requiere mas herramental. Considerar solo si el proyecto escala mas alla de portfolio inicial.

**Default recomendado**: PLA impreso 3D si hay impresora disponible (mejor para encastre de servos), carton pluma/MDF como alternativa cero-inversion si no.

## Distribucion de peso

- Bateria(s) y componentes pesados (PCA9685, cableado) ubicar lo mas bajo posible (cerca de cadera/pies) para bajar centro de masa -> mejora estabilidad y reduce torque necesario en tobillos.
- Cabeza (ESP32-CAM + OLED + mic + amp + 2 servos pan/tilt) es la carga mas alta del robot — mantenerla lo mas liviana posible, ya que su peso multiplica el torque exigido en cadera/tobillo por efecto palanca.

## Rango de movimiento minimo por articulacion (referencia inicial, ajustar en pruebas)

| Articulacion | Rango |
|---|---|
| Cadera pitch | ±40° |
| Cadera roll | ±20° |
| Rodilla pitch | 0° a 90° (no hiperextender) |
| Tobillo pitch | ±30° |

## Validacion mecanica antes de firmware de marcha

1. Mover cada servo manualmente (sin carga) y confirmar rango sin choques mecanicos entre piezas.
2. Parar el robot sostenido a mano, confirmar que geometria de piernas permite centro de masa dentro del area de apoyo de los pies.
3. Pesar el robot completo armado — validar contra torque real de servos (ver docs/04-riesgos-decisiones.md, riesgo de torque insuficiente).
