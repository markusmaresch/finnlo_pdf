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
        Opens a PDF with a complex page ordering, reorders the pages
        logically, and saves them as high-resolution PNG files.
        This version re-opens the PDF for each page to prevent rendering artifacts.
        """
        if not os.path.exists(self.pdf_source):
            logging.error(f"Source PDF not found: '{self.pdf_source}'")
            return False

        # --- Step 1: Determine the correct page order first ---
        # We open the document once just to get the page count and determine the mapping.
        try:
            doc = fitz.open(self.pdf_source)
            page_count = doc.page_count
            doc.close()  # Close it immediately after getting the count.
        except Exception as e:
            logging.error(f"Failed to initially open PDF '{self.pdf_source}' to get page count: {e}")
            return False

        if page_count == 0:
            logging.warning("PDF contains no pages.")
            return True

        if page_count % 2 != 0:
            logging.warning(
                f"PDF has an odd number of pages ({page_count}). The reordering logic assumes an even number.")

        logging.info(f"Processing '{self.pdf_source}' with {page_count} pages.")

        # Create a list to hold the *physical page indices* in their correct logical order.
        reordered_physical_indices = [None] * page_count

        # Unscramble the pages based on the "last, first, second, last-but-one..." layout.
        logging.info("Determining correct logical page order...")
        for i in range(page_count):
            # i = current physical page index (0-based)
            # logical_index = target logical page index (0-based)
            if i % 4 == 0 or i % 4 == 3:
                logical_index = page_count - 1 - (i // 2)
                reordered_physical_indices[logical_index] = i
            elif i % 4 == 1 or i % 4 == 2:
                logical_index = i // 2
                reordered_physical_indices[logical_index] = i

        # --- Step 2: Extract each page by re-opening the PDF every time ---
        # This is less efficient but provides a clean state for each page render,
        # which is necessary to prevent "phantom image" artifacts from older PDFs.
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Saving reordered pages to '{self.output_dir}/' by re-opening per page.")

        for logical_page_num, physical_page_index in enumerate(reordered_physical_indices):
            if physical_page_index is None:
                logging.warning(f"Could not find a mapping for logical page {logical_page_num + 1}. Skipping.")
                continue

            output_filename = os.path.join(self.output_dir, f"page_{logical_page_num + 1:02d}.png")

            doc_instance = None
            try:
                # Open a new instance of the document for this page only.
                doc_instance = fitz.open(self.pdf_source)
                page = doc_instance.load_page(physical_page_index)

                # For old or complex PDFs, cleaning the content stream before rendering
                # can resolve issues like phantom images or incorrect layering.
                page.clean_contents()

                # Render the page to a pixmap with the specified DPI for high resolution.
                pix = page.get_pixmap(dpi=self.output_dpi)
                pix.save(output_filename)
                logging.info(f"Saved '{output_filename}' (from physical page {physical_page_index + 1})")

            except Exception as e:
                logging.error(f"Failed to save page {logical_page_num + 1} to '{output_filename}': {e}")
            finally:
                # CRITICAL: Ensure the document instance is closed for every page.
                if doc_instance:
                    doc_instance.close()

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
