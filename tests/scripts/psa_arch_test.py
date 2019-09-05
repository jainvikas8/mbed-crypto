#!/usr/bin/env python3
"""
This file is part of Mbed TLS (https://tls.mbed.org)

Copyright (c) 2019, Arm Limited, All Rights Reserved

Purpose

This script helps to tests the PSA compilance for crypto.
It can't be run offline, as it relies on 2 repo's
1. ARM-software/psa-arch-tests
2. ARMmbed/mbedtls-test

Run from mbed-crypto folder:
Example : ~/mbed-crypto$ ./tests/scripts/psa_arch_test.py
"""

import subprocess
import os
import sys
import traceback
import shutil

class PsaArchtest():
    """PSA Compliance Architecture Tests"""

    def __init__(self):
        """Initialize the PSA arch tests parameters."""
        self.git_command = "git"
        self.cmake_command = "cmake"
        self.make_command = "make"
        self.gcc_command = "gcc"
        self.working_folder = "psa-tests-temp"
        self.cmake_build_folder = "cmake_build"
        self.psa_arch_tests_repo = "git@github.com:jainvikas8/psa-arch-tests.git"
        self.psa_arch_tests_branch = "linux-target-support"
        self.mbedtls_test_repo = "git@github.com:ARMmbed/mbedtls-test.git"
        self.mbedtls_test_branch = "dev/jainvikas8/automate-psa"
        self.start_directory = os.getcwd()

    @staticmethod
    def execute_shell_cmd(arguments):
        """Execute shell command with set of arguments."""
        try:
            status = subprocess.check_output(
                arguments,
                stderr=subprocess.STDOUT
            ).decode("ascii").rstrip()
            print(status)
        except subprocess.CalledProcessError as e:
            print(e.output)

    def create_work_directory(self):
        """Create a work directory."""
        print("Current working directory is : " + self.start_directory)

        if os.path.exists(self.working_folder):
            print("Found a directory --" + self.working_folder + "-- therefore deleting it...")
            shutil.rmtree(self.working_folder)

        os.mkdir(self.working_folder)
        print("Directory ++" + self.working_folder + "++ created..")

        os.chdir(os.getcwd() + "/" + self.working_folder)

        print("Current working directory is : " + os.getcwd())

    def clone_repos(self):
        """Clone required repo's."""
        self.execute_shell_cmd([self.git_command, "clone",
                                self.psa_arch_tests_repo, "-b", self.psa_arch_tests_branch])
        self.execute_shell_cmd([self.git_command, "clone",
                                self.mbedtls_test_repo, "-b", self.mbedtls_test_branch])

    def build_crypto_library(self):
        """Build crypto"""
        self.execute_shell_cmd([self.make_command, "-C", "../", "clean"])
        self.execute_shell_cmd([self.make_command, "-C", "../", "-j"])

    def build_test_main(self):
        """Build psa test invoker."""
        self.execute_shell_cmd([self.gcc_command, "-Wall", "-Werror", "-c", "-o",
                                "./mbedtls-test/resources/psa-arch-tests/main.o",
                                "./mbedtls-test/resources/psa-arch-tests/main.c"])

    def prepare_build_directory(self):
        """Create a build directory for tests."""
        os.chdir(os.getcwd() + "/psa-arch-tests/api-tests/")
        print("Current working directory is : " + os.getcwd())

        if os.path.exists(self.cmake_build_folder):
            print("Found a directory --" + self.working_folder + "-- therefore deleting it...")
            shutil.rmtree(self.working_folder)

        os.mkdir(self.cmake_build_folder)
        print("Directory ++" + self.cmake_build_folder + "++ created..")

        os.chdir(os.getcwd() + "/" + self.cmake_build_folder)

        print("Current working directory is : " + os.getcwd())

    def build_psa_tests(self):
        """Build psa-arch-tests."""
        # Path of the psa headers generated
        psa_header_path = "-DPSA_INCLUDE_PATHS=" + os.path.realpath("../../../../include")

        self.execute_shell_cmd([self.cmake_command, "../", "-GUnix Makefiles",
                                "-DTOOLCHAIN=HOST_GCC", "-DTARGET=tgt_dev_apis_stdc",
                                "-DSUITE=CRYPTO", psa_header_path, "-DCPU_ARCH=armv7m"])

        self.execute_shell_cmd([self.cmake_command, "--build", "."])

    def link_psa_tests(self):
        """Link psa-arch-tests and generate a executable"""
        self.execute_shell_cmd([self.gcc_command, "-o", "psa-arch-crypto-tests",
                                "./mbedtls-test/resources/psa-arch-tests/main.o",
                                "./dev_apis/crypto/test_combine.a", "./val/val_nspe.a",
                                "./platform/pal_nspe.a", "./dev_apis/crypto/test_combine.a",
                                "../../../../library/libmbedcrypto.a"])

    def run_psa_tests(self):
        """Run executable"""
        self.execute_shell_cmd(["./psa-arch-crypto-tests"])

    def cleanup(self):
        """Cleanup"""
        os.chdir(self.start_directory)
        print("Current working directory is : " + self.start_directory)

        if os.path.exists(self.working_folder):
            print("Deleting --" + self.working_folder + "-- directory")
            shutil.rmtree(self.working_folder)

    def start(self):
        """Execute the following Step-by-Step"""
        self.create_work_directory()
        self.clone_repos()
        self.build_crypto_library()
        self.build_test_main()
        self.prepare_build_directory()
        self.build_psa_tests()
        self.link_psa_tests()
        return self.run_psa_tests()


def run_main():

    psa_test = PsaArchtest()
    try:
        return_code = psa_test.start()
        psa_test.cleanup()
        sys.exit(return_code)
    except Exception: # pylint: disable=broad-except
        # Print the backtrace and exit explicitly so as to exit with
        # status 2, not 1.
        traceback.print_exc()
        psa_test.cleanup()
        sys.exit(2)


if __name__ == "__main__":
    run_main()
