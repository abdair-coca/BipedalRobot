"""
Parametros del robot cuadrupedo generico, 12 DOF (3 por pata).

TODO ESTE ARCHIVO es el unico lugar que hay que tocar cuando tengas las
medidas reales del robot fisico. generate_urdf.py, quad_env.py, train.py
y enjoy.py leen todo desde aca, no hay valores hardcodeados en otro lado.

Convenciones de ejes (frame del torso, robot mirando hacia +X):
  X = adelante/atras (longitudinal)
  Y = izquierda(+)/derecha(-) (lateral)
  Z = arriba/abajo (vertical)

Orden de las 4 patas: front_left, front_right, rear_left, rear_right.
Cadena de articulaciones por pata (padre -> hijo):
  torso -> hip_abduction (eje X) -> hip_pitch (eje Y) -> knee (eje Y) -> foot
"""

import math

# ---------------------------------------------------------------------------
# TORSO
# ---------------------------------------------------------------------------
# Caja rectangular. Medidas reales del chasis "spider-open-v1" (SketchUp,
# 2026-07-13), bounding box del cuerpo.
BODY_LENGTH = 0.14595   # [m] eje X, 145.95mm medido
BODY_WIDTH = 0.11419    # [m] eje Y, 114.19mm medido
BODY_HEIGHT = 0.040     # [m] eje Z, 40mm medido

# MASAS: estimadas (2026-07-13), no medidas en balanza -- reemplazar en
# cuanto peses el robot real. Supuestos usados para toda la estimacion:
#   - Piezas impresas en PLA: densidad efectiva ~620 kg/m3 (~50% de la
#     densidad solida del PLA, 1240 kg/m3, para compensar infill+paredes
#     tipico de brackets chicos impresos en 3D).
#   - Placa base del torso: se estima como plancha de ~4mm de espesor en
#     PLA casi solido (1240 kg/m3), no como el bounding box completo de
#     40mm (ese alto incluye la caja de bateria/parantes, no es material
#     macizo).
#   - Servo: MG90S, 13.4g cada uno (dato de hoja tecnica), 12 en total.
#   - Electronica torso: ESP32 (~10g) + driver PCA9685 (~10g) + cableado
#     y conectores (~15g) = ~35g.
#   - Bateria: generica chica sin definir todavia, placeholder ~60g
#     (equivalente a un LiPo 2S chico o 2x18650). Ajustar cuando elijas
#     la bateria real.
# Placa torso ~ 0.14595*0.11419*0.004 m3 * 1240 kg/m3 = ~83g
# + electronica ~35g + bateria ~60g => ~178g
BODY_MASS = 0.178       # [kg] ESTIMADO (plancha PLA + ESP32 + PCA9685 + bateria generica)

# ---------------------------------------------------------------------------
# GEOMETRIA DE PATA (misma para las 4 patas; cambia solo el signo del
# offset de montaje en el torso)
# ---------------------------------------------------------------------------
# Link "hip": stub corto que separa el eje de abduccion (X) del eje de
# pitch (Y). Representa el bracket de cadera real (bounding box 38.1 x
# 43.35 x 38.1mm medido en SketchUp -- se toma el lado mas largo como
# longitud del stub y se promedia el resto para el radio del cilindro).
# Lleva 2 servos MG90S montados (abduccion + hip-pitch, tipicamente
# apilados en el hombro/cadera): bracket PLA (pi*r^2*L * 620 kg/m3 = ~31g)
# + 2x13.4g servo = ~57g.
HIP_LINK_LENGTH = 0.04335   # [m] 43.35mm medido
HIP_LINK_RADIUS = 0.01905   # [m] promedio de 38.1mm / 2
HIP_LINK_MASS = 0.057       # [kg] ESTIMADO (bracket PLA + 2x servo MG90S)

# Femur (muslo): del hip_pitch a la rodilla. Bounding box medido 29.27 x
# 53.25 x 19.83mm -- el lado mas largo (53.25mm) es el alcance real del
# link (el bounding box de SketchUp no viene alineado a longitud/ancho/alto
# funcional porque la pieza esta rotada en el ensamble).
# Lleva 1 servo MG90S montado en la punta (actua la rodilla): bracket PLA
# (~16g) + 1x13.4g servo = ~29g.
FEMUR_LENGTH = 0.05325   # [m] 53.25mm medido (lado mas largo del bounding box)
FEMUR_RADIUS = 0.0123    # [m] promedio de 29.27/19.83mm / 2
FEMUR_MASS = 0.029       # [kg] ESTIMADO (bracket PLA + 1x servo MG90S)

# Tibia (pantorrilla/pie, pieza unica en este diseno): bounding box medido
# 77.16 x 38.26 x 23.83mm.
# Solo PLA, sin servo propio (la rodilla la mueve el servo del femur).
TIBIA_LENGTH = 0.07716   # [m] 77.16mm medido
TIBIA_RADIUS = 0.0155    # [m] promedio de 38.26/23.83mm / 2
TIBIA_MASS = 0.036       # [kg] ESTIMADO (solo bracket PLA, sin servo)

# Pie: esfera chica fija en la punta de la tibia (mejor contacto/friccion
# que un borde de cilindro). El diseno real integra el pie en la misma
# pieza que la tibia, esto queda como aproximacion de la punta de contacto.
FOOT_RADIUS = 0.012  # [m]
FOOT_MASS = 0.005    # [kg] ESTIMADO (punta PLA/goma chica)

# Postura "arania": angulo (grados) que rota el montaje de cada pata hacia
# la esquina diagonal del torso en vez de derecho hacia el costado (ver
# imagen de referencia del diseno real). 45 = patas formando una X vista
# desde arriba, como en la CAD real. 0 = patas perpendiculares al costado
# del cuerpo (postura tipo "perro"), no es lo que queremos aca.
SPIDER_SPLAY_DEG = 45.0

# Cuanto se insetea el punto de montaje de la cadera respecto de la esquina
# del torso (para que el bracket de cadera no quede exactamente en el borde).
HIP_MOUNT_INSET_X = 0.02  # [m]

# ---------------------------------------------------------------------------
# LIMITES DE ARTICULACION (grados) -- por tipo de joint, aplican a las 4 patas
# ---------------------------------------------------------------------------
# Abduccion/aduccion de cadera (rota sobre eje X del torso): mueve la pata
# hacia adentro/afuera. Rango chico, es sobre todo para correccion lateral.
HIP_ABDUCTION_MIN_DEG = -30.0
HIP_ABDUCTION_MAX_DEG = 30.0

# Pitch de cadera (rota sobre eje Y): balanceo adelante/atras de la pata.
HIP_PITCH_MIN_DEG = -50.0
HIP_PITCH_MAX_DEG = 50.0

# Rodilla (rota sobre eje Y): 0 deg = pata estirada, valores positivos =
# rodilla flexionada. No permitimos negativo (la rodilla no flexiona "al reves").
KNEE_MIN_DEG = 10.0
KNEE_MAX_DEG = 150.0

# Limites fisicos del motor (URDF <limit effort=".." velocity="..">).
# Referencia: servo tipo MG996R entrega ~1.0-1.5 N*m a 5-6V, velocidad libre
# ~6-7 rad/s bajo carga real es menor. Ajusta a la hoja de datos de tu servo
# cuando lo elijas para el robot fisico.
JOINT_MAX_TORQUE = 1.5      # [N*m]
JOINT_MAX_VELOCITY = 6.0    # [rad/s]

# ---------------------------------------------------------------------------
# POSTURA / ALTURA DE REPOSO
# ---------------------------------------------------------------------------
# Altura objetivo del torso sobre el piso, de pie con las patas algo
# flexionadas (no estiradas del todo: mas estabilidad y rango de movimiento).
# Calculado con forward kinematics (no a ojo, ver pose de abajo): con el
# montaje diagonal de SPIDER_SPLAY_DEG, la abduccion (no el pitch) es la
# que controla que tan abierta/en diagonal queda la pata -- se barrio
# abduccion/pitch/rodilla numericamente hasta encontrar el angulo de pie
# a ~45 grados del eje X (diagonal real, no tipo perro).
TARGET_STANDING_HEIGHT = 0.107  # [m]

# Angulos de pata (grados) que producen aproximadamente TARGET_STANDING_HEIGHT
# con el robot parado quieto. Se usan como pose inicial en cada reset() del
# entorno, asi el episodio no arranca en una configuracion rara/inestable.
STANDING_HIP_ABDUCTION_DEG = 20.0   # abre la pata a la diagonal (bearing ~45 deg)
STANDING_HIP_PITCH_DEG = -10.0
STANDING_KNEE_DEG = 15.0            # pata casi estirada

# ---------------------------------------------------------------------------
# DERIVADOS (no editar a mano, se calculan solos)
# ---------------------------------------------------------------------------
JOINT_LIMITS_DEG = {
    "hip_abduction": (HIP_ABDUCTION_MIN_DEG, HIP_ABDUCTION_MAX_DEG),
    "hip_pitch": (HIP_PITCH_MIN_DEG, HIP_PITCH_MAX_DEG),
    "knee": (KNEE_MIN_DEG, KNEE_MAX_DEG),
}

JOINT_LIMITS_RAD = {
    name: (math.radians(lo), math.radians(hi))
    for name, (lo, hi) in JOINT_LIMITS_DEG.items()
}

STANDING_POSE_DEG = {
    "hip_abduction": STANDING_HIP_ABDUCTION_DEG,
    "hip_pitch": STANDING_HIP_PITCH_DEG,
    "knee": STANDING_KNEE_DEG,
}

# Nombres de pata en orden fijo. joint_order define el orden de las 12
# dimensiones de observacion/accion en quad_env.py: NO cambiar el orden
# relativo sin actualizar los indices que dependan de el.
LEG_NAMES = ["front_left", "front_right", "rear_left", "rear_right"]
JOINT_TYPES = ["hip_abduction", "hip_pitch", "knee"]

# signo del offset de montaje en el torso por pata: (signo_X, signo_Y)
# +X = adelante, +Y = izquierda
LEG_MOUNT_SIGN = {
    "front_left": (+1, +1),
    "front_right": (+1, -1),
    "rear_left": (-1, +1),
    "rear_right": (-1, -1),
}

# Lista ordenada de los 12 joints tal cual apareceran en obs/accion.
ALL_JOINT_NAMES = [
    f"{leg}_{joint}" for leg in LEG_NAMES for joint in JOINT_TYPES
]

# ---------------------------------------------------------------------------
# TERMINACION / REWARD (entorno RL) -- no son parametros del robot fisico,
# pero viven aca para tener un solo lugar de configuracion del experimento.
# ---------------------------------------------------------------------------
MIN_TORSO_HEIGHT = 0.045     # [m] si el torso baja de esto, cae -> terminate
MAX_ROLL_PITCH_DEG = 45.0    # [deg] si roll o pitch superan esto -> terminate
MAX_EPISODE_STEPS = 1000

REWARD_FORWARD_VELOCITY_WEIGHT = 1.0
REWARD_ALIVE_BONUS = 0.05
REWARD_ENERGY_WEIGHT = 0.01
REWARD_LATERAL_PENALTY_WEIGHT = 0.05
REWARD_FALL_PENALTY = 10.0

# Frecuencia de simulacion / control
SIM_TIMESTEP = 1.0 / 240.0   # [s] paso interno de PyBullet
CONTROL_DECIMATION = 4        # pasos de fisica por cada step() del entorno
                               # (240/4 = 60 Hz de control, similar a un servo real)
