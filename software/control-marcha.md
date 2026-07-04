# Control de marcha

## Enfoque general: marcha estatica por poses precalculadas (sin cinematica inversa compleja)

Para 4 DOF/pierna (cadera pitch, cadera roll, rodilla pitch, tobillo pitch) no hace falta resolver cinematica inversa general — alcanza con definir a mano una secuencia de **poses clave** (keyframes) y interpolar entre ellas. Es el enfoque estandar en bipedos hobby economicos.

## Definicion de pose

Una pose = angulo objetivo para cada uno de los 8 servos, en un instante del ciclo de paso.

```
Pose = {
  hip_pitch_L, hip_roll_L, knee_L, ankle_L,
  hip_pitch_R, hip_roll_R, knee_R, ankle_R
}
```

## Ciclo de paso basico (secuencia de poses, simetrica izq/der)

1. **Pose neutral**: parado, peso distribuido 50/50, piernas rectas.
2. **Transferir peso** a pierna de apoyo (ej. derecha): inclinar cadera-roll hacia el lado de apoyo.
3. **Levantar pierna libre** (izquierda): flexionar rodilla + cadera pitch hacia adelante, tobillo compensa para despegar el pie del piso.
4. **Avanzar pierna libre**: cadera pitch sigue moviendose adelante mientras la pierna esta en el aire.
5. **Apoyar pierna libre**: extender rodilla, bajar pie, tobillo ajusta para apoyo plano.
6. **Transferir peso** a la pierna que acaba de apoyar (ahora izquierda es de apoyo).
7. Repetir simetrico con la otra pierna.

Cada paso de la secuencia se interpola linealmente (o con suavizado tipo ease-in-out) entre pose anterior y siguiente, en N frames, para movimiento suave y no brusco (brusco = mas riesgo de caida y mas estres en servos economicos).

## Ajuste fino (se hace empiricamente en fase 3, no se puede calcular perfecto de antemano)

- **Timing**: cuanto dura cada fase del paso (ms) — empezar lento (500-800ms por fase) e ir acelerando conforme se valida estabilidad.
- **Amplitud de transferencia de peso**: cuanto se inclina la cadera-roll antes de levantar la pierna — insuficiente = se cae al levantar el pie; excesivo = se desestabiliza hacia el lado de apoyo.
- **Compensacion con IMU en tiempo real**: la secuencia de poses da la "forma" del paso, pero el PID de balance (firmware/arquitectura-firmware.md) corrige sobre esa forma en tiempo real segun el angulo real medido — no seguir la secuencia ciegamente si el IMU detecta desbalance.

## Herramienta de calibracion sugerida (opcional, acelera fase 2-3)

Script simple (Python o web serial) que permite mover cada servo individualmente desde una PC via serial, para:
- Encontrar visualmente los angulos clave de cada pose sin tener que editar y re-flashear firmware cada vez.
- Guardar la secuencia final como constantes en `gait.cpp`.

## Fuera de alcance (fase futura, no bloquea portfolio)

- ZMP (Zero Moment Point) dinamico completo.
- Aprendizaje por refuerzo para la marcha.
- Marcha adaptativa a terreno irregular.
