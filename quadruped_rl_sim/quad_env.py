"""
Entorno Gymnasium que envuelve PyBullet para el cuadrupedo de 12 DOF.

Observacion (31,): [12 angulos rad, 12 velocidades rad/s, roll, pitch, yaw,
                     vx, vy, vz (velocidad lineal torso), altura torso]
Accion (12,): target de angulo por joint, normalizado [-1, 1], mapeado a los
              limites reales definidos en config.py (JOINT_LIMITS_RAD).
Control: POSITION_CONTROL (setJointMotorControlArray) -- el robot real usa
         servos de posicion, no de torque, asi que la politica debe emitir
         siempre angulos objetivo, nunca torques.
"""

import os

import numpy as np
import pybullet as p
import pybullet_data
import gymnasium as gym
from gymnasium import spaces

import config as cfg
import generate_urdf


N_JOINTS = len(cfg.ALL_JOINT_NAMES)  # 12
OBS_DIM = N_JOINTS + N_JOINTS + 3 + 3 + 1  # angulos + vel + rpy + linvel + altura


def _ensure_urdf(urdf_path: str) -> str:
    """Genera el URDF desde config.py si todavia no existe en disco."""
    if not os.path.exists(urdf_path):
        urdf_text = generate_urdf.build_urdf()
        with open(urdf_path, "w", encoding="utf-8") as f:
            f.write(urdf_text)
    return urdf_path


