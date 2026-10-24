# Question bank format

Create a UTF-8 JSON file in `questions/` (or elsewhere) with this structure:

```json
{
  "schema_version": 1,
  "title": "Example subject",
  "questions": [
    {
      "id": "example-01",
      "type": "mcq",
      "topic": "arithmetic",
      "prompt": "What is 2 + 2?",
      "choices": ["3", "4", "5"],
      "correct": 1,
      "answer": "4",
      "explanation": "Adding two pairs gives four items.",
      "source": "Optional source reference"
    },
    {
      "id": "example-02",
      "type": "open",
      "prompt": "Explain what addition represents.",
      "answer": "Addition combines quantities into a total.",
      "explanation": "The result counts the combined quantity.",
      "key_points": ["Combining quantities", "Finding a total"]
    }
  ]
}
```

`correct` is a **zero-based** choice index. MCQs need 2–9 nonempty choices.
All questions require nonempty `id`, `type`, `prompt`, `answer`, and `explanation`.
IDs must be unique within each bank. `topic`, `source`, and `key_points` are
optional. Top-level `notes`, `sources`, and `schema_version` are descriptive
metadata; the app uses `title` and `questions`. No bank content is executed.

Validate a bank with `python3 quiz.py questions/your_bank.json --validate`.
Open answers use `answer`, `explanation`, and `key_points` as the Codex grading rubric.
Include a `source` reference for each question and top-level `notes` for qualifications.
