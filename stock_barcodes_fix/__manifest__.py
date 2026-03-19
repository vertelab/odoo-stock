{
    "name": "OCA Stock Barcodes Fix",
    "summary": "Fixes for stock_barcodes module",
    "version": "16.0.0.1.0",
    "author": "Vertel AB",
    "website": "https://github.com/vertelab/odoo-stock",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "depends": ["stock_barcodes"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            ("replace", "stock_barcodes/static/src/views/views.esm.js", "stock_barcodes_fix/static/src/views/views.esm.js"),
        ],
    },
    "installable": True,
}
