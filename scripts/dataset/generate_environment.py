"""Thin shim so dataset scripts keep a stable import path.

The generator lives in the package (src/canarygame/environment.py) so the
harness and tests use the same source of truth.
"""

from canarygame.environment import (  # noqa: F401
    CredEntry,
    FixtureBundle,
    GeneratedStore,
    decoy_labels,
    generate_fixtures,
    generate_store,
)