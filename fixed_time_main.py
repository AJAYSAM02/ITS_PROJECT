from __future__ import absolute_import
from __future__ import print_function

import os
import datetime
from shutil import copyfile

from generator import TrafficGenerator
from visualization import Visualization
from utils import import_fixed_time_configuration, set_sumo
from fixed_time_simulation import Simulation


if __name__ == "__main__":

    config = import_fixed_time_configuration(config_file='fixed_time_settings.ini')
    sumo_cmd = set_sumo(config['gui'], config['sumocfg_file_name'], config['max_steps'])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = os.path.join(os.getcwd(), "fixed_time", "run_" + timestamp, "")
    os.makedirs(plot_path, exist_ok=True)

    TrafficGen = TrafficGenerator(
        config['max_steps'],
        config['n_cars_generated']
    )

    Visualization = Visualization(
        plot_path,
        dpi=96
    )

    Simulation = Simulation(
        TrafficGen,
        sumo_cmd,
        config['max_steps'],
        config['green_duration'],
        config['yellow_duration']
    )

    print('\n----- Fixed-time test episode')
    simulation_time = Simulation.run(config['episode_seed'])

    print('\n----- Run summary -----')
    print('Average queue length:', round(Simulation.avg_queue_length, 3))
    print('Total waiting time:', round(Simulation.total_waiting_time, 3))
    print('Total reward:', round(Simulation.total_reward, 3))
    print('Simulation time:', simulation_time, 's')

    print("\n----- Testing info saved at:", plot_path)

    copyfile(src='fixed_time_settings.ini', dst=os.path.join(plot_path, 'fixed_time_settings.ini'))

    Visualization.save_data_and_plot(
        data=Simulation.reward_episode,
        filename='reward',
        xlabel='Action step',
        ylabel='Reward'
    )

    Visualization.save_data_and_plot(
        data=Simulation.queue_length_episode,
        filename='queue',
        xlabel='Step',
        ylabel='Queue length (vehicles)'
    )

    with open(os.path.join(plot_path, 'summary.txt'), 'w') as f:
        f.write(f"Average queue length: {round(Simulation.avg_queue_length, 3)}\n")
        f.write(f"Total waiting time: {round(Simulation.total_waiting_time, 3)}\n")
        f.write(f"Total reward: {round(Simulation.total_reward, 3)}\n")
        f.write(f"Simulation time: {simulation_time} s\n")