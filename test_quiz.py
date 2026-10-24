"""Checks for bank validation and preserving answer identity during shuffles."""

import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from quiz import load_bank, prepare_questions


class QuizTests(unittest.TestCase):
    def setUp(self):
        self.bank = {
            "title": "Example", "questions": [{
                "id": "one", "type": "mcq", "prompt": "Pick B",
                "choices": ["A", "B", "C"], "correct": 1,
                "answer": "B", "explanation": "B is correct.",
            }],
        }

    def load(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bank.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return load_bank(path)

    def test_shuffle_preserves_correct_answer_and_original(self):
        original = self.load(self.bank)
        before = copy.deepcopy(original)
        for seed in range(30):
            q = prepare_questions(original, "mixed", random.Random(seed))[0]
            self.assertEqual(q["choices"][q["correct"]], "B")
        self.assertEqual(original, before)

    def test_retry_shuffle_preserves_answer(self):
        first = prepare_questions(self.load(self.bank), "mixed", random.Random(3))
        retry = prepare_questions(first, "mixed", random.Random(5))[0]
        self.assertEqual(retry["choices"][retry["correct"]], "B")

    def test_open_mode_hides_mcq_without_changing_native_type(self):
        q = prepare_questions(self.load(self.bank), "open", random.Random(0))[0]
        self.assertEqual(q["display_type"], "open")
        self.assertEqual(q["type"], "mcq")
        self.assertEqual(q["answer"], "B")

    def test_reject_invalid_banks(self):
        invalid = [[], {}, {"title": "Empty", "questions": []}]
        for field, value in [("correct", True), ("correct", -1), ("correct", 3),
                             ("choices", ["A"]), ("choices", ["A", ""]),
                             ("explanation", ""), ("type", "essay"),
                             ("key_points", "not a list"), ("source", 4)]:
            bank = copy.deepcopy(self.bank)
            bank["questions"][0][field] = value
            invalid.append(bank)
        duplicate = copy.deepcopy(self.bank)
        duplicate["questions"] *= 2
        invalid.append(duplicate)
        for bank in invalid:
            with self.subTest(bank=bank), self.assertRaises(ValueError):
                self.load(bank)

    def test_bundled_banks_have_sources_and_open_rubrics(self):
        root = Path(__file__).resolve().parent
        paths = sorted((root / "questions").glob("*.json"))
        self.assertTrue(paths, "Expected bundled question banks")
        all_ids = set()
        for path in paths:
            with self.subTest(path=path):
                questions = load_bank(path)
                self.assertTrue(all(q.get("source") for q in questions))
                for q in questions:
                    self.assertNotIn(q["id"], all_ids)
                    all_ids.add(q["id"])
                    if q["type"] == "open":
                        self.assertTrue(q.get("key_points"))
                        self.assertTrue(all(p.strip() for p in q["key_points"]))


if __name__ == "__main__":
    unittest.main()
