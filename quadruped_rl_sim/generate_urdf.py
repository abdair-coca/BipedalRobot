"""
Genera quadruped.urdf a partir de los parametros en config.py.

No hay ninguna medida hardcodeada aca: todo (largos, radios, masas,
limites de joint, offsets de montaje) sale de config.py. Corre este
script cada vez que cambies config.py para regenerar el URDF.

Uso:
    python generate_urdf.py [ruta_salida.urdf]

Geometria: solo primitivas (box/cylinder/sphere), sin mallas, para que
la simulacion de colisiones sea rapida y no dependa de archivos .stl.

Convencion de cada link de pata (ver docstring de config.py para ejes):
  torso --(hip_abduction, eje X)--> hip_link --(hip_pitch, eje Y)--> femur
        --(knee, eje Y)--> tibia --(fixed)--> foot
"""

import math
import sys

import config as cfg


# ---------------------------------------------------------------------------
# Helpers de inercia (formulas estandar para primitivas solidas y
# homogeneas). ixx/iyy/izz estan expresados en el frame LOCAL de la forma
# (cilindro con eje largo en Z, caja con lados x/y/z, esfera). Cuando el
# link tiene una rotacion (rpy) en su <collision>/<visual>, se aplica la
# misma rpy en <inertial> para que PyBullet reoriente el tensor correctamente.
# ---------------------------------------------------------------------------
def box_inertia(mass, x, y, z):
    ixx = mass / 12.0 * (y ** 2 + z ** 2)
    iyy = mass / 12.0 * (x ** 2 + z ** 2)
    izz = mass / 12.0 * (x ** 2 + y ** 2)
    return ixx, iyy, izz


def cylinder_inertia(mass, radius, length):
    ixx = iyy = mass / 12.0 * (3.0 * radius ** 2 + length ** 2)
    izz = 0.5 * mass * radius ** 2
    return ixx, iyy, izz


def sphere_inertia(mass, radius):
    i = 2.0 / 5.0 * mass * radius ** 2
    return i, i, i


def inertial_xml(mass, ixx, iyy, izz, xyz="0 0 0", rpy="0 0 0"):
    # mass minima para evitar masas 0/negativas si el usuario pone un valor
    # invalido en config.py (PyBullet no tolera masa <= 0 en links moviles).
    mass = max(mass, 1e-6)
    return f"""    <inertial>
      <origin xyz="{xyz}" rpy="{rpy}"/>
      <mass value="{mass:.6f}"/>
      <inertia ixx="{ixx:.9f}" ixy="0" ixz="0" iyy="{iyy:.9f}" iyz="0" izz="{izz:.9f}"/>
    </inertial>
"""


def box_link(name, x, y, z, mass, material="torso_mat"):
    ixx, iyy, izz = box_inertia(mass, x, y, z)
    return f"""  <link name="{name}">
{inertial_xml(mass, ixx, iyy, izz)}    <visual>
      <geometry><box size="{x} {y} {z}"/></geometry>
      <material name="{material}"/>
    </visual>
    <collision>
      <geometry><box size="{x} {y} {z}"/></geometry>
    </collision>
  </link>
"""


def cylinder_link(name, radius, length, mass, xyz="0 0 0", rpy="0 0 0", material="leg_mat"):
    """Cilindro cuyo eje largo (Z local) queda orientado/posicionado por rpy/xyz."""
    ixx, iyy, izz = cylinder_inertia(mass, radius, length)
    return f"""  <link name="{name}">
{inertial_xml(mass, ixx, iyy, izz, xyz=xyz, rpy=rpy)}    <visual>
      <origin xyz="{xyz}" rpy="{rpy}"/>
      <geometry><cylinder radius="{radius}" length="{length}"/></geometry>
      <material name="{material}"/>
    </visual>
    <collision>
      <origin xyz="{xyz}" rpy="{rpy}"/>
      <geometry><cylinder radius="{radius}" length="{length}"/></geometry>
    </collision>
  </link>
"""


def sphere_link(name, radius, mass, material="foot_mat"):
    ixx, iyy, izz = sphere_inertia(mass, radius)
    return f"""  <link name="{name}">
{inertial_xml(mass, ixx, iyy, izz)}    <visual>
      <geometry><sphere radius="{radius}"/></geometry>
      <material name="{material}"/>
    </visual>
    <collision>
      <geometry><sphere radius="{radius}"/></geometry>
    </collision>
  </link>
"""


def revolute_joint(name, parent, child, axis, xyz, lower_rad, upper_rad, rpy="0 0 0"):
    return f"""  <joint name="{name}" type="revolute">
    <parent link="{parent}"/>
    <child link="{child}"/>
    <origin xyz="{xyz}" rpy="{rpy}"/>
    <axis xyz="{axis}"/>
    <limit lower="{lower_rad:.6f}" upper="{upper_rad:.6f}" effort="{cfg.JOINT_MAX_TORQUE}" velocity="{cfg.JOINT_MAX_VELOCITY}"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
"""


def fixed_joint(name, parent, child, xyz):
    return f"""  <joint name="{name}" type="fixed">
    <parent link="{parent}"/>
    <child link="{child}"/>
    <origin xyz="{xyz}" rpy="0 0 0"/>
  </joint>
"""


def servo_box_link(name):
    """Cajita chica (visual + colision) representando el cuerpo de un
    MG90S, con masa practicamente nula (la masa real ya esta contada en
    el link padre -- ver SERVO_BODY_* en config.py)."""
    return box_link(name, cfg.SERVO_BODY_LENGTH, cfg.SERVO_BODY_WIDTH,
                     cfg.SERVO_BODY_HEIGHT, 0.001, material="leg_mat")


def build_leg(leg_name):
    sign_x, sign_y = cfg.LEG_MOUNT_SIGN[leg_name]

    mount_x = sign_x * (cfg.BODY_LENGTH / 2.0 - cfg.HIP_MOUNT_INSET_X)
    mount_y = sign_y * (cfg.BODY_WIDTH / 2.0)
    mount_z = 0.0

    hip_link_name = f"{leg_name}_hip"
    femur_link_name = f"{leg_name}_femur"
    tibia_link_name = f"{leg_name}_tibia"
    foot_link_name = f"{leg_name}_foot"

    abd_joint_name = f"{leg_name}_hip_abduction_joint"
    pitch_joint_name = f"{leg_name}_hip_pitch_joint"
    knee_joint_name = f"{leg_name}_knee_joint"
    foot_joint_name = f"{leg_name}_foot_joint"

    # rotacion que alinea el eje Z local del cilindro (por defecto) con +-Y,
    # para que el stub de cadera "apunte" hacia afuera del torso.
    hip_roll = -sign_y * (math.pi / 2.0)
    hip_rpy = f"{hip_roll:.6f} 0 0"
    hip_xyz = f"0 {sign_y * cfg.HIP_LINK_LENGTH / 2.0:.6f} 0"

    xml = ""
    xml += cylinder_link(hip_link_name, cfg.HIP_LINK_RADIUS, cfg.HIP_LINK_LENGTH,
                          cfg.HIP_LINK_MASS, xyz=hip_xyz, rpy=hip_rpy)
    xml += cylinder_link(femur_link_name, cfg.FEMUR_RADIUS, cfg.FEMUR_LENGTH,
                          cfg.FEMUR_MASS, xyz=f"0 0 {-cfg.FEMUR_LENGTH / 2.0:.6f}")
    xml += cylinder_link(tibia_link_name, cfg.TIBIA_RADIUS, cfg.TIBIA_LENGTH,
                          cfg.TIBIA_MASS, xyz=f"0 0 {-cfg.TIBIA_LENGTH / 2.0:.6f}")
    xml += sphere_link(foot_link_name, cfg.FOOT_RADIUS, cfg.FOOT_MASS)

    # cajitas de servo: una en cada joint (abduccion, pitch, rodilla),
    # pegadas al link hijo justo en el origen del joint. Solo dan espacio
    # visual/colision, no aportan masa nueva.
    abd_servo_name = f"{leg_name}_abduction_servo"
    pitch_servo_name = f"{leg_name}_pitch_servo"
    knee_servo_name = f"{leg_name}_knee_servo"
    xml += servo_box_link(abd_servo_name)
    xml += servo_box_link(pitch_servo_name)
    xml += servo_box_link(knee_servo_name)

    abd_lo, abd_hi = cfg.JOINT_LIMITS_RAD["hip_abduction"]
    pitch_lo, pitch_hi = cfg.JOINT_LIMITS_RAD["hip_pitch"]
    knee_lo, knee_hi = cfg.JOINT_LIMITS_RAD["knee"]

    # rotacion de montaje (yaw, eje Z) que apunta la pata entera hacia la
    # esquina diagonal del torso en vez de derecho hacia el costado -- esto
    # es lo que da la postura "arania" (patas en X vistas desde arriba) en
    # vez de una postura "perro" (patas rectas bajo el cuerpo). El resto de
    # la cadena (abduccion, pitch, rodilla) queda igual, solo que ahora
    # actua dentro de este plano rotado.
    mount_yaw = -sign_x * sign_y * math.radians(cfg.SPIDER_SPLAY_DEG)
    mount_rpy = f"0 0 {mount_yaw:.6f}"

    # el eje de abduccion se invierte segun el lado (izq/der): por el
    # montaje diagonal (mount_yaw, con signo opuesto entre izq/der), rotar
    # ambos lados sobre el MISMO eje local con el MISMO angulo no da un
    # movimiento espejado (un lado se abre, el otro se deforma). Invertir
    # el eje local en el lado derecho hace que un mismo angulo comandado
    # produzca el mismo movimiento fisico (abrir/cerrar) en las 4 patas --
    # verificado numericamente (misma distancia/altura de pie en las 4).
    abd_axis = f"{sign_y} 0 0"

    xml += revolute_joint(abd_joint_name, "torso", hip_link_name, abd_axis,
                           f"{mount_x:.6f} {mount_y:.6f} {mount_z:.6f}", abd_lo, abd_hi,
                           rpy=mount_rpy)
    xml += revolute_joint(pitch_joint_name, hip_link_name, femur_link_name, "0 1 0",
                           f"0 {sign_y * cfg.HIP_LINK_LENGTH:.6f} 0", pitch_lo, pitch_hi)
    xml += revolute_joint(knee_joint_name, femur_link_name, tibia_link_name, "0 1 0",
                           f"0 0 {-cfg.FEMUR_LENGTH:.6f}", knee_lo, knee_hi)
    xml += fixed_joint(foot_joint_name, tibia_link_name, foot_link_name,
                        f"0 0 {-cfg.TIBIA_LENGTH:.6f}")

    xml += fixed_joint(f"{abd_servo_name}_joint", hip_link_name, abd_servo_name, "0 0 0")
    xml += fixed_joint(f"{pitch_servo_name}_joint", femur_link_name, pitch_servo_name, "0 0 0")
    xml += fixed_joint(f"{knee_servo_name}_joint", tibia_link_name, knee_servo_name, "0 0 0")

    return xml


