"""
Carga un modelo PPO entrenado (.zip de stable-baselines3) y lo corre en
modo GUI de PyBullet, en tiempo real, para ver la marcha resultante.

Uso:
    python enjoy.py checkpoints/ppo_quadruped_final.zip
    python enjoy.py checkpoints/ppo_quadruped_final.zip --episodes 5 --deterministic
"""

import argparse
import time

from stable_baselines3 import PPO

from quad_env import QuadrupedEnv
import config as cfg


def parse_args():
    p = argparse.ArgumentParser(description="Visualiza una politica entrenada en GUI.")
    p.add_argument("model_path", type=str, help="Ruta al .zip del modelo SB3.")
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--deterministic", action="store_true",
                    help="Accion determinista (media de la politica) en vez de muestreada.")
    return p.parse_args()


def main():
    args = parse_args()

    env = QuadrupedEnv(render_mode="human")
    model = PPO.load(args.model_path, env=env)

    dt_real = cfg.SIM_TIMESTEP * cfg.CONTROL_DECIMATION  # segundos "reales" por step()

    for ep in range(args.episodes):
        obs, _info = env.reset()
        terminated = truncated = False
        ep_reward = 0.0
        ep_len = 0

        while not (terminated or truncated):
            t0 = time.time()
            action, _state = model.predict(obs, deterministic=args.deterministic)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            ep_len += 1

            elapsed = time.time() - t0
            sleep_time = dt_real - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        print(f"episodio {ep + 1}: reward={ep_reward:.2f} pasos={ep_len} "
              f"cayo={info.get('fell')} altura_final={info.get('height'):.3f}")

    env.close()


if __name__ == "__main__":
    main()
