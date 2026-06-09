"""Typer CLI for ESP32 CSI radar host tools."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import typer

from .breathing import estimate_breathing_rate
from .motion import motion_score
from .parser import (
    generate_synthetic_records,
    load_records_csv,
    save_records_csv,
    save_records_npz,
)
from .serial_reader import record_csv
from .visualise import amplitude_heatmap, breathing_plot, motion_plot, save_figure, spectrogram_plot

app = typer.Typer(help="ESP32 Wi-Fi CSI radar host tools")


@app.command()
def record(
    port: str = typer.Option(..., "--port"),
    baud: int = typer.Option(921600, "--baud"),
    output: Path = typer.Option(..., "--output"),
) -> None:
    """Record raw CSI CSV lines from serial."""

    record_csv(port=port, baud=baud, output=output)


@app.command()
def live(
    port: str = typer.Option(..., "--port"),
    baud: int = typer.Option(921600, "--baud"),
) -> None:
    """Simple live view placeholder that records parseable serial lines."""

    typer.echo("Live plotting is intentionally simple in v0.1; recording parseable lines.")
    record_csv(port=port, baud=baud, output=Path("data/live_session.csv"))


@app.command()
def analyse(csv_file: Path, out: Path = typer.Option(Path("results"), "--out")) -> None:
    """Run offline analysis and save plots."""

    records = load_records_csv(csv_file)
    out.mkdir(parents=True, exist_ok=True)
    motion = motion_score(records)
    breathing = estimate_breathing_rate(records)
    fig, _ = amplitude_heatmap(records)
    save_figure(fig, out / "amplitude_heatmap.png")
    plt.close(fig)
    fig, _ = motion_plot(motion)
    save_figure(fig, out / "motion_score.png")
    plt.close(fig)
    fig, _ = spectrogram_plot(records)
    save_figure(fig, out / "spectrogram.png")
    plt.close(fig)
    fig, _ = breathing_plot(breathing)
    save_figure(fig, out / "breathing.png")
    plt.close(fig)
    typer.echo(f"motion_present={motion.present}")
    typer.echo(f"breathing={breathing.breaths_per_minute:.1f} breaths/min")


@app.command()
def convert(csv_file: Path, output: Path = typer.Option(..., "--output")) -> None:
    """Convert raw CSI CSV to parsed NPZ."""

    records = load_records_csv(csv_file)
    save_records_npz(records, output)
    typer.echo(f"wrote {output}")


@app.command()
def simulate(
    output: Path = typer.Option(..., "--output"),
    seconds: float = typer.Option(60.0, "--seconds"),
    rate: float = typer.Option(100.0, "--rate"),
) -> None:
    """Generate synthetic ESP32-style CSI CSV."""

    records = generate_synthetic_records(seconds=seconds, rate_hz=rate)
    save_records_csv(records, output)
    typer.echo(f"wrote {len(records)} records to {output}")


if __name__ == "__main__":
    app()

