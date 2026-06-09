"""Generate a synthetic CSI NPZ file."""

from pathlib import Path

from wificsi.core import save_npz
from wificsi.io.simulator import generate_synthetic_csi


output = Path("synthetic.npz")
data = generate_synthetic_csi(seconds=60, rate_hz=100, breathing_hz=0.25)
save_npz(data, output)
print(f"Wrote {output} with {data.summary()}")

