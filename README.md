# 📚 quiz_tui

![Python 3](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![Standard library](https://img.shields.io/badge/dependencies-standard_library-green)
![Codex feedback](https://img.shields.io/badge/open_answers-Codex_feedback-purple)

A small terminal quiz for practicing understanding with reusable JSON question banks.
Write an answer, submit it, and get **correct / partial / incorrect** feedback,
missing points and a model answer. Multiple-choice questions are graded locally.

## Get started

Requires Python 3 with `curses` on Linux/macOS. Open answers also require
[Codex CLI](https://developers.openai.com/codex/cli/), a working login and network access.

```sh
git clone https://github.com/Nickmadia/quiz_tui.git
cd quiz_tui
codex login
python3 quiz.py questions/iot_03_wlan.json
```

```sh
# Choose a model available to your Codex account
python3 quiz.py questions/iot_03_wlan.json --model MODEL_ID

# Mix banks, practice 10 questions, hide any multiple-choice options
python3 quiz.py questions/*.json --count 10 --mode open
```

Without `--model`, your Codex configuration selects the model. See `--help` for
filters, reproducible shuffling and grading timeout options.

## Controls

| Action | Key |
| --- | --- |
| Submit an open answer / insert a newline | Ctrl-D / Enter |
| Choose a multiple-choice answer | ↑ ↓ then Enter, or 1–9 |
| Continue after feedback / scroll | Enter / PgUp, PgDn |
| Quit, including while grading | Ctrl-G |

Failed assessments offer **Retry** or **Skip**; skipped answers do not lower your
score. The summary can retry missed or ungraded questions. There is no self-rating.

## How it works

The Python standard library handles the TUI, bank validation and shuffling.
Each open answer is sent with its question and rubric to an ephemeral, read-only
`codex exec` request. Feedback returns as structured JSON. Grading uses your Codex
allowance and can make mistakes; responses and scores are not saved by the app.
Multiple-choice practice and `--validate` work offline.

## Banks and authoring

Included: **151 open questions** covering IoT access protocols (38), WLAN (26),
WPAN (36), and LPWAN/application protocols/routing (51).
[Coverage and sources](questions/README.md) · [JSON format](docs/bank-format.md)

The bundled [question-bank skill](skills/quiz-question-banks/SKILL.md) guides Codex
through source reading, understanding-focused questions, rubrics and validation.
To install it:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/quiz-question-banks "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Check

```sh
python3 quiz.py questions/*.json --validate
python3 -m unittest discover -s . -p 'test_*.py'
```
