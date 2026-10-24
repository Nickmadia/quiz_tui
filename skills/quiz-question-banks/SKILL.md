---
name: quiz-question-banks
description: "Create, extend, or review JSON question banks for the Python quiz_tui study app from slides, notes, or other learning material. Use for multiple-choice and Codex-graded open-answer banks; not for changing the TUI itself."
---

# Quiz Question Banks

Create learning-oriented question banks compatible with `quiz.py`.

## Locate the app and sources

- Locate `quiz.py`, `README.md`, and `questions/` in the user's
  project. Read the README's bank format and inspect `load_bank` in the app before
  writing; the current loader is authoritative if the format has changed.
- If the project is elsewhere, use its supplied path. If it cannot be found, ask
  for the app location while inspecting available source material. The schema
  example below supports drafting, but do not claim app validation without the app.
- Read the actual requested material before generating questions. For local PDFs,
  use `pdftotext -layout` when available; inspect rendered pages when diagrams,
  tables, or extraction problems affect the answer. Do not infer contents from titles.
- Honor the requested topics, language, count, and question styles. Otherwise use
  the source language and make one bank per distinct requested topic. For a full
  lecture, choose question count from its topic breadth and requested coverage.
  For full-deck coverage, map substantive sections to questions; do not pad with
  repetition or force differently sized lectures to have equal counts. State scope briefly.

## Write useful questions

- Cover the material's main ideas, mechanisms, failure modes, and applications.
  Mix recall with reasoning, code reading, and short scenarios when supported by
  the source. Avoid padding with historical counts or incidental names.
- An MCQ has exactly one defensible correct choice. Use plausible distractors
  reflecting actual misconceptions, and vary the correct choice's position.
  Choices are shuffled by the app: avoid “all of the above,” letter/number
  references between choices, and answer explanations tied to a display position.
- Every question needs a standalone model `answer` and an `explanation` of why it
  is correct. For MCQs, explain the misconceptions behind the distractors where
  useful; merely restating the correct choice does not teach the mechanism.
- MCQs can be converted to open recall with `--mode open`. Make the prompt
  meaningful without visible choices; include code and assumptions in the prompt
  rather than hiding essential context in a choice.
- Open questions need concrete `key_points` as a grading rubric. The app sends
  the question, submitted answer, model answer, explanation and rubric to Codex.
  Make these standalone and consistent: the grader does not receive the slides.
  Accept equivalent correct reasoning; do not require wording or optional details. Prefer bounded prompts over vague requests such as “discuss security.”
- Cite each question's source in `source`: filename plus PDF page number, or a
  precise section/link for other materials. Distinguish PDF pages from printed
  slide numbers. Do not invent references for added context.
- Do not reproduce a source error as fact. Clarify consequential simplifications,
  dated guidance, or incorrect code; record qualifications in top-level `notes`
  and the affected explanation. Label added context beyond the source. If a point
  cannot be established, verify it through an appropriate primary source or omit
  the question rather than teach an uncertain answer.

## Save compatible JSON

Use UTF-8 JSON under `questions/<topic_slug>.json`, unless another destination is
requested. Preserve existing banks and stable IDs when extending them; do not
replace an unrelated bank. Use `json.dumps(..., ensure_ascii=False, indent=2)` or
equivalent serialization so code snippets and newlines are escaped correctly.

The current format is illustrated below. `correct` is a **zero-based integer**,
not a Boolean. MCQs require 2–9 nonempty string choices. Required strings must be
nonempty, and IDs must be unique within each bank. `topic` and `source` are string
fields; `key_points` is a list of strings. Include sources and key points as above
even though the loader permits their omission.

```json
{
  "schema_version": 1,
  "title": "Example topic",
  "sources": ["Example notes, section 1"],
  "notes": [],
  "questions": [
    {
      "id": "example-01",
      "type": "mcq",
      "topic": "integer validation",
      "prompt": "Why is successfully parsing an integer insufficient to validate an array index?",
      "choices": [
        "The value may still be outside the array bounds.",
        "Parsing automatically grants access to every index.",
        "Every integer is a valid index."
      ],
      "correct": 0,
      "answer": "The parsed value must also fall within the valid index range.",
      "explanation": "Parsing establishes a numeric representation. It does not establish that the value is nonnegative and smaller than the array length.",
      "source": "Example notes, section 1"
    },
    {
      "id": "example-02",
      "type": "open",
      "topic": "integer validation",
      "prompt": "State the bounds required for an index i into an array of length n.",
      "answer": "The index must satisfy 0 <= i < n.",
      "explanation": "Zero is the first valid index, and n is already one past the last element. An empty array has no valid index.",
      "key_points": ["Nonnegative index", "Strictly less than the array length"],
      "source": "Example notes, section 1"
    }
  ]
}
```

The example's source is illustrative; replace it with references to material
actually read. `sources`, `notes`, and `schema_version` are metadata, not fields
the app currently enforces. Do not add runtime fields such as `bank` or
`display_type` to the saved questions.

## Check and deliver

1. Run the actual loader, from the app's project root, on the banks created or
   changed: `python3 quiz.py questions/<topic_slug>.json --validate`.
2. Review coverage against the source sections and check numerical examples independently.
   Review question quality separately: valid JSON cannot establish correctness,
   source coverage, unambiguous choices, or agreement between `correct`, `answer`,
   and `explanation`. Check those explicitly, plus duplicate prompts and rubrics.
3. Report the files, counts by style, source coverage, and any important caveats.
   Provide a command to start the bank and optionally its `--mode open` variant.
   State what validation actually ran. Never claim completion before banks are saved
   and validated; report incomplete work explicitly. Creating a bank does not require launching
   the interactive TUI or changing the app, README, or existing question banks.
