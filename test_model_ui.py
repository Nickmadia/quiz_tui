"""Model discovery, selection, and responsive loading UI checks."""
import curses
import json
import os
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from quiz import GradingError, QuitQuiz, Screen, choose_model, discover_models, run

MODELS = [{"model": "one", "displayName": "Model One", "isDefault": True},
          {"model": "two", "displayName": "Model Two"}]


class ModelUITests(unittest.TestCase):
    def test_picker_default_and_explicit_selection(self):
        for choice, expected in [("1", "configured"), ("2", "one"), ("3", "two")]:
            screen = Mock()
            screen.read.return_value = choice
            with self.subTest(choice=choice), \
                    patch("quiz.discover_models", return_value=(MODELS, "configured")):
                self.assertEqual(choose_model(screen), expected)
            self.assertIn("configured", screen.read.call_args.kwargs["choices"][0])

    def test_manual_model_requires_nonempty_single_line(self):
        screen = Mock()
        screen.read.side_effect = ["4", "", "bad\nmodel", "  custom-model  "]
        with patch("quiz.discover_models", return_value=(MODELS, "one")):
            self.assertEqual(choose_model(screen), "custom-model")
        self.assertEqual(screen.read.call_args.kwargs["edit_label"], "MODEL ID:")

    def test_discovery_failure_keeps_manual_entry_available(self):
        screen = Mock()
        screen.read.side_effect = ["2", "custom-model"]
        with patch("quiz.discover_models", side_effect=GradingError("Offline")):
            self.assertEqual(choose_model(screen), "custom-model")
        self.assertIn("Offline", screen.read.call_args_list[0].args[1])

    def test_quit_during_discovery_does_not_open_picker(self):
        screen = Mock()
        with patch("quiz.discover_models", side_effect=QuitQuiz), self.assertRaises(QuitQuiz):
            choose_model(screen)
        screen.read.assert_not_called()

    def fake_catalog(self, behavior="normal"):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        script = Path(directory.name) / "codex"
        script.write_text('''#!/usr/bin/env python3
import json,sys,time
for line in sys.stdin:
    request=json.loads(line)
    method=request['method']
    if method=='initialized': continue
    if BEHAVIOR=='timeout':
        time.sleep(30)
        continue
    if BEHAVIOR=='malformed':
        print('not json',flush=True)
        continue
    result={}
    if method=='config/read': result={'config':{'model':'configured'}}
    if method=='model/list':
        if BEHAVIOR=='error':
            print(json.dumps({'id':request['id'],'error':{'message':'no models'}}),flush=True)
            continue
        if 'cursor' not in request['params']:
            result={'data':[{'model':'one','displayName':'One','isDefault':True},
                            {'model':'hidden','hidden':True},
                            {'model':'audio-only','inputModalities':['audio']}],
                    'nextCursor':'next'}
        else:
            result={'data':[{'model':'one'}, {'model':'two','displayName':'Two'}],
                    'nextCursor':None}
    print(json.dumps({'method':'notice','params':{}}),flush=True)
    print(json.dumps({'id':request['id'],'result':result}),flush=True)
'''.replace("BEHAVIOR", repr(behavior)))
        script.chmod(0o755)
        env = patch.dict(os.environ, {"PATH": directory.name + os.pathsep + os.environ["PATH"]})
        env.start()
        self.addCleanup(env.stop)

    def test_real_discovery_handshake_pagination_and_filtering(self):
        self.fake_catalog()
        models, default = discover_models(timeout=3)
        self.assertEqual([m["model"] for m in models], ["one", "two"])
        self.assertEqual(default, "configured")

    def test_malformed_and_failed_catalogs(self):
        for behavior in ("malformed", "error"):
            with self.subTest(behavior=behavior):
                self.fake_catalog(behavior)
                with self.assertRaises(GradingError):
                    discover_models(timeout=2)

    def test_catalog_timeout_and_cancellation(self):
        self.fake_catalog("timeout")
        with self.assertRaises(GradingError):
            discover_models(timeout=0.1)
        with self.assertRaises(QuitQuiz):
            discover_models(on_wait=Mock(side_effect=QuitQuiz))

    def test_selected_model_reaches_grading_and_stays_visible(self):
        question = {"id":"q", "bank":"Example", "type":"open", "prompt":"Question?",
                    "answer":"Answer", "explanation":"Explanation"}
        screen = Mock()
        screen.read.side_effect = ["Answer", "\n", "q"]
        grade = {"verdict":"correct", "feedback":"Good", "missing_points":[]}
        with patch("quiz.Screen", return_value=screen), \
                patch("quiz.choose_model", return_value="selected") as picker, \
                patch("quiz.grade_answer", return_value=grade) as grader:
            run(None, [question], "open", random.Random(0))
        picker.assert_called_once_with(screen)
        self.assertEqual(grader.call_args.args[2], "selected")
        self.assertEqual(screen.model_label, "Model: selected")

    def test_cli_model_bypasses_picker(self):
        screen = Mock()
        screen.read.side_effect = ["", "\n", "q"]
        question = {"id":"q", "bank":"Example", "type":"open", "prompt":"Question?",
                    "answer":"Answer", "explanation":"Explanation"}
        with patch("quiz.Screen", return_value=screen), patch("quiz.choose_model") as picker:
            run(None, [question], "open", random.Random(0), model="explicit")
        picker.assert_not_called()
        self.assertEqual(screen.model_label, "Model: explicit")

    def test_mcq_skips_model_discovery(self):
        screen = Mock()
        screen.read.side_effect = ["1", "\n", "q"]
        question = {"id":"q", "bank":"Example", "type":"mcq", "prompt":"Question?",
                    "answer":"A", "explanation":"Why", "choices":["A","B"], "correct":0}
        with patch("quiz.Screen", return_value=screen), patch("quiz.choose_model") as picker:
            run(None, [question], "mcq", random.Random(0))
        picker.assert_not_called()

    def test_loading_animates_displays_model_and_restores_input(self):
        window = Mock()
        window.getmaxyx.return_value = (24, 80)
        window.get_wch.side_effect = curses.error
        with patch("quiz.curses.has_colors", return_value=False), patch("quiz.curses.curs_set"):
            screen = Screen(window)
        with patch("quiz.time.monotonic", side_effect=[10, 10.5]):
            screen.grading_status("Quiz", "chosen", 10)
            screen.grading_status("Quiz", "chosen", 10)
        draws = [c.args for c in window.addnstr.call_args_list]
        self.assertTrue(any("Model: chosen" in c[2] for c in draws))
        bars = [c[2] for c in draws if c[0] == 5]
        self.assertEqual(len(bars), 2)
        self.assertNotEqual(bars[0], bars[1])
        window.timeout.assert_called_with(-1)
        window.get_wch.side_effect = None
        window.get_wch.return_value = "\x07"
        with self.assertRaises(QuitQuiz):
            screen.loading("Quiz", "Waiting", 10)
        window.timeout.assert_called_with(-1)


if __name__ == "__main__":
    unittest.main()
