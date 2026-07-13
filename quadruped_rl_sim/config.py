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
# MASAS: TODO -- no hay peso real todavia (pesar el chasis/patas impresos +
# servos + bateria en balanza). Valores placeholder chicos, coherentes con
# un chasis de este tamano en impresion 3D + servos tipo SG90/MG90S, pero
# NO son una medicion real. Reemplazar apenas se pese el robot.
BODY_MASS = 0.25       # [kg] PLACEHOLDER

# ---------------------------------------------------------------------------
# GEOMETRIA DE PATA (misma para las 4 patas; cambia solo el signo del
# offset de montaje en el torso)
# ---------------------------------------------------------------------------
# Link "hip": stub corto que separa el eje de abduccion (X) del eje de
# pitch (Y). Representa el bracket de cadera real (bounding box 38.1 x
# 43.35 x 38.1mm medido en SketchUp -- se toma el lado mas largo como
# longitud del stub y se promedia el resto para el radio del cilindro).
HIP_LINK_LENGTH = 0.04335   # [m] 43.35mm medido
HIP_LINK_RADIUS = 0.01905   # [m] promedio de 38.1mm / 2
HIP_LINK_MASS = 0.04        # [kg] PLACEHOLDER, ver nota de masas arriba

# Femur (muslo): del hip_pitch a la rodilla. Bounding box medido 29.27 x
# 53.25 x 19.83mm -- el lado mas largo (53.25mm) es el alcance real del
# link (el bounding box de SketchUp no viene alineado a longitud/ancho/alto
# funcional porque la pieza esta rotada en el ensamble).
FEMUR_LENGTH = 0.05325   # [m] 53.25mm medido (lado mas largo del bounding box)
FEMUR_RADIUS = 0.0123    # [m] promedio de 29.27/19.83mm / 2
FEMUR_MASS = 0.03        # [kg] PLACEHOLDER, ver nota de masas arriba

# Tibia (pantorrilla/pie, pieza unica en este diseno): bounding box medido
# 77.16 x 38.26 x 23.83mm.
TIBIA_LENGTH = 0.07716   # [m] 77.16mm medido
TIBIA_RADIUS = 0.0155    # [m] promedio de 38.26/23.83mm / 2
TIBIA_MASS = 0.03        # [kg] PLACEHOLDER, ver nota de masas arriba

# Pie: esfera chica fija en la punta de la tibia (mejor contacto/friccion
# que un borde de cilindro). El diseno real integra el pie en la misma
# pieza que la tibia, esto queda como aproximacion de la punta de contacto.
FOOT_RADIUS = 0.012  # [m]
FOOT_MASS = 0.01     # [kg] PLACEHOLDER, ver nota de masas arriba

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
# Alcance vertical maximo de la pata = FEMUR_LENGTH + TIBIA_LENGTH = ~130mm
# (con las medidas reales de arriba); target ~75% de eso, extendida pero no
# al limite.
TARGET_STANDING_HEIGHT = 0.098  # [m]

# Angulos de pata (grados) que producen aproximadamente TARGET_STANDING_HEIGHT
# con el robot parado quieto. Se usan como pose inicial en cada reset() del
# entorno, asi el episodio no arranca en una configuracion rara/inestable.
STANDING_HIP_ABDUCTION_DEG = 0.0
STANDING_HIP_PITCH_DEG = -20.0
STANDING_KNEE_DEG = 60.0

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
