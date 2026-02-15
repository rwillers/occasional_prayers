from pelicanconf import *  # noqa: F403,F401

# Fast smoke config for migration iteration.
# Keeps output tiny and avoids expensive full-corpus generation.
OUTPUT_PATH = "_build_pelican_smoke"
PAGE_PATHS = ["acna2019"]
STATIC_PATHS = ["css", "js", "images", "manifest.json"]
