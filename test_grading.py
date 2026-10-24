"""Codex boundary and quiz flow checks; no network calls."""
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from quiz import GradingError, QuitQuiz, grade_answer, run


QUESTION = {
    "id": "open-1", "bank": "Example", "type": "open",
    "prompt": "Why acknowledge a frame?", "answer": "To confirm reception.",
    "explanation": "An ACK confirms delivery to the receiver.",
    "key_points": ["Confirm reception"],
}
GRADE = {"verdict": "correct", "feedback": "You explained reception correctly.",
         "missing_points": []}


class GradingTests(unittest.TestCase):
    def invoke(self, result=GRADE, returncode=0, model=None):
        self.command = None
        self.prompt = None

        def start(command, **kwargs):
            self.command = command
            self.prompt = kwargs["stdin"].read()
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text(json.dumps(result))
            return Mock(poll=Mock(return_value=returncode), returncode=returncode)

        with patch("quiz.subprocess.Popen", side_effect=start):
            return grade_answer(QUESTION, "The receiver confirms it got the frame.", model)

    def test_structured_grade_and_model_forwarding(self):
        self.assertEqual(self.invoke(model="chosen-model"), GRADE)
        self.assertEqual(self.command[self.command.index("--model") + 1], "chosen-model")
        self.assertIn("read-only", self.command)
        self.assertIn("--ephemeral", self.command)
        self.assertIn("The receiver confirms it got the frame.", self.prompt)
        self.assertIn(QUESTION["answer"], self.prompt)
        self.assertIn("Confirm reception", self.prompt)

    def test_configured_model_is_default(self):
        self.invoke()
        self.assertNotIn("--model", self.command)

    def test_blank_needs_no_codex(self):
        with patch("quiz.subprocess.Popen") as start:
            self.assertEqual(grade_answer(QUESTION, "  ")["verdict"], "incorrect")
            start.assert_not_called()

    def test_reject_malformed_grades(self):
        for result in ([], {}, {**GRADE, "verdict": []},
                       {**GRADE, "verdict": "maybe"}, {**GRADE, "feedback": ""},
                       {**GRADE, "missing_points": [42]}):
            with self.subTest(result=result), self.assertRaises(GradingError):
                self.invoke(result)

    def test_failure_is_not_an_incorrect_grade(self):
        with self.assertRaises(GradingError):
            self.invoke(returncode=1)

    def test_timeout_and_quit_reap_process(self):
        for cancel in (False, True):
            process = Mock(pid=123456, poll=Mock(return_value=None))
            callback = Mock(side_effect=QuitQuiz) if cancel else None
            with self.subTest(cancel=cancel), \
                    patch("quiz.subprocess.Popen", return_value=process), \
                    patch("quiz.os.killpg") as kill, \
                    self.assertRaises(QuitQuiz if cancel else GradingError):
                try:
                    grade_answer(QUESTION, "answer", timeout=0 if not cancel else 180,
                                 on_wait=callback)
                finally:
                    kill.assert_called_once()
                    process.wait.assert_called_once()

    def test_real_subprocess_protocol(self):
        # A fake CLI exercises stdin, output file handling, and argument boundaries.
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text(
                "#!/usr/bin/env python3\nimport sys,json\nfrom pathlib import Path\n"
                "assert 'student_answer' in sys.stdin.read()\n"
                "assert sys.argv[sys.argv.index('--model')+1] == 'a model; $(literal)'\n"
                "Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text("
                + repr(json.dumps(GRADE)) + ")\n")
            executable.chmod(0o755)
            import os
            with patch.dict(os.environ, {"PATH": directory + os.pathsep + os.environ["PATH"]}):
                self.assertEqual(grade_answer(QUESTION, "Answer", "a model; $(literal)"), GRADE)

    def test_open_feedback_has_no_self_assessment(self):
        screen = Mock()
        screen.read.side_effect = ["My answer", "\n", "q"]
        with patch("quiz.Screen", return_value=screen), \
                patch("quiz.grade_answer", return_value=GRADE):
            run(None, [QUESTION], "open", random.Random(0), "chosen-model")
        feedback = screen.read.call_args_list[1]
        self.assertEqual(feedback.kwargs["allowed"], "\n\r")
        self.assertIn("CODEX FEEDBACK:", feedback.kwargs["below"])
        self.assertTrue(feedback.kwargs["focus_feedback"])
        self.assertIn("1/1 points", screen.read.call_args_list[-1].args[1])

    def test_skip_is_ungraded_and_can_be_retried(self):
        screen = Mock()
        screen.read.side_effect = ["My answer", "s", "\n", "r", "New answer", "\n", "q"]
        with patch("quiz.Screen", return_value=screen), \
                patch("quiz.grade_answer", side_effect=[GradingError("offline"), GRADE]):
            run(None, [QUESTION], "open", random.Random(0))
        summary = screen.read.call_args_list[3].args[1]
        self.assertIn("Ungraded: 1", summary)
        self.assertNotIn("0/1 points", summary)
        self.assertIn("Questions to retry: 1", summary)

    def test_retry_preserves_answer_and_partial_score(self):
        screen = Mock()
        screen.read.side_effect = ["My answer", "r", "\n", "q"]
        partial = {**GRADE, "verdict": "partial", "missing_points": ["One point"]}
        with patch("quiz.Screen", return_value=screen), \
                patch("quiz.grade_answer", side_effect=[GradingError("offline"), partial]) as grade:
            run(None, [QUESTION], "open", random.Random(0))
        self.assertEqual([c.args[1] for c in grade.call_args_list], ["My answer"] * 2)
        self.assertIn("0.5/1 points", screen.read.call_args_list[-1].args[1])


if __name__ == "__main__":
    unittest.main()
