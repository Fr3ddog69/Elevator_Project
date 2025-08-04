import os
import pandas as pd
import matplotlib.pyplot as plt


def ensure_vis_dir():
    # Ensure the visualization directory exists
    vis_dir = "Visualizations"
    if not os.path.exists(vis_dir):
        os.makedirs(vis_dir)
    return vis_dir


def plot_wait_times_per_hour(logs, episode, filename="wait_times_per_hour_bar.png"):
    # Plot average waiting time per hour
    vis_dir = ensure_vis_dir()
    filename = os.path.join(vis_dir, f"wait_times_per_hour_ep{episode}.png")
    df = pd.DataFrame(logs)
    df = df[df["mode"] == "elevator_waiting"].copy()
    df["hour"] = (df["time"] // 3600).astype(int)
    hourly = df.groupby("hour")["wait_time"].mean().reset_index()
    hourly["wait_time"] = hourly["wait_time"].round().astype(int)
    fig, ax = plt.subplots()
    ax.bar(hourly["hour"], hourly["wait_time"])
    ax.set_xlabel("Hour (since simulation start)")
    ax.set_ylabel("Average waiting time (seconds)")
    ax.set_title(f"Average waiting time per hour (Episode {episode})")
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def plot_travel_times_per_hour(logs, episode, filename="travel_times_per_hour_bar.png"):
    # Plot average travel time per hour
    vis_dir = ensure_vis_dir()
    filename = os.path.join(vis_dir, f"travel_times_per_hour_ep{episode}.png")
    df = pd.DataFrame(logs)
    df = df[df["mode"] == "elevator_drive"].copy()
    df["start_travel_time"] = df["time"] + df["wait_time"]
    df["hour"] = (df["start_travel_time"] // 3600).astype(int)
    hourly = df.groupby("hour")["travel_time"].mean().reset_index()
    hourly["travel_time"] = hourly["travel_time"].round().astype(int)
    fig, ax = plt.subplots()
    ax.bar(hourly["hour"], hourly["travel_time"])
    ax.set_xlabel("Hour")
    ax.set_ylabel("Average travel time (seconds)")
    ax.set_title(f"Average travel time per hour (Episode {episode})")
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def plot_total_travel_times_per_hour(
    logs, episode, filename="total_travel_times_per_hour_bar.png"
):
    # Plot average total time per hour (waiting + travel)
    vis_dir = ensure_vis_dir()
    filename = os.path.join(vis_dir, f"total_travel_times_per_hour_ep{episode}.png")
    df = pd.DataFrame(logs)
    df = df[df["mode"] == "elevator_drive"].copy()
    df["total_time"] = df["wait_time"] + df["travel_time"]
    df["start_travel_time"] = df["time"]
    df["hour"] = (df["start_travel_time"] // 3600).astype(int)
    hourly = df.groupby("hour")["total_time"].mean().reset_index()
    hourly["total_time"] = hourly["total_time"].round().astype(int)
    fig, ax = plt.subplots()
    ax.bar(hourly["hour"], hourly["total_time"])
    ax.set_xlabel("Hour")
    ax.set_ylabel("Average total time (seconds)")
    ax.set_title(f"Average total time per hour (Episode {episode})")
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def plot_guest_counts_per_hour(logs, episode, filename="guest_counts_per_hour.png"):
    # Plot guest count per hour
    vis_dir = ensure_vis_dir()
    filename = os.path.join(vis_dir, f"guest_counts_per_hour_ep{episode}.png")
    df = pd.DataFrame(logs)
    df = df[df["mode"] == "elevator_drive"].copy()
    df["start_travel_time"] = df["time"] + df["wait_time"]
    df["hour"] = (df["start_travel_time"] // 3600).astype(int)
    hourly_counts = df.groupby("hour")["guest_id"].count()
    fig, ax = plt.subplots()
    ax.plot(hourly_counts.index, hourly_counts.values, marker="o", label="Elevator")
    ax.set_xlabel("Hour (since simulation start)")
    ax.set_ylabel("Number of guests")
    ax.set_title(f"Guests per hour (Episode {episode})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def plot_average_total_time_per_hour(
    logs, episode, filename="avg_total_time_per_hour.png"
):
    # Plot average total time per hour (line plot)
    vis_dir = ensure_vis_dir()
    filename = os.path.join(vis_dir, f"avg_total_time_per_hour_ep{episode}.png")
    df = pd.DataFrame(logs)
    df = df[df["mode"] == "elevator_drive"].copy()
    df["total_time"] = df["wait_time"] + df["travel_time"]
    df["start_travel_time"] = df["time"] + df["wait_time"]
    df["hour"] = (df["start_travel_time"] // 3600).astype(int)
    hourly_avg = df.groupby("hour")["total_time"].mean().reset_index()
    hourly_avg["total_time"] = hourly_avg["total_time"].round().astype(int)
    fig, ax = plt.subplots()
    ax.plot(
        hourly_avg["hour"],
        hourly_avg["total_time"],
        marker="o",
        label="Ø Total time (Elevator)",
    )
    ax.set_xlabel("Hour")
    ax.set_ylabel("Average total time (seconds)")
    ax.set_title(f"Average total time per hour (Episode {episode})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)
