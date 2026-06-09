"""Command-line interface for the Wi-Fi CSI sensing toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import typer

from wificsi.core import CSIError, save_npz
from wificsi.io.base import load_csi
from wificsi.io.simulator import generate_synthetic_csi
from wificsi.processing.breathing import estimate_breathing_rate
from wificsi.processing.features import pca_motion_component
from wificsi.processing.motion import motion_score
from wificsi.processing.spectrogram import stft_spectrogram
from wificsi.visualisation.live import run_serial_live_plot
from wificsi.visualisation.plots import (
    plot_amplitude_heatmap,
    plot_breathing,
    plot_motion_score,
    plot_phase_heatmap,
    plot_spectrogram,
)

app = typer.Typer(help="Wi-Fi CSI sensing toolkit")


@app.command()
def info(file: Path, format: str = typer.Option(..., "--format", "-f")) -> None:
    """Print a concise summary of a CSI file."""

    _run_or_exit(lambda: typer.echo(load_csi(file, format).summary()))


@app.command()
def plot(
    file: Path,
    format: str = typer.Option(..., "--format", "-f"),
    plot: Literal["amplitude", "phase"] = typer.Option("amplitude", "--plot"),
) -> None:
    """Plot CSI amplitude or phase heatmap."""

    def command() -> None:
        data = load_csi(file, format)
        if plot == "amplitude":
            plot_amplitude_heatmap(data)
        else:
            plot_phase_heatmap(data)
        plt.show()

    _run_or_exit(command)


@app.command()
def motion(file: Path, format: str = typer.Option(..., "--format", "-f")) -> None:
    """Compute and plot a simple motion/occupancy score."""

    def command() -> None:
        data = load_csi(file, format)
        result = motion_score(data)
        typer.echo(f"occupied={result.occupied} threshold={result.threshold:.6g}")
        plot_motion_score(result)
        plt.show()

    _run_or_exit(command)


@app.command()
def breathing(
    file: Path,
    format: str = typer.Option(..., "--format", "-f"),
    min_hz: float = typer.Option(0.1, "--min-hz"),
    max_hz: float = typer.Option(0.6, "--max-hz"),
) -> None:
    """Estimate breathing-like periodic motion from CSI."""

    def command() -> None:
        data = load_csi(file, format)
        result = estimate_breathing_rate(data, min_hz=min_hz, max_hz=max_hz)
        typer.echo(
            f"estimated_breathing={result.frequency_hz:.3f} Hz "
            f"({result.breaths_per_minute:.1f} breaths/min)"
        )
        plot_breathing(result)
        plt.show()

    _run_or_exit(command)


@app.command()
def simulate(
    seconds: float = typer.Option(60.0, "--seconds"),
    rate: float = typer.Option(100.0, "--rate"),
    breathing_hz: float = typer.Option(0.25, "--breathing-hz"),
    output: Path = typer.Option(Path("synthetic.npz"), "--output", "-o"),
) -> None:
    """Generate synthetic CSI and save it as NPZ."""

    def command() -> None:
        data = generate_synthetic_csi(
            seconds=seconds,
            rate_hz=rate,
            breathing_hz=breathing_hz,
        )
        save_npz(data, output)
        typer.echo(f"wrote {output} with {data.summary()}")

    _run_or_exit(command)


@app.command()
def spectrogram(
    file: Path,
    format: str = typer.Option(..., "--format", "-f"),
    window_seconds: float = typer.Option(2.0, "--window-seconds"),
    step_seconds: float = typer.Option(0.25, "--step-seconds"),
) -> None:
    """Plot a Doppler-like spectrogram from the PCA motion component."""

    def command() -> None:
        data = load_csi(file, format)
        waveform = pca_motion_component(data)
        times, frequencies, spectrum = stft_spectrogram(
            waveform,
            sample_rate_hz=data.sample_rate_hz,
            window_seconds=window_seconds,
            step_seconds=step_seconds,
        )
        plot_spectrogram(times, frequencies, spectrum)
        plt.show()

    _run_or_exit(command)


@app.command()
def live(
    source: Literal["serial"] = typer.Option("serial", "--source"),
    port: str = typer.Option(..., "--port"),
    baud: int = typer.Option(921600, "--baud"),
) -> None:
    """Launch a simple live serial visualiser."""

    def command() -> None:
        if source != "serial":
            raise CSIError("only --source serial is implemented in this version")
        run_serial_live_plot(port=port, baud=baud)

    _run_or_exit(command)


def _run_or_exit(callback) -> None:
    try:
        callback()
    except CSIError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()

