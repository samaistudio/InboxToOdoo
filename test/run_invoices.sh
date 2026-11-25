#!/bin/zsh
# Runs the invoice test cases and compares each verdict with the expected one. See test/run_invoices.py.
cd ${0:A:h:h}
exec python3 test/run_invoices.py "$@"