def build_urdf():
    parts = []
    parts.append('<?xml version="1.0"?>\n')
    parts.append('<robot name="quadruped">\n\n')

    # materiales (solo visual, no afecta fisica)
    parts.append('  <material name="torso_mat"><color rgba="0.25 0.25 0.28 1"/></material>\n')
    parts.append('  <material name="leg_mat"><color rgba="0.15 0.45 0.75 1"/></material>\n')
    parts.append('  <material name="foot_mat"><color rgba="0.85 0.15 0.15 1"/></material>\n')
    parts.append('  <material name="nose_mat"><color rgba="1.0 0.9 0.0 1"/></material>\n\n')

    # torso = base link (root). Sin joint padre => PyBullet lo carga como
    # base libre (6 DOF flotantes) si loadURDF se llama con useFixedBase=False.
    parts.append(box_link("torso", cfg.BODY_LENGTH, cfg.BODY_WIDTH, cfg.BODY_HEIGHT,
                           cfg.BODY_MASS, material="torso_mat"))
    parts.append("\n")

    # marcador visual amarillo en la punta +X del torso (adelante, direccion
    # que la reward de quad_env.py premia). Solo para identificar orientacion
    # a simple vista en GUI/capturas, masa despreciable, no afecta la fisica.
    nose_size = 0.02
    parts.append(box_link("nose_marker", nose_size, nose_size, nose_size, 0.001, material="nose_mat"))
    parts.append(fixed_joint("nose_marker_joint", "torso", "nose_marker",
                              f"{cfg.BODY_LENGTH / 2.0 + nose_size / 2.0:.6f} 0 0"))
    parts.append("\n")

    for leg_name in cfg.LEG_NAMES:
        parts.append(f"  <!-- ===== pata: {leg_name} ===== -->\n")
        parts.append(build_leg(leg_name))
        parts.append("\n")

    parts.append("</robot>\n")
    return "".join(parts)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "quadruped.urdf"
    urdf_text = build_urdf()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(urdf_text)
    print(f"URDF generado: {out_path} (12 joints revolute + 4 fixed de pie + "
          f"12 fixed de cajitas de servo + 1 fixed de marcador nariz)")


if __name__ == "__main__":
    main()
