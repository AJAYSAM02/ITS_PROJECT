
import traci
import numpy as np
import random
import timeit
import os
import sys
import configparser

PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6
PHASE_EWL_YELLOW = 7


class Simulation:
    def __init__(self, TrafficGen, sumo_cmd, max_steps, green_duration, yellow_duration):
        self._TrafficGen = TrafficGen
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration

        self._step = 0
        self._queue_length_episode = []
        self._reward_episode = []

        self._sum_queue_length = 0
        self._sum_waiting_time = 0
        self._sum_reward = 0
        self._waiting_times = {}

    def run(self, episode):
        start_time = timeit.default_timer()

        self._TrafficGen.generate_routefile(seed=episode)
        traci.start(self._sumo_cmd)
        print("Simulating fixed-time...")

        self._step = 0
        self._queue_length_episode = []
        self._reward_episode = []
        self._sum_queue_length = 0
        self._sum_waiting_time = 0
        self._sum_reward = 0
        self._waiting_times = {}

        old_total_wait = 0
        phase_cycle = [0, 1, 2, 3]
        cycle_index = 0

        while self._step < self._max_steps:
            current_total_wait = self._collect_waiting_times()
            reward = old_total_wait - current_total_wait
            self._reward_episode.append(reward)
            self._sum_reward += reward
            old_total_wait = current_total_wait

            action = phase_cycle[cycle_index % len(phase_cycle)]

            self._set_green_phase(action)
            self._simulate(self._green_duration)

            if self._step < self._max_steps:
                self._set_yellow_phase(action)
                self._simulate(self._yellow_duration)

            cycle_index += 1

        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)
        return simulation_time

    def _simulate(self, steps_todo):
        if (self._step + steps_todo) >= self._max_steps:
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()
            self._step += 1
            steps_todo -= 1

            queue_length = self._get_queue_length()
            self._queue_length_episode.append(queue_length)
            self._sum_queue_length += queue_length
            self._sum_waiting_time += queue_length

    def _collect_waiting_times(self):
        incoming_roads = ["E2TL", "N2TL", "W2TL", "S2TL"]
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)

            if road_id in incoming_roads:
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times:
                    del self._waiting_times[car_id]

        total_waiting_time = sum(self._waiting_times.values())
        return total_waiting_time

    def _set_yellow_phase(self, old_action):
        yellow_phase_code = old_action * 2 + 1
        traci.trafficlight.setPhase("TL", yellow_phase_code)

    def _set_green_phase(self, action_number):
        if action_number == 0:
            traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
        elif action_number == 1:
            traci.trafficlight.setPhase("TL", PHASE_NSL_GREEN)
        elif action_number == 2:
            traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
        elif action_number == 3:
            traci.trafficlight.setPhase("TL", PHASE_EWL_GREEN)

    def _get_queue_length(self):
        halt_N = traci.edge.getLastStepHaltingNumber("N2TL")
        halt_S = traci.edge.getLastStepHaltingNumber("S2TL")
        halt_E = traci.edge.getLastStepHaltingNumber("E2TL")
        halt_W = traci.edge.getLastStepHaltingNumber("W2TL")
        return halt_N + halt_S + halt_E + halt_W

    @property
    def queue_length_episode(self):
        return self._queue_length_episode

    @property
    def reward_episode(self):
        return self._reward_episode

    @property
    def total_reward(self):
        return self._sum_reward

    @property
    def total_waiting_time(self):
        return self._sum_waiting_time

    @property
    def avg_queue_length(self):
        if self._step == 0:
            return 0
        return self._sum_queue_length / self._step