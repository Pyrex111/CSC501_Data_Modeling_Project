#!/usr/bin/env python3
"""Capture the Milestone 5 UI screenshots against a fresh, throwaway graph.

Builds a new graph store in a temporary directory through the same startup path
as the application (ontology loaded, native validator + parity bridge attached),
loads the 356 synthetic triples, serves the Flask UI on a local port and drives
it with a headless browser. The persistent store in data/semantic_store is never
opened, so the screenshots are repeatable from a clean checkout.

Requires: pip install playwright && python -m playwright install chromium
Usage:    python scripts/capture_ui_screenshots.py [--out milestones/05_semantic/docs/screenshots]
"""
import argparse
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "ui"))

from werkzeug.serving import make_server  # noqa: E402

from app import app  # noqa: E402
from dal.seed_data import seed  # noqa: E402
from semantic.codec import export_connection  # noqa: E402
from semantic.runtime import open_graph_database  # noqa: E402
from semantic.vocabulary import schema_connection  # noqa: E402


def build_graph(path):
    sql = schema_connection()
    try:
        seed(sql, ROOT)
        graph = open_graph_database(path)
        graph.load_data(export_connection(sql))
        return graph
    finally:
        sql.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "milestones/05_semantic/docs/screenshots")
    parser.add_argument("--port", type=int, default=5055)
    parser.add_argument("--channel", default=None,
                        help="browser channel, e.g. chrome (default: bundled chromium)")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="etf-ui-shots-") as tmp:
        graph = build_graph(str(Path(tmp) / "store"))
        app.config.update(BACKEND="graph", GRAPH=graph, TESTING=False)
        server = make_server("127.0.0.1", args.port, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{args.port}"
        shots = []

        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 860})
            page.on("dialog", lambda d: d.accept())  # confirm() on Delete

            def shot(name, full=True):
                path = args.out / f"{name}.png"
                page.screenshot(path=str(path), full_page=full)
                shots.append(path.name)

            def set_weights(values):
                boxes = page.locator('input[form="batch"][name="weight"]')
                for i, v in enumerate(values):
                    if v is not None:
                        boxes.nth(i).fill(str(v))

            # 1-2 Retrieval: search all, then filter
            page.goto(base + "/")
            shot("01_search_all")
            page.fill('input[name="ticker"]', "sya")
            page.select_option('select[name="dimension"]', "Sector")
            page.click('button[type="submit"]')
            shot("02_search_filtered")

            # 3 Detail of a Complete disclosure
            page.goto(base + "/disclosure/2")
            shot("03_detail")

            # 4-5 Data entry: create a Partial disclosure
            page.goto(base + "/disclosure/new")
            page.select_option('select[name="etf_id"]', "2")
            page.select_option('select[name="dimension_id"]', "1")
            page.select_option('select[name="source_id"]', "2")
            page.fill('input[name="source_locator"]', "sector-table")
            page.fill('input[name="as_of_date"]', "2026-06-30")
            page.select_option('select[name="coverage_status"]', "Partial")
            cats = page.locator('select[name="category"]')
            weights = page.locator('input[name="weight"]')
            for i, (c, w) in enumerate((("1", "0.4"), ("2", "0.3"), ("3", "0.1"))):
                cats.nth(i).select_option(c)
                weights.nth(i).fill(w)
            shot("04_create_form")
            page.click('button:has-text("Create disclosure")')
            page.wait_for_load_state()
            new_url = page.url
            shot("05_create_saved")

            # 6 Duplicate create is rejected by the graph validators
            page.go_back()
            page.click('button:has-text("Create disclosure")')
            page.wait_for_load_state()
            shot("06_create_duplicate_rejected", full=False)

            # 7 Update: batch weight edit on the new disclosure
            page.goto(new_url)
            set_weights([0.45, 0.25, None])
            page.click('button:has-text("Save all weights")')
            page.wait_for_load_state()
            shot("07_update_saved")

            # 8 Update rejected: Complete total would not be 1; graph unchanged
            before = graph.snapshot()
            page.goto(base + "/disclosure/2")
            set_weights([0.455])  # Other Sectors 0.415 -> 0.455, total 1.04
            page.click('button:has-text("Save all weights")')
            page.wait_for_load_state()
            assert graph.snapshot() == before, "rejected update changed the graph"
            shot("08_update_rejected")

            # 9 Delete: remove the last entry of the Partial disclosure
            page.goto(new_url)
            page.locator('button.danger').last.click()
            page.wait_for_load_state()
            shot("09_delete_saved")

            # 10 Delete rejected on a Complete disclosure; graph unchanged
            before = graph.snapshot()
            page.goto(base + "/disclosure/2")
            page.locator('button.danger').first.click()
            page.wait_for_load_state()
            assert graph.snapshot() == before, "rejected delete changed the graph"
            shot("10_delete_rejected", full=False)

            # 11 Portfolio retrieval joining holdings to disclosures
            page.goto(base + "/portfolio?customer=1001")
            shot("11_portfolio")
            browser.close()

        server.shutdown()
        print("Saved", len(shots), "screenshots to", args.out)
        for s in shots:
            print(" -", s)


if __name__ == "__main__":
    main()
