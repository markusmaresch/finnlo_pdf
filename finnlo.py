#
# -*- coding: utf-8 -*-
#
import sys
import logging
import os

import numpy as np
import cv2

import fitz  # This is the PyMuPDF library

from py_log_util.log_wrapper import LogWrapper


class FinnloPdf:
    def __init__(self):
        self.pdf_source = '3842.pdf'
        self.raw_directory = 'pages_raw'
        self.crop_directory = 'cropped_raw'
        self.output_dpi = 300
        self.crop_strip_height_ratio = 0.3
        self.crop_definitions = [
            {
                'pages': range(44, 83),
                'description': 'Strips from Vertical Breaks',
                'breaks': [
                    0.07,  # Start of the first strip at the very top
                    0.36,  # Start of the second strip
                    0.65  # Start of the third strip
                ]
            }
        ]

    def get_page_raw(self, index_zero: int) -> str:
        return os.path.join(self.raw_directory, f'page_{index_zero + 1:02d}.png')

    def get_page_crop(self, index_zero: int, sub_index: int) -> str:
        return os.path.join(self.crop_directory, f'page_{index_zero + 1:02d}_{sub_index + 1:02d}.png')

    def crop_details(self) -> bool:
        """
        Crops specified pages into horizontal strips of a fixed, adjustable height,
        starting at the vertical breaks defined in self.crop_definitions.
        """
        logging.info("Starting to crop pages based on defined rules...")
        os.makedirs(self.crop_directory, exist_ok=True)

        # Iterate through each cropping rule in our configuration table
        for rule in self.crop_definitions:
            page_range = rule['pages']
            y_start_ratios = rule['breaks']
            description = rule.get('description', 'custom crop')

            logging.info(f"Applying rule '{description}' to pages {page_range.start}-{page_range.stop - 1}")
            logging.info(f"Using a fixed strip height of {self.crop_strip_height_ratio * 100:.0f}% of page height.")

            # Loop through the page numbers defined in the current rule
            for page_number in page_range:
                # Convert 1-based page number to 0-based index for file access
                i = page_number - 1
                page_raw_name = self.get_page_raw(i)

                if not os.path.exists(page_raw_name):
                    logging.warning(f"Source page '{page_raw_name}' not found, skipping crop.")
                    continue

                try:
                    # Load the full page image using OpenCV
                    image = cv2.imread(page_raw_name)
                    if image is None:
                        logging.error(f"Failed to load image '{page_raw_name}' with OpenCV.")
                        continue

                    height, _, _ = image.shape

                    # Calculate the fixed height in pixels for all strips from the ratio
                    strip_height_px = int(height * self.crop_strip_height_ratio)

                    # Create and save each horizontal crop based on the defined start points
                    for sub_index, y_start_ratio in enumerate(y_start_ratios):
                        # Calculate absolute pixel coordinates for the start of the strip
                        y_start = int(height * y_start_ratio)

                        # Calculate the end coordinate based on the fixed strip height
                        y_end = y_start + strip_height_px

                        # Ensure the crop does not go beyond the image boundary
                        y_end = min(y_end, height)

                        # Perform the horizontal slice using numpy array slicing
                        crop_img = image[y_start:y_end, :]

                        # Save the cropped image
                        crop_filename = self.get_page_crop(i, sub_index)
                        cv2.imwrite(crop_filename, crop_img)
                        logging.info(f"Saved cropped image '{crop_filename}'")

                except Exception as e:
                    logging.error(f"Failed to crop page '{page_raw_name}': {e}")
                    # Continue to the next page even if one fails

        logging.info("Cropping process finished.")
        return True

    def extract_pages(self) -> bool:

        prn0 = self.get_page_raw(0)
        if os.path.exists(prn0):
            logging.info('Done with extracting pages, have: {prn0}')
            return True

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
        os.makedirs(self.raw_directory, exist_ok=True)
        logging.info(f"Saving pages in physical order as PNGs to '{self.raw_directory}/'")

        # Iterate through each page in the PDF.
        try:
            for i, page in enumerate(doc):
                if page is None:
                    logging.warning(f"Could not process physical page {i + 1}. Skipping.")
                    continue

                page_raw_name = self.get_page_raw(i)
                pix = page.get_pixmap(dpi=self.output_dpi)
                pix.save(page_raw_name)
                logging.info(f"Saved '{page_raw_name}' (Physical Page {i + 1})")
        except Exception as e:
            logging.error(f"Failed to save page to image: {e}")
            return False
        finally:
            doc.close()
            logging.info("Processing complete.")
            return True

    def run(self) -> bool:
        if not self.extract_pages():
            return False
        if not self.crop_details():
            return False
        return True


def main() -> int:
    LogWrapper(logging.INFO, __file__).setup()
    dcc = FinnloPdf()
    if not dcc.run():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
