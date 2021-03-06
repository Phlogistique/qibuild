## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Update every toolchain using the feed that was used to create them

If a toolchain name is given, only update this toolchain.
If a feed url is given, use this feed instead of the recorded one
to update the given toolchain.
"""

from qisys import ui
import qisys.parsers
import qitoolchain

def configure_parser(parser):
    """ Configure parser for this action """
    qisys.parsers.default_parser(parser)
    parser.add_argument("name", nargs="?", metavar="NAME",
        help="Update only this toolchain")
    parser.add_argument("feed", metavar="TOOLCHAIN_FEED",
        help="Use this feed location to update the toolchain.\n",
        nargs="?")
    parser.add_argument("--feed-name", dest="feed_name",
        help="Name of the feed. To be specified when using a git url")
    parser.add_argument("-b", "--branch",
        help="Branch of the git url to use")

def do(args):
    """Main entry point

    """
    feed = args.feed
    tc_name = args.name
    if tc_name:
        toolchain = qitoolchain.get_toolchain(tc_name)
        if not feed:
            feed = toolchain.feed_location
            if not feed:
                mess  = "Could not find feed for toolchain %s\n" % tc_name
                mess += "Please check configuration or " \
                        "specifiy a feed on the command line\n"
                ui.fatal(mess)
        toolchain.update(feed, branch=args.branch, name=args.feed_name)
    else:
        tc_names = qitoolchain.get_tc_names()
        tc_with_feed = [x for x in tc_names if qitoolchain.toolchain.Toolchain(x).feed_location]
        tc_without_feed = list(set(tc_names) - set(tc_with_feed))
        for i, tc_name in enumerate(tc_with_feed):
            ui.info_count(i, len(tc_with_feed),
		          ui.green, "Updating",
			  ui.blue, tc_name)
            toolchain = qitoolchain.toolchain.Toolchain(tc_name)
            tc_feed = toolchain.feed_location
            toolchain.update(tc_feed)
        if tc_without_feed:
            ui.info("These toolchains will be skipped because they have no feed:", ", ".join(tc_without_feed))
