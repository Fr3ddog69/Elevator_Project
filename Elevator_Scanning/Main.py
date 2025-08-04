import sys
import pygame
import simpy
from Building import Building
import tkinter as tk
from tkinter import ttk, messagebox
from Visualization import (
    plot_travel_times_per_hour,
    plot_wait_times_per_hour,
    plot_total_travel_times_per_hour,
    plot_guest_counts_per_hour,
    plot_average_total_time_per_hour,
    append_episode_stats,
)


def get_simulation_params(param_defs):
    """
    Opens a popup window for all parameters defined in param_defs,
    returns a dictionary with converted values.
    param_defs: dict
        Key: parameter name (str)
        Value: Tuple (type, default value)
    Returns: dict with entered values
    """
    results = {}

    def on_submit():
        try:
            for name, (typ, _) in param_defs.items():
                raw = entries[name].get()
                results[name] = typ(raw)
            root.destroy()
        except Exception as e:
            messagebox.showerror(
                "Invalid input", f"Error while converting a value:\n{e}"
            )

    root = tk.Tk()
    root.title("Simulation settings")
    entries = {}

    for row, (name, (typ, default)) in enumerate(param_defs.items()):
        ttk.Label(root, text=f"{name} ({typ.__name__}):").grid(
            row=row, column=0, padx=5, pady=5, sticky="e"
        )
        entry = ttk.Entry(root)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        entries[name] = entry

    btn = ttk.Button(root, text="Start Simulation", command=on_submit)
    btn.grid(row=len(param_defs), column=0, columnspan=2, pady=10)

    root.mainloop()
    return results


def main():
    # Enter parameters via popup
    parameter_definitions = {
        "num_floors": (int, 10),
        "num_elevators": (int, 3),
        "elevator_capacity": (int, 5),
        "door_time": (float, 4),
        "building_width": (int, 600),
        "building_height": (int, 800),
        "shaft_width": (int, 60),
        "shaft_spacing": (int, 10),
        "waiting_area_width": (int, 140),
        "visualize_every": (float, 1.0),
        "max_guests": (int, 200),
        "working_time": (int, 480),
        "screen_width": (int, 800),
        "screen_height": (int, 800),
        "no_floor_zero": (str, "False"),
        "spawn_intervall": (int, 7200),
    }
    params = get_simulation_params(parameter_definitions)

    # 1) Initialize Pygame
    pygame.init()
    screen_width, screen_height = params["screen_width"], params["screen_height"]
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Elevator Simulation")

    # 2) Create SimPy environment
    env = simpy.Environment()

    # 3) Create Building instance with popup parameters
    building = Building(
        screen=screen,
        env=env,
        num_floors=params["num_floors"],
        num_elevators=params["num_elevators"],
        elevator_capacity=params["elevator_capacity"],
        door_time=params["door_time"],
        building_width=params["building_width"],
        building_height=params["building_height"],
        shaft_width=params["shaft_width"],
        shaft_spacing=params["shaft_spacing"],
        waiting_area_width=params["waiting_area_width"],
        visualize_every=params["visualize_every"],
        max_guests=params["max_guests"],
        working_time=params["working_time"],
        no_floor_zero=params["no_floor_zero"],
        spawn_intervall=params["spawn_intervall"],
    )

    # 4) Run simulation until stop_event
    env.process(building.run())
    env.run(until=building.stop_event)

    # Visualization of results
    ep = 11
    plot_wait_times_per_hour(building.logs, ep)
    plot_travel_times_per_hour(building.logs, ep)
    plot_total_travel_times_per_hour(building.logs, ep)
    plot_guest_counts_per_hour(building.logs, ep)
    plot_average_total_time_per_hour(building.logs, ep)
    append_episode_stats(building.logs, ep)
    # 5) Cleanup
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
