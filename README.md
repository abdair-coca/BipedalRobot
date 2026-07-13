# Bipedal Robot

Robot bipedo mediano (40-80cm) — proyecto portfolio/demo tecnico dentro del workspace **robotCreeper**.
Reutiliza y extiende el hardware/software ya desarrollado en robotCreeper (cabeza con camara, voz y cara OLED) montandolo sobre un cuerpo bipedo nuevo con piernas motorizadas y control de balance.

## Estructura del proyecto

| Carpeta | Contenido |
|---|---|
| [`docs/`](docs/) | Vision, alcance, arquitectura de sistema, roadmap, decisiones y riesgos |
| [`mecanica/`](mecanica/) | Diseno estructural, DOF de piernas, materiales |
| [`electronica/`](electronica/) | BOM, presupuesto energetico, conexionado |
| [`firmware/`](firmware/) | Arquitectura de firmware (ESP32 principal + nodos) |
| [`software/`](software/) | Control de marcha, cinematica, simulacion (a definir) |
| [`gestion/`](gestion/) | Backlog y milestones del proyecto |
| [`tests/`](tests/) | Tests de componentes especificos, aislados del firmware final |
| [`quadruped_rl_sim/`](quadruped_rl_sim/) | Experimento aislado: sim PyBullet+RL (PPO) de marcha en un cuadrupedo 12 DOF, previo a portar el enfoque al bipedo real |

## Punto de partida

- Empieza por [`docs/01-vision-alcance.md`](docs/01-vision-alcance.md)
- Arquitectura general en [`docs/02-arquitectura-sistema.md`](docs/02-arquitectura-sistema.md)
- Roadmap de fases en [`docs/03-roadmap-fases.md`](docs/03-roadmap-fases.md)
