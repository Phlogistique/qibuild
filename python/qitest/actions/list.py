""" List the tests"""


import os
import sys
from qisys import ui

import qibuild.parsers
import qitest.conf

def configure_parser(parser):
    qibuild.parsers.build_parser(parser)
    qibuild.parsers.project_parser(parser)

def do(args):
    build_worktree = qibuild.parsers.get_build_worktree(args)
    project = qibuild.parsers.get_one_build_project(build_worktree, args)
    qitest_cmake = os.path.join(project.build_directory, "qitest.cmake")
    if not os.path.exists(qitest_cmake):
        ui.error("No tests found for project", project.name)
        sys.exit(1)
    ui.info(ui.green, "Lists of tests for", ui.blue, project.name)
    tests = qitest.conf.parse_qitest_cmake(qitest_cmake)
    for i, test in enumerate(tests):
        ui.info_count(i, len(tests), test["name"])