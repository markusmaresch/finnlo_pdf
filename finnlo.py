#
# -*- coding: utf-8 -*-
#
import sys
import logging
import os

from pdf2image import convert_from_path
from pdf2image import pdfinfo_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

from py_log_util.log_wrapper import LogWrapper


class FinnloPdf:
    def __init__(self):
        self.pdf_source = '3841.pdf'
        self.output_dir = 'output_pages'
        self.output_dpi = 300  # DPI for high-resolution PNGs.

    def reorder_and_extract_pages(self) -> bool:
        """
        Opens a PDF with a complex page ordering, reorders the pages
        logically, and saves them as high-resolution PNG files using the
        Poppler rendering engine for maximum compatibility.
        """
        if not os.path.exists(self.pdf_source):
            logging.error(f"Source PDF not found: '{self.pdf_source}'")
            return False

        # --- Step 1: Determine the correct page order first ---
        # We still need to know the page count and calculate the mapping.
        # We can use a lightweight tool for this or stick to fitz for just the count.
        try:
            # Using pdf2image's info utility is a good way to check Poppler and get page count
            info = pdfinfo_from_path(self.pdf_source)
            page_count = info['Pages']
        except PDFInfoNotInstalledError:
            logging.error("Poppler not found. Make sure it's installed and in your system's PATH.")
            return False
        except Exception as e:
            logging.error(f"Failed to get PDF info from '{self.pdf_source}': {e}")
            return False

        if page_count == 0:
            logging.warning("PDF contains no pages.")
            return True

        logging.info(f"Processing '{self.pdf_source}' with {page_count} pages using Poppler.")

        # Create a list to hold the *physical page indices* in their correct logical order.
        reordered_physical_indices = [None] * page_count

        # Unscramble the pages based on the "last, first, second, last-but-one..." layout.
        logging.info("Determining correct logical page order...")
        for i in range(page_count):
            if i % 4 == 0 or i % 4 == 3:
                logical_index = page_count - 1 - (i // 2)
                reordered_physical_indices[logical_index] = i + 1  # Poppler is 1-based
            elif i % 4 == 1 or i % 4 == 2:
                logical_index = i // 2
                reordered_physical_indices[logical_index] = i + 1  # Poppler is 1-based

        # --- Step 2: Extract each page using pdf2image (Poppler) ---
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Saving reordered pages to '{self.output_dir}/' using pdf2image.")

        for logical_page_num, physical_page_index in enumerate(reordered_physical_indices):
            if physical_page_index is None:
                logging.warning(f"Could not find a mapping for logical page {logical_page_num + 1}. Skipping.")
                continue

            output_filename_base = os.path.join(self.output_dir, f"page_{logical_page_num + 1:02d}")

            try:
                # convert_from_path extracts pages and returns them as a list of PIL Image objects.
                # By specifying first_page and last_page, we extract only one page at a time,
                # ensuring a completely clean rendering environment for each.
                image = convert_from_path(
                    self.pdf_source,
                    dpi=self.output_dpi,
                    first_page=physical_page_index,
                    last_page=physical_page_index,
                    fmt='png',  # Specify the output format
                    thread_count=1  # Process one page at a time
                )

                if image:
                    # The result is a list, so we take the first (and only) element.
                    image[0].save(f"{output_filename_base}.png", 'PNG')
                    logging.info(f"Saved '{output_filename_base}.png' (from physical page {physical_page_index})")
                else:
                    logging.warning(f"Poppler returned no image for page {physical_page_index}.")

            except Exception as e:
                logging.error(f"Failed to save page {logical_page_num + 1} to '{output_filename_base}.png': {e}")

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
