# Milestone 4 figures

- `etf_allocation_erd.drawio` and `etf_allocation_erd_revised.pdf`: the current
  conceptual model and business identity assumptions.
- `system_architecture.pdf` / `.png`: compact report diagram of actual calls.
  Routes open/pass connections and call business helpers and DAL functions;
  repository writes invoke `validated_transaction`. File checks are optional
  when `capture_root` is supplied, as the report caption explains.
- `system_architecture.dot`: editable topology for optional Graphviz rendering.
- `ui_operations.pdf`: report layout of explicitly cropped screenshot excerpts.
  Search shows the filter and first two results. Creation shows the success
  message and Partial coverage. Update shows the success message, selected
  edited weights and saved total; intervening rows are omitted. Deletion shows
  its success message and the two remaining weights/total. Update and delete
  are separate examples, not successive states of one disclosure.
- `ui_screenshots/`: all nine unmodified full-resolution original captures,
  including provenance, portfolio and rejected-operation evidence.
- `figure2_ui_composite.png`: Mason's earlier full-page montage, retained as a
  historical layout; the final report uses the larger excerpts instead.

Rebuild canonical report figures with `python scripts/generate_report_figures.py`.
The generator uses vector drawing and PDF clipping of unchanged screenshots,
not image generation. Full originals are included in the submission ZIP with
lossless compression and identical pixels. Poppler's `pdftoppm` is optional
and refreshes the architecture PNG preview.
