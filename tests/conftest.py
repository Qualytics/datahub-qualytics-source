"""Pytest configuration.

Pulls in DataHub's own golden-file hooks rather than reimplementing them, so
`--update-golden-files` behaves exactly as it does in the monorepo and the tests port
across unchanged. The plugin also pins the test process to UTC, which keeps golden
timestamps stable regardless of the developer's clock.
"""

pytest_plugins = ["datahub.testing.pytest_hooks"]
