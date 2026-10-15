"""별도 프로세스에서 프로그램이 정상 실행되는지 확인한다."""

from pathlib import Path
import subprocess
import sys
import unittest


class StartupTests(unittest.TestCase):
    def run_cli(self, commands):
        """별도 프로세스에 입력을 전달하고 실행 결과를 받는다."""
        project_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=project_root,
            input=commands,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_quit_stops_reading_commands(self):
        output = self.run_cli("quit\nSET ignored value\n")
        self.assertEqual(output, "mini-redis> ")

    def test_exit_stops_reading_commands(self):
        self.assertEqual(self.run_cli("exit\n"), "mini-redis> ")

    def test_eof_exits_cleanly(self):
        self.assertEqual(self.run_cli(""), "mini-redis> \n")
        self.assertEqual(self.run_cli("SET name Alice\n"), "mini-redis> OK\nmini-redis> \n")

    def test_repl_keeps_data_and_recovers_from_errors(self):
        output = self.run_cli(
            'SET name "Alice Kim"\nGET name\nGET\nHELLO\n'
            'SET name "broken\nGET name\nDEL name\nKEYS\nquit\n'
        )
        self.assertEqual(
            output,
            'mini-redis> OK\n'
            'mini-redis> "Alice Kim"\n'
            "mini-redis> (error) ERR wrong number of arguments for 'GET' command\n"
            "mini-redis> (error) ERR unknown command 'HELLO'\n"
            'mini-redis> (error) ERR unbalanced quotes in request\n'
            'mini-redis> "Alice Kim"\n'
            'mini-redis> (integer) 1\n'
            'mini-redis> (empty array)\n'
            'mini-redis> ',
        )

    def test_blank_input_continues_repl(self):
        self.assertEqual(
            self.run_cli("\n \t\nDBSIZE\nquit\n"),
            "mini-redis> mini-redis> mini-redis> (integer) 0\nmini-redis> ",
        )


if __name__ == "__main__":
    unittest.main()
