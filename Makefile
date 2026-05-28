.PHONY: ci-local test compliance offline-guard release-check release-build wheelhouse offline-bundle

test:
	PYTHONPATH=src:. python -m pytest -q

compliance:
	PYTHONPATH=src:. python tools/check_compliance.py

offline-guard:
	PYTHONPATH=src:. python tools/check_offline_guard.py

ci-local: test compliance offline-guard

release-check:
	PYTHONPATH=src:. python scripts/release_check.py --run-tests

release-build:
	PYTHONPATH=src:. python scripts/build_release.py

wheelhouse:
	PYTHONPATH=src:. python scripts/build_offline_wheelhouse.py

offline-bundle:
	PYTHONPATH=src:. python scripts/create_offline_bundle.py dist/imbizo-cs-workbench-1.5.0-offline
