"""DSP tests using synthetic ESP32 CSI records."""

from esp32csi.breathing import estimate_breathing_rate
from esp32csi.motion import motion_score
from esp32csi.parser import generate_synthetic_records
from esp32csi.processing import amplitude_phase, clean_records, remove_static_mean


def test_processing_shapes() -> None:
    records = generate_synthetic_records(seconds=2, rate_hz=50, subcarriers=16)
    timestamps, csi, rssi = clean_records(records)
    amplitude, phase = amplitude_phase(csi)
    dynamic = remove_static_mean(amplitude)

    assert timestamps.size == 100
    assert csi.shape == (100, 16)
    assert rssi.shape == (100,)
    assert phase.shape == csi.shape
    assert dynamic.shape == csi.shape


def test_motion_and_breathing_estimators() -> None:
    records = generate_synthetic_records(seconds=60, rate_hz=50, breathing_hz=0.25)

    motion = motion_score(records)
    breathing = estimate_breathing_rate(records)

    assert motion.score.shape == motion.timestamps.shape
    assert 10.0 <= breathing.breaths_per_minute <= 20.0

