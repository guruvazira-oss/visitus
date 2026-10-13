.PHONY: help setup dataset validate demo evaluate agreement thresholds report charts test lint format dashboard clean
help:
	@echo "Targets: setup dataset validate demo evaluate agreement thresholds report charts test lint format dashboard clean"
setup:
	uv sync
dataset:
	uv run voice-eval generate-dataset
validate:
	uv run voice-eval validate-dataset
demo:
	uv run voice-eval demo
evaluate:
	uv run voice-eval evaluate --provider anthropic --rubric v1
agreement:
	uv run voice-eval agreement --rubric v1
thresholds:
	uv run voice-eval thresholds --rubric v1
report:
	uv run voice-eval report
charts:
	uv run voice-eval charts
test:
	uv run pytest
lint:
	uv run ruff check .
format:
	uv run ruff format .
dashboard:
	uv run streamlit run app.py
clean:
	rm -rf results/cache results/figures results/analysis .pytest_cache .ruff_cache
