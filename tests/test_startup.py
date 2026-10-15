"""별도 프로세스에서 프로그램이 정상 실행되는지 확인한다."""

from pathlib import Path
import subprocess
import sys
import unittest


class StartupTests(unittest.TestCase):
    def test_main_runs_successfully(self):
        """실제 실행 경로의 패키지 import와 정상 종료를 함께 확인한다."""
        project_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Phase 0 준비 완료", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
