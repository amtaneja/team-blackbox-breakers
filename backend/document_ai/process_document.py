"""Run the included sample PDF through the configured Document AI processor."""

import json
from pathlib import Path

from document_ai.config import get_settings
from document_ai.service import process_pdf


if __name__ == "__main__":
    settings = get_settings()
    sample_path = Path(__file__).parent / "sample_data" / "inv_28_rajputana.pdf"
    result = process_pdf(sample_path.read_bytes(), settings)
    print(json.dumps(result, indent=2, ensure_ascii=False))
