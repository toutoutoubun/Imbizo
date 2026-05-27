.PHONY: ci-local

ci-local:
	PYTHONPATH=src:. python -m pytest -q
	PYTHONPATH=src:. python tools/check_compliance.py
	PYTHONPATH=src:. python tools/check_offline_guard.py
