"""Install a project """

import logging
import qibuild

def install_project(args, project):
    r"""Build a project.

    /!\ assumes that set_build_configs has been called
    """
    pass

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.project_parser(parser)
    qibuild.parsers.build_parser(parser)
    group = parser.add_argument_group("install arguments")
    group.add_argument("destdir", metavar="DESTDIR")
    # Force use_deps to be false, because we want to install
    # only the runtime dependencies by default.
    parser.set_defaults(use_deps=False)

def do(args):
    """Main entry point"""
    logger = logging.getLogger(__name__)
    toc      = qibuild.toc.open(args.work_tree, args, use_env=True)

    (project_names, _, _) = qibuild.toc.resolve_deps(toc, args, runtime=True)

    logger.info("Installing %s to %s", ", ".join([n for n in project_names]), args.destdir)
    for project_name in project_names:
        project = toc.get_project(project_name)
        qibuild.project.install(project,  args.destdir)
