"""Start the simple live serial recorder/viewer."""

from esp32csi.cli import live


if __name__ == "__main__":
    live(port="COM3", baud=921600)

