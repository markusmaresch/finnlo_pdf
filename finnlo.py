#
# -*- coding: utf-8 -*-
#
import sys
import logging

from py_log_util.log_wrapper import LogWrapper


class FinnloPdf:
    def __init__(self):
        self.pdf_source = '3841.pdf'

    def run(self) -> bool:
        return True


def main() -> int:
    LogWrapper(logging.INFO, __file__).setup()
    dcc = FinnloPdf()
    if not dcc.run():
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
