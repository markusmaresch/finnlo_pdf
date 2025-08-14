#
# -*- coding: utf-8 -*-
#
import sys
import logging
import os

import fitz  # This is the PyMuPDF library

from py_log_util.log_wrapper import LogWrapper


class FinnloPdf:
    def __init__(self):
        self.pdf_source = '3842.pdf'
        self.output_dir = 'output_pages'
        self.output_dpi = 300  # DPI for high-resolution PNGs. Increase for higher quality.

    def extract_pages(self) -> bool:
        """
        Opens a PDF and saves each page in its physical order as a
        high-resolution PNG file.
        """
        if not os.path.exists(self.pdf_source):
            logging.error(f"Source PDF not found: '{self.pdf_source}'")
            return False

        try:
            doc = fitz.open(self.pdf_source)
        except Exception as e:
            logging.error(f"Failed to open or process PDF '{self.pdf_source}': {e}")
            return False

        page_count = doc.page_count
        if page_count == 0:
            logging.warning("PDF contains no pages.")
            doc.close()
            return True

        logging.info(f"Processing '{self.pdf_source}' with {page_count} pages for image extraction.")

        # Create the output directory if it doesn't already exist.
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Saving pages in physical order as PNGs to '{self.output_dir}/'")

        # Iterate through each page in the PDF.
        try:
            for i, page in enumerate(doc):
                if page is None:
                    logging.warning(f"Could not process physical page {i + 1}. Skipping.")
                    continue

                # Format filename with leading zeros (e.g., page_01.png, page_02.png, ...).
                output_filename = os.path.join(self.output_dir, f"page_{i + 1:02d}.png")

                # Render the page to a pixmap with the specified DPI for high resolution.
                pix = page.get_pixmap(dpi=self.output_dpi)

                # Save the pixmap as a PNG file.
                pix.save(output_filename)
                logging.info(f"Saved '{output_filename}' (Physical Page {i + 1})")
        except Exception as e:
            logging.error(f"Failed to save page to image: {e}")
            return False
        finally:
            doc.close()
            logging.info("Processing complete.")

        return True

    def run(self) -> bool:
        return self.extract_pages()


def main() -> int:
    LogWrapper(logging.INFO, __file__).setup()
    dcc = FinnloPdf()
    if not dcc.run():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
