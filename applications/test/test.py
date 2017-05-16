#!/usr/bin/env python
"""Automatically collect and run unit tests."""

from __future__ import division, print_function
import subprocess
import argparse
import os
import glob
from subprocess import STDOUT

# Run from this directory
this_dir = os.path.abspath(os.path.dirname(__file__))
os.chdir(this_dir)


def collect_test_dirs():
    """Loop through test application directories looking for ``Make``
    subdirectories.
    """
    return sorted([d for d in os.listdir(".") if os.path.isdir(d) \
                   and "Make" in os.listdir(d)])


def get_test_exe_name(test_dir):
    """Get the name of the test executable."""
    with open("Make/files") as f:
        for line in f.readlines():
            if line.strip().startswith("EXE"):
                return line.strip().split("/")[-1]


def test_single(test_dir, autopar=True):
    """Run one unit test.

    If ``autopar`` is ``True`` and test executable has ``parallel` in its name,
    it will be run in parallel.
    """
    os.chdir(test_dir)
    run_out = ""
    compile_out = ""
    try:
        compile_out = subprocess.check_output("wmake", stderr=STDOUT).decode()
        test_compiled = True
    except subprocess.CalledProcessError as e:
        compile_out += e.output.decode()
        test_compiled = False
    if test_compiled:
        test_exe = get_test_exe_name(test_dir)
        if autopar and "parallel" in test_exe.lower():
            test_exe = "mpirun -np 2 " + test_exe
        try:
            run_out = subprocess.check_output(test_exe, stderr=STDOUT,
                                              shell=True).decode()
            test_ran = True
        except subprocess.CalledProcessError as e:
            run_out += e.output.decode()
            test_ran = False
    else:
        test_ran = False
    os.chdir(this_dir)
    return test_compiled, test_ran, compile_out, run_out


def clean(test_dirs="all"):
    """Go through all directories and clean executables."""
    if test_dirs == "all":
        test_dirs = collect_test_dirs()
    for d in test_dirs:
        subprocess.call(["wclean", d])


def test_multiple(test_dirs="all", verbose=False):
    """Run multiple tests."""
    if test_dirs == "all":
        test_dirs = collect_test_dirs()
    print("\nRunning OpenFOAM unit tests")
    print("\nCollected {} tests\n".format(len(test_dirs)))
    status_str = ""
    errored = []
    passed = []
    failed = []
    err_out = ""
    fail_out = ""
    std_out = ""
    for test_dir in test_dirs:
        if verbose:
            print("Testing {:24s}".format(test_dir + "..."), end="", sep=" ")
        c, p, cout, rout = test_single(test_dir)
        if not c:
            if verbose:
                print("ERROR")
            errored.append(test_dir)
            status_str += "E"
            err_out += cout
        elif not p:
            if verbose:
                print("FAIL")
            failed.append(test_dir)
            status_str += "F"
            fail_out += rout
        elif c and p:
            if verbose:
                print("PASS")
            passed.append(test_dir)
            status_str += "."
            std_out += rout
        if not verbose:
            print(status_str, end="", flush=True)
    print("\n")
    # Now print a summary
    print("Passed: {}/{}".format(len(passed), len(test_dirs)))
    if errored:
        print("Errored: {}/{}:".format(len(errored), len(test_dirs)), errored)
        print("\n====== COMPILATION ERRORS ======\n")
        print(err_out)
    if failed:
        print("Failed: {}/{}:".format(len(failed), len(test_dirs)), failed)
        print("\n====== RUN ERRORS ======\n")
        print(fail_out)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OpenFOAM unit tests")
    parser.add_argument("--tests", "-n", help="Which tests to run or clean",
                        default="all", choices=collect_test_dirs() + ["all"],
                        metavar="tests", nargs="+")
    parser.add_argument("--clean", "-c", action="store_true", default=False,
                        help="Clean all unit test executables")
    parser.add_argument("--verbose", "-v", action="store_true", default=False,
                        help="Print verbose output")
    args = parser.parse_args()
    if args.clean:
        clean_all(args.tests)
    else:
        test_multiple(args.tests, verbose=args.verbose)
