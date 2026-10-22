"""Vigil pipeline package — the shared ingest seam.

Both the demo path (canned scenarios) and the live path (real Ring/Bee/Fire TV/
Alexa+ device adapters) feed ONE pipeline through a single ``IngestAdapter``
interface, so the UI, the MCP server, and a live deployment all exercise the
same reasoning spine. Demo mode and live mode differ only in the ingest source,
never in the pipeline logic — this is the honest "device optional" seam.
"""
