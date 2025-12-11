"""Constants used across the GCRS package."""

from typing import Literal

# Output file format constants
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMAT_MARKDOWN = "markdown"
OUTPUT_FORMAT_CSV = "csv"
OUTPUT_FORMAT_SARIF = "sarif"

# Output file format to extension mapping
OUTPUT_FILE_FORMAT_EXTENSIONS = {
    OUTPUT_FORMAT_JSON: ".json",
    OUTPUT_FORMAT_MARKDOWN: ".md",
    OUTPUT_FORMAT_CSV: ".csv",
    OUTPUT_FORMAT_SARIF: ".sarif.json",
}

# Type hint for output formats (for use in Literal types)
OutputFormat = Literal["json", "markdown", "csv", "sarif"]