class QuadrupedEnv(gym.Env):
    metadata = {"render_modes": ["human", None]}

    def __init__(self, render_mode=None, urdf_path=None, max_episode_steps=None):
        super().__init__()
        self.render_mode = render_mode
        self.max_episode_steps = max_episode_steps or cfg.MAX_EPISODE_STEPS

        if urdf_path is None:
            urdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quadruped.urdf")
        self.urdf_path = _ensure_urdf(urdf_path)

        connect_mode = p.GUI if render_mode == "human" else p.DIRECT
        self.client = p.connect(connect_mode)
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.client)
        p.setGravity(0, 0, -9.8, physicsClientId=self.client)
        p.setTimeStep(cfg.SIM_TIMESTEP, physicsClientId=self.client)

        self.plane_id = p.loadURDF("plane.urdf", physicsClientId=self.client)

        start_pos = [0, 0, cfg.TARGET_STANDING_HEIGHT + 0.05]
        start_orn = p.getQuaternionFromEuler([0, 0, 0])
        self.robot_id = p.loadURDF(
            self.urdf_path, start_pos, start_orn,
            useFixedBase=False, physicsClientId=self.client,
        )

        self._build_joint_index_map()

        # angulos de pie objetivo (rad), en el mismo orden que ALL_JOINT_NAMES
        self.standing_angles = np.array(
            [
                np.radians(cfg.STANDING_POSE_DEG[jt])
                for _leg in cfg.LEG_NAMES
                for jt in cfg.JOINT_TYPES
            ],
            dtype=np.float32,
        )

        self.joint_low = np.array(
            [cfg.JOINT_LIMITS_RAD[jt][0] for _leg in cfg.LEG_NAMES for jt in cfg.JOINT_TYPES],
            dtype=np.float32,
        )
        self.joint_high = np.array(
            [cfg.JOINT_LIMITS_RAD[jt][1] for _leg in cfg.LEG_NAMES for jt in cfg.JOINT_TYPES],
            dtype=np.float32,
        )
        self.abduction_mask = np.array(
            [1.0 if jt == "hip_abduction" else 0.0 for _leg in cfg.LEG_NAMES for jt in cfg.JOINT_TYPES],
            dtype=np.float32,
        )

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(N_JOINTS,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(OBS_DIM,), dtype=np.float32
        )

        self.step_count = 0
        self.prev_target_angles = self.standing_angles.copy()

    # ------------------------------------------------------------------
    def _build_joint_index_map(self):
        """Mapea nombre logico ('front_left_hip_abduction', ...) -> jointIndex."""
        name_to_index = {}
        n = p.getNumJoints(self.robot_id, physicsClientId=self.client)
        for i in range(n):
            info = p.getJointInfo(self.robot_id, i, physicsClientId=self.client)
            joint_name = info[1].decode("utf-8")
            name_to_index[joint_name] = i

        self.joint_indices = []
        for leg in cfg.LEG_NAMES:
            for jt in cfg.JOINT_TYPES:
                urdf_name = f"{leg}_{jt}_joint"
                if urdf_name not in name_to_index:
                    raise RuntimeError(
                        f"Joint '{urdf_name}' no encontrado en el URDF. "
                        "Regenera quadruped.urdf con generate_urdf.py."
                    )
                self.joint_indices.append(name_to_index[urdf_name])

    # ------------------------------------------------------------------
    def _get_obs(self):
        angles = np.zeros(N_JOINTS, dtype=np.float32)
        velocities = np.zeros(N_JOINTS, dtype=np.float32)
        for k, j_idx in enumerate(self.joint_indices):
            pos, vel, _, _ = p.getJointState(self.robot_id, j_idx, physicsClientId=self.client)
            angles[k] = pos
            velocities[k] = vel

        base_pos, base_orn = p.getBasePositionAndOrientation(self.robot_id, physicsClientId=self.client)
        roll, pitch, yaw = p.getEulerFromQuaternion(base_orn)
        lin_vel, _ang_vel = p.getBaseVelocity(self.robot_id, physicsClientId=self.client)
        height = base_pos[2]

        obs = np.concatenate([
            angles,
            velocities,
            np.array([roll, pitch, yaw], dtype=np.float32),
            np.array(lin_vel, dtype=np.float32),
            np.array([height], dtype=np.float32),
        ]).astype(np.float32)
        return obs, (base_pos, (roll, pitch, yaw), lin_vel)

    # ------------------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        p.resetBasePositionAndOrientation(
            self.robot_id, [0, 0, cfg.TARGET_STANDING_HEIGHT + 0.05],
            p.getQuaternionFromEuler([0, 0, 0]), physicsClientId=self.client,
        )
        p.resetBaseVelocity(self.robot_id, [0, 0, 0], [0, 0, 0], physicsClientId=self.client)

        for k, j_idx in enumerate(self.joint_indices):
            p.resetJointState(
                self.robot_id, j_idx, targetValue=self.standing_angles[k],
                targetVelocity=0.0, physicsClientId=self.client,
            )

        self.step_count = 0
        self.prev_target_angles = self.standing_angles.copy()

        obs, _ = self._get_obs()
        return obs, {}

    # ------------------------------------------------------------------
    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float32), -1.0, 1.0)
        target_angles = self.joint_low + (action + 1.0) * 0.5 * (self.joint_high - self.joint_low)

        p.setJointMotorControlArray(
            self.robot_id, self.joint_indices, p.POSITION_CONTROL,
            targetPositions=target_angles.tolist(),
            forces=[cfg.JOINT_MAX_TORQUE] * N_JOINTS,
            positionGains=[0.3] * N_JOINTS,
            velocityGains=[1.0] * N_JOINTS,
            physicsClientId=self.client,
        )

        for _ in range(cfg.CONTROL_DECIMATION):
            p.stepSimulation(physicsClientId=self.client)

        obs, (base_pos, (roll, pitch, yaw), lin_vel) = self._get_obs()

        height = base_pos[2]
        fell = (
            height < cfg.MIN_TORSO_HEIGHT
            or abs(np.degrees(roll)) > cfg.MAX_ROLL_PITCH_DEG
            or abs(np.degrees(pitch)) > cfg.MAX_ROLL_PITCH_DEG
        )

        energy = np.sum(np.abs(target_angles - self.prev_target_angles))
        lateral = abs(lin_vel[1]) + float(np.mean(np.abs(target_angles) * self.abduction_mask))

        reward = 0.0
        reward += cfg.REWARD_FORWARD_VELOCITY_WEIGHT * lin_vel[0]
        reward += cfg.REWARD_ALIVE_BONUS
        reward -= cfg.REWARD_ENERGY_WEIGHT * energy
        reward -= cfg.REWARD_LATERAL_PENALTY_WEIGHT * lateral
        if fell:
            reward -= cfg.REWARD_FALL_PENALTY

        self.prev_target_angles = target_angles
        self.step_count += 1

        terminated = bool(fell)
        truncated = self.step_count >= self.max_episode_steps

        info = {"fell": fell, "height": height, "forward_velocity": lin_vel[0]}
        return obs, float(reward), terminated, truncated, info

    # ------------------------------------------------------------------
    def render(self):
        # con render_mode="human" la ventana GUI de PyBullet ya se actualiza
        # sola en cada stepSimulation; no hace falta nada extra aca.
        return None

    def close(self):
        if p.isConnected(self.client):
            p.disconnect(self.client)
