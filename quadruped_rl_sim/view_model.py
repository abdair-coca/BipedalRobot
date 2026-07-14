"""
Abre el URDF actual en GUI, parado en la pose de reposo de config.py, para
inspeccionar visualmente el diseno (proporciones, postura, colisiones) sin
necesidad de entrenar ni cargar ningun modelo.

Uso:
    python view_model.py

Gira la camara con el mouse (click izquierdo = orbitar, rueda = zoom,
click derecho/medio = paneo). Cerra la ventana cuando termines.

Corre `python generate_urdf.py` antes si cambiaste config.py y queres ver
la version actualizada (este script no regenera el URDF solo, para que
puedas comparar contra una version anterior si queres).
"""

import math

import pybullet as p
import pybullet_data

import config as cfg


def main():
    client = p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=client)
    p.setGravity(0, 0, -9.8, physicsClientId=client)
    p.loadURDF("plane.urdf", physicsClientId=client)

    start_pos = [0, 0, cfg.TARGET_STANDING_HEIGHT + 0.05]
    robot_id = p.loadURDF("quadruped.urdf", start_pos, useFixedBase=False, physicsClientId=client)

    name_to_index = {}
    for i in range(p.getNumJoints(robot_id, physicsClientId=client)):
        info = p.getJointInfo(robot_id, i, physicsClientId=client)
        name_to_index[info[1].decode("utf-8")] = i

    for leg in cfg.LEG_NAMES:
        for joint_type in cfg.JOINT_TYPES:
            joint_name = f"{leg}_{joint_type}_joint"
            angle = math.radians(cfg.STANDING_POSE_DEG[joint_type])
            p.resetJointState(robot_id, name_to_index[joint_name], angle, physicsClientId=client)

    p.resetDebugVisualizerCamera(
        cameraDistance=0.5, cameraYaw=35, cameraPitch=-30,
        cameraTargetPosition=[0, 0, cfg.TARGET_STANDING_HEIGHT / 2],
        physicsClientId=client,
    )

    print("Ventana abierta. Gira/zoomea con el mouse. Cerrala cuando termines.")
    while p.isConnected(client):
        p.stepSimulation(physicsClientId=client)


if __name__ == "__main__":
    try:
        main()
    except p.error:
        pass  # ventana cerrada por el usuario, salida normal
