"""명령 파싱, 결과 형식, 잘못된 입력 후의 데이터 보존을 확인한다."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from mini_redis.cli import execute_command, main, parse_command
from mini_redis.store import RedisStore


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.store = RedisStore()

    def execute(self, line):
        return execute_command(line, self.store)

    def test_basic_command_sequence(self):
        self.assertEqual(self.execute("SET name Alice"), "OK")
        self.assertEqual(self.execute("GET name"), '"Alice"')
        self.assertEqual(self.execute("EXISTS name"), "(integer) 1")
        self.assertEqual(self.execute("DBSIZE"), "(integer) 1")
        self.assertEqual(self.execute("SET name Bob"), "OK")
        self.assertEqual(self.execute("GET name"), '"Bob"')
        self.assertEqual(self.execute("DBSIZE"), "(integer) 1")
        self.assertEqual(self.execute("DEL name"), "(integer) 1")
        self.assertEqual(self.execute("DEL name"), "(integer) 0")
        self.assertEqual(self.execute("GET name"), "(nil)")
        self.assertEqual(self.execute("EXISTS name"), "(integer) 0")
        self.assertEqual(self.execute("DBSIZE"), "(integer) 0")

    def test_command_case_does_not_change_keys_or_values(self):
        self.assertEqual(self.execute("sEt Name Alice"), "OK")
        self.assertEqual(self.execute("gEt Name"), '"Alice"')
        self.assertEqual(self.execute("get name"), "(nil)")

    def test_quoted_keys_values_and_unicode(self):
        self.assertEqual(self.execute('SET "사용자 이름" "김 예주 🔑"'), "OK")
        self.assertEqual(self.execute('GET "사용자 이름"'), '"김 예주 🔑"')
        self.assertEqual(self.execute('KEYS'), '1. "사용자 이름"')

    def test_empty_key_and_value_are_not_missing(self):
        self.assertEqual(self.execute('SET "" ""'), "OK")
        self.assertEqual(self.execute('GET ""'), '""')
        self.assertEqual(self.execute('EXISTS ""'), "(integer) 1")
        self.assertEqual(self.execute("KEYS"), '1. ""')
        self.assertEqual(self.execute('DEL ""'), "(integer) 1")
        self.assertEqual(self.execute('GET ""'), "(nil)")

    def test_quote_and_backslash_escapes(self):
        self.assertEqual(self.execute(r'SET message "say \"hello\" \\ end"'), "OK")
        self.assertEqual(self.store.get("message"), 'say "hello" \\ end')
        self.assertEqual(self.execute("GET message"), r'"say \"hello\" \\ end"')

    def test_output_escapes_control_characters(self):
        self.store.set("line", "a\nb\t\"c\"\\")
        self.assertEqual(self.execute("GET line"), r'"a\nb\t\"c\"\\"')

    def test_keys_output_does_not_require_sorted_order(self):
        self.execute("SET first A")
        self.execute("SET second B")
        lines = self.execute("KEYS").splitlines()
        values = []
        for index, line in enumerate(lines, start=1):
            prefix = "{}. ".format(index)
            self.assertTrue(line.startswith(prefix))
            values.append(line[len(prefix):])
        self.assertCountEqual(values, ['"first"', '"second"'])

    def test_empty_keys_output(self):
        self.assertEqual(self.execute("KEYS"), "(empty array)")

    def test_blank_input_has_no_output_or_changes(self):
        self.execute("SET kept value")
        for line in ("", " ", "\t  "):
            with self.subTest(line=line):
                self.assertEqual(self.execute(line), "")
        self.assertEqual(self.execute("GET kept"), '"value"')

    def test_unknown_command(self):
        self.assertEqual(
            self.execute("HeLLo"), "(error) ERR unknown command 'HeLLo'"
        )
        self.assertEqual(self.store.dbsize(), 0)

    def test_wrong_arity_preserves_data(self):
        self.execute("SET kept value")
        cases = (
            ("SET", "SET"), ("SET kept", "SET"),
            ("SET kept new extra", "SET"),
            ("GET", "GET"), ("GET kept extra", "GET"),
            ("DEL", "DEL"), ("DEL kept extra", "DEL"),
            ("EXISTS", "EXISTS"), ("EXISTS kept extra", "EXISTS"),
            ("DBSIZE extra", "DBSIZE"), ("KEYS extra", "KEYS"),
            ("quit extra", "QUIT"), ("exit extra", "EXIT"),
        )
        for line, command in cases:
            with self.subTest(line=line):
                self.assertEqual(
                    self.execute(line),
                    "(error) ERR wrong number of arguments for '{}' command".format(command),
                )
                self.assertEqual(self.store.get("kept"), "value")
                self.assertEqual(self.store.dbsize(), 1)

    def test_unclosed_quotes_do_not_apply_partial_command(self):
        self.execute("SET kept value")
        for line in ('SET kept "broken', 'DEL "kept', '"quit'):
            with self.subTest(line=line):
                self.assertEqual(
                    self.execute(line), "(error) ERR unbalanced quotes in request"
                )
                self.assertEqual(self.store.get("kept"), "value")
        self.assertEqual(self.execute("SET kept recovered"), "OK")
        self.assertEqual(self.execute("GET kept"), '"recovered"')

    def test_quit_and_exit_return_exit_signal(self):
        for line in ("quit", "EXIT", "  QuIt  "):
            with self.subTest(line=line):
                self.assertIsNone(self.execute(line))

    def test_shell_characters_are_literal_values(self):
        for value in ("#tag", "$HOME", "$(date)", "a;b", "a|b", "*.py"):
            with self.subTest(value=value):
                self.assertEqual(self.execute("SET literal " + value), "OK")
                self.assertEqual(self.store.get("literal"), value)

    def test_parser_preserves_whitespace_and_fragments(self):
        self.assertEqual(
            parse_command('  SET\tkey "  Alice Kim  "  '),
            ["SET", "key", "  Alice Kim  "],
        )
        self.assertEqual(parse_command('SET key pre" "suffix'), ["SET", "key", "pre suffix"])
        self.assertEqual(parse_command(r'SET path C:\temp'), ["SET", "path", r'C:\temp'])

    def test_ctrl_c_exits_without_traceback(self):
        output = StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(output):
                main()
        self.assertEqual(output.getvalue(), "\n")


if __name__ == "__main__":
    unittest.main()
