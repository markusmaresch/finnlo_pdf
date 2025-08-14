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
        self.pdf_source = '3841.pdf'
        self.output_dir = 'output_pages'
        self.output_dpi = 300  # DPI for high-resolution PNGs. Increase for higher quality.

    def reorder_and_extract_pages(self) -> bool:
        """
        Opens a PDF with booklet-style page ordering, reorders the pages
        logically, and saves them as high-resolution PNG files.
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

        # This kind of layout usually requires an even number of pages.
        if page_count % 2 != 0:
            logging.warning(
                f"PDF has an odd number of pages ({page_count}). The reordering logic assumes an even number.")

        logging.info(f"Processing '{self.pdf_source}' with {page_count} pages.")

        # Create a list to hold the page objects in their correct logical order.
        reordered_pages = [None] * page_count

        # Unscramble the pages based on the "first, last, second, last-but-one" layout.
        for i in range(page_count):
            # i = current physical page index (0-based)
            # logical_index = target logical page index (0-based)

            # This pattern handles physical pages that belong at the end of the document,
            # working inwards (e.g., physical pages 1, 4, 5, 8...).
            if i % 4 == 0 or i % 4 == 3:
                logical_index = page_count - 1 - (i // 2)
                reordered_pages[logical_index] = doc[i]

            # This pattern handles physical pages that belong at the start of the document,
            # working forwards (e.g., physical pages 2, 3, 6, 7...).
            elif i % 4 == 1 or i % 4 == 2:
                logical_index = i // 2
                reordered_pages[logical_index] = doc[i]

        # Create the output directory if it doesn't already exist.
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Saving reordered pages to '{self.output_dir}/'")

        # Save the reordered pages as sequentially numbered PNG files.
        for i, page in enumerate(reordered_pages):
            if page is None:
                logging.warning(f"Could not find a mapping for logical page {i + 1}. Skipping.")
                continue

            # Format filename with leading zeros (e.g., page_01.png, page_02.png, ...).
            output_filename = os.path.join(self.output_dir, f"page_{i + 1:02d}.png")
            try:
                # Render the page to a pixmap with the specified DPI for high resolution.
                pix = page.get_pixmap(dpi=self.output_dpi)
                # Save the pixmap as a PNG file.
                pix.save(output_filename)
                logging.info(f"Saved '{output_filename}'")
            except Exception as e:
                logging.error(f"Failed to save page {i + 1} to '{output_filename}': {e}")

        doc.close()
        logging.info("Processing complete.")
        return True

    def run(self) -> bool:
        return self.reorder_and_extract_pages()


def main() -> int:
    LogWrapper(logging.INFO, __file__).setup()
    dcc = FinnloPdf()
    if not dcc.run():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
