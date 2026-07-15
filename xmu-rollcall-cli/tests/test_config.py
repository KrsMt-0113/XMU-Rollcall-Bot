import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xmu_rollcall import config


class ConfigTests(unittest.TestCase):
    def test_missing_config_returns_fresh_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            with patch.object(config, "CONFIG_DIR", config_dir), patch.object(
                config, "CONFIG_FILE", config_dir / "config.json"
            ):
                first = config.load_config()
                first["accounts"].append({"id": 1})
                second = config.load_config()

        self.assertEqual(second["accounts"], [])
        self.assertEqual(second["attendance_threshold"], 0.2)

    def test_invalid_threshold_uses_default(self):
        self.assertEqual(config.get_attendance_threshold({"attendance_threshold": 2}), 0.2)
        self.assertEqual(
            config.get_attendance_threshold({"attendance_threshold": "invalid"}),
            0.2,
        )


if __name__ == "__main__":
    unittest.main()
