import os
import pandas as pd
import matplotlib.pyplot as plt


def ensure_vis_dir():
    vis_dir = "Visualizations"
    if not os.path.exists(vis_dir):
        os.makedirs(vis_dir)
    return vis_dir


def plot_wait_times_per_hour(logs, episode, filename="wait_times_per_hour_bar.png"):
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
        label="Ø total time (elevator)",
    )
    ax.set_xlabel("Hour")
    ax.set_ylabel("Average total time (seconds)")
    ax.set_title(f"Average total time per hour (Episode {episode})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


import os
import pandas as pd


def append_episode_stats(logs, episode):
    # Create directory (if you still want this)
    stats_dir = "EpisodeStats"
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    filename = os.path.join(stats_dir, "all_episode_stats.txt")

    df = pd.DataFrame(logs)

    # Waiting time: all with mode == elevator_waiting
    wait_df = df[df["mode"] == "elevator_waiting"]
    avg_wait_time = wait_df["wait_time"].mean() if not wait_df.empty else 0

    # Travel time: all with mode == elevator_drive
    drive_df = df[df["mode"] == "elevator_drive"]
    avg_travel_time = drive_df["travel_time"].mean() if not drive_df.empty else 0

    # Total time: all with mode == elevator_drive
    if not drive_df.empty:
        avg_total_time = (drive_df["wait_time"] + drive_df["travel_time"]).mean()
    else:
        avg_total_time = 0

    # Round values
    avg_wait_time = round(avg_wait_time, 2)
    avg_travel_time = round(avg_travel_time, 2)
    avg_total_time = round(avg_total_time, 2)

    # Prepare line for this episode
    line = (
        f"Episode {episode}: "
        f"Durchschnittliche Wartezeit: {avg_wait_time} Sekunden, "
        f"Durchschnittliche Fahrzeit: {avg_travel_time} Sekunden, "
        f"Durchschnittliche Gesamtzeit: {avg_total_time} Sekunden\n"
    )

    # Append line
    with open(filename, "a") as f:
        f.write(line)
