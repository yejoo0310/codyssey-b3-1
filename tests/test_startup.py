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
            'mini-redis> (error) ERR No closing quotation\n'
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

    def test_memory_limit_eviction_and_oom_recovery(self):
        output = self.run_cli(
            "CONFIG SET maxmemory 4\nSET a 1\nSET b 2\nGET a\n"
            "SET c 3\nGET b\nSET a 12345\nINFO memory\n"
            "CONFIG SET maxmemory abc\nDEL c\nINFO memory\nquit\n"
        )
        self.assertEqual(
            output,
            'mini-redis> OK\nmini-redis> OK\nmini-redis> OK\n'
            'mini-redis> "1"\nmini-redis> OK\nmini-redis> (nil)\n'
            "mini-redis> (error) OOM command not allowed when used_memory > 'maxmemory'\n"
            'mini-redis> used_memory:4\nmaxmemory:4\nevicted_keys:1\n'
            'mini-redis> (error) ERR value is not an integer or out of range\n'
            'mini-redis> (integer) 1\n'
            'mini-redis> used_memory:2\nmaxmemory:4\nevicted_keys:1\n'
            'mini-redis> ',
        )

    def test_ttl_commands_and_error_recovery(self):
        output = self.run_cli(
            "SET a 1\nTTL a\nEXPIRE a 100\nSET a 2\nTTL a\n"
            "EXPIRE a abc\nGET a\nEXPIRE a 0\nTTL a\nGET a\nINFO memory\nquit\n"
        )
        self.assertEqual(
            output,
            'mini-redis> OK\nmini-redis> (integer) -1\n'
            'mini-redis> (integer) 1\nmini-redis> OK\nmini-redis> (integer) -1\n'
            'mini-redis> (error) ERR value is not an integer or out of range\n'
            'mini-redis> "2"\nmini-redis> (integer) 1\n'
            'mini-redis> (integer) -2\nmini-redis> (nil)\n'
            'mini-redis> used_memory:0\nmaxmemory:0\nevicted_keys:0\n'
            'mini-redis> ',
        )

    def test_all_commands_with_unicode_and_memory_management(self):
        output = self.run_cli(
            'CONFIG SET maxmemory 8\nSET 가 "🔑"\nGET 가\nEXISTS 가\n'
            'EXPIRE 가 100\nSET 가 나\nTTL 가\nSET a 1\nSET b 2\n'
            'GET 가\nGET a\nGET b\nDBSIZE\nKEYS\nINFO memory\n'
            'EXPIRE b 0\nDEL a\nDBSIZE\nKEYS\nINFO memory\nquit\n'
        )
        prefix, keys_and_rest = output.split('mini-redis> (integer) 2\n', 1)
        self.assertEqual(
            prefix,
            'mini-redis> OK\nmini-redis> OK\nmini-redis> "🔑"\n'
            'mini-redis> (integer) 1\nmini-redis> (integer) 1\n'
            'mini-redis> OK\nmini-redis> (integer) -1\n'
            'mini-redis> OK\nmini-redis> OK\nmini-redis> (nil)\n'
            'mini-redis> "1"\nmini-redis> "2"\n',
        )
        key_output, rest = keys_and_rest.split('mini-redis> used_memory:', 1)
        lines = key_output.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith('mini-redis> 1. '))
        self.assertTrue(lines[1].startswith('2. '))
        self.assertCountEqual(
            [lines[0][len('mini-redis> 1. '):], lines[1][len('2. '):]],
            ['"a"', '"b"'],
        )
        self.assertEqual(
            rest,
            '4\nmaxmemory:8\nevicted_keys:1\n'
            'mini-redis> (integer) 1\nmini-redis> (integer) 1\n'
            'mini-redis> (integer) 0\nmini-redis> (empty array)\n'
            'mini-redis> used_memory:0\nmaxmemory:8\nevicted_keys:1\n'
            'mini-redis> ',
        )


if __name__ == "__main__":
    unittest.main()
