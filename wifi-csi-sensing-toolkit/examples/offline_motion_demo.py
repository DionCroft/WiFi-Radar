"""Offline motion score demo using synthetic CSI."""

import matplotlib.pyplot as plt

from wificsi.io.simulator import generate_synthetic_csi
from wificsi.processing.motion import motion_score
from wificsi.visualisation.plots import plot_motion_score


data = generate_synthetic_csi(seconds=30, rate_hz=100)
result = motion_score(data)
print(f"occupied={result.occupied}, threshold={result.threshold:.6g}")
plot_motion_score(result)
plt.show()

