"""Offline breathing-like rate demo using synthetic CSI."""

import matplotlib.pyplot as plt

from wificsi.io.simulator import generate_synthetic_csi
from wificsi.processing.breathing import estimate_breathing_rate
from wificsi.visualisation.plots import plot_breathing


data = generate_synthetic_csi(seconds=60, rate_hz=100, breathing_hz=0.25)
result = estimate_breathing_rate(data)
print(f"Estimated {result.breaths_per_minute:.1f} breaths/min")
plot_breathing(result)
plt.show()

