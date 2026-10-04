# Labs

Hands-on code for the book's technical chapters. Every lab is standard-library Python that runs on a laptop in seconds, with tests, and with a README that explains the intuition behind each piece, shows worked examples, and maps every function to the chapter section it belongs to. Nothing is installed; clone the repository and run the commands.

| Lab | Chapter | What it gives you | Start with |
|---|---|---|---|
| [`dataset-examples/`](dataset-examples/README.md) | 26d | A complete, validated example of every training, post-training and evaluation dataset type (SFT chats, preference pairs, reward-model labels, AI feedback, RL prompts with verifiers, eval sets with scorers, pairwise annotation, reasoning items, egocentric video, terminal and SWE tasks, an agentic gym, delivery, provenance, QA and ops files), each folder with its own README on how a model uses it, plus the calculations behind the chapter's numbers | `python3 validate_all.py` then `python3 how_models_use_it.py` |
| [`coding-patterns/`](coding-patterns/README.md) | 39d | Tested templates for the twenty coding-interview patterns and the families beyond them, checked against brute force | `python3 -B test_patterns.py` |
| [`algorithm-frameworks/`](algorithm-frameworks/README.md) | 39e, 39f, 39g | Data structures from arrays and linked nodes, the ten sorting algorithms, the classic templates, graph algorithms, backtracking, BFS, dynamic programming, greedy and math techniques | the three test files |
| [`python-brushup/`](python-brushup/README.md) | 49a | Thirty-eight exercises on Python fundamentals and advanced idioms, with reference solutions | `python3 -B test_exercises.py` |
| [`cs-essentials/`](cs-essentials/README.md) | 49b | A JWT signer and verifier, PKCE, a log-structured merge-tree store and a mutual-TLS demo | `python3 -B test_cs_essentials.py` |
| [`finops-analyst/`](finops-analyst/README.md) | 47g | Eighteen months of synthetic multi-cloud billing data with planted problems, and the forecasting, variance, anomaly, allocation, commitment, savings and executive-reporting analyses an analyst runs each month | `python3 finops_lab.py` |

**How the labs stay honest.** Three labs ship a `check_chapter_sync.py` that fails if any function shown in the chapter differs from the tested one in the lab, so the book's code and the lab's code are the same bytes. The dataset lab's `validate_all.py` runs every schema, consistency, checksum and grader check a delivery team would run. The Python chapter's own examples are executed from the Markdown by `tools/run_chapter_examples.py`.

**How to use them for interviews.** Read the chapter section, close it, implement the function from its docstring, run the tests, then compare with the reference. Each lab README has a practice loop and timing targets, and the pitfalls each test was written to catch.

Requirements: Python 3.10 or newer for the algorithm labs, 3.11 or newer for the rest (the terminal-task check in the dataset lab reads TOML with `tomllib`). The SWE-task grader needs `git` and `pytest`; the mutual-TLS demo needs `openssl`; both skip themselves cleanly when the tool is absent.
