"""Analyse a recorded ESP32 CSI CSV file."""

from esp32csi.breathing import estimate_breathing_rate
from esp32csi.motion import motion_score
from esp32csi.parser import load_records_csv


records = load_records_csv("data/session.csv")
motion = motion_score(records)
breathing = estimate_breathing_rate(records)
print(f"motion_present={motion.present}")
print(f"breathing={breathing.breaths_per_minute:.1f} breaths/min")

