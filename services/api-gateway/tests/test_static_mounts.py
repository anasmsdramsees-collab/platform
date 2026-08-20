"""The console and design-system static mounts (ADR-007, ADR-008).

The gateway serves the console because the hub runs no Node runtime and a second
origin would need its own authorization. The design system is mounted separately
rather than nested under `/console`, because the console mount claims
`/console/*` wholesale and a nested mount would never be reached.

Neither mount is authenticated, and that is deliberate: both serve stylesheets
and markup, never household data. What must be true is that they serve *only*
that — hence the traversal tests.
"""

import pytest
from fastapi.testclient import TestClient

DESIGN_SYSTEM_ASSETS = [
    "/design-system/tokens/tokens.css",
    "/design-system/tokens/motion.css",
    "/design-system/themes/dark-theme.css",
    "/design-system/themes/light-theme.css",
    "/design-system/typography/typography.css",
    "/design-system/foundation.css",
    "/design-system/primitives.css",
]

CATALOGUE_ASSETS = [
    "/console/catalogue/",
    "/console/catalogue/catalogue.css",
    "/console/catalogue/catalogue.js",
]


@pytest.mark.parametrize("path", DESIGN_SYSTEM_ASSETS + CATALOGUE_ASSETS)
def test_the_design_system_and_catalogue_are_served(client: TestClient, path: str) -> None:
    # The catalogue links these by absolute path. If a mount moves, the page
    # renders unstyled rather than failing, so this is the only thing that
    # would catch it.
    response = client.get(path)
    assert response.status_code == 200, path
    assert response.content


def test_the_catalogue_needs_no_token(client: TestClient) -> None:
    # It shows the design system, not a home. Requiring a token would make the
    # style guide unreachable to a designer.
    assert client.get("/console/catalogue/").status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/design-system/../../../pyproject.toml",
        "/design-system/tokens/../../../../.env",
        "/design-system/../../../../etc/passwd",
        "/console/../../../pyproject.toml",
    ],
)
def test_a_static_mount_cannot_escape_its_directory(client: TestClient, path: str) -> None:
    # A new static mount is a new place to ask for files. `.env` holds the
    # credentials the whole platform is built to keep out of the repository.
    assert client.get(path).status_code == 404


def test_the_design_system_serves_no_source_of_truth_it_should_not(
    client: TestClient,
) -> None:
    # tokens.json is the source the CSS is generated from. Serving it is
    # harmless — it is public design data — but it must resolve inside the
    # mount rather than anywhere else.
    response = client.get("/design-system/tokens/tokens.json")
    assert response.status_code == 200
    assert "syltra" in response.text.lower()
