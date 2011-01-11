
##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>
##
## Copyright (C) 2009, 2010, 2011 Aldebaran Robotics
##

import os
import platform
import subprocess
import logging
import qitools.configstore
import qitools.qiworktree

from   qibuild.project     import Project
import qitools.sh
from qibuild.dependencies_solver import DependenciesSolver
from   qitools.qiworktree import QiWorkTree
import qitoolchain

LOGGER = logging.getLogger("qibuild.toc")


class BadBuildConfig(Exception):
    """Custom exception"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        mess = self.message + "\n"
        mess += "Please check qi configuration"
        return mess


class Toc(QiWorkTree):
    def __init__(self, work_tree,
            build_type,
            toolchain_name,
            build_config,
            cmake_flags,
            cmake_generator):
        """
            work_tree      = a toc worktree
            build_type     = a build type, could be debug or release
            toolchain_name = by default the system toolchain is used
            build_config   = optional a build configuration
            cmake_flags    = optional additional cmake flags
            cmake_generator = optional cmake generator (defaults to Unix Makefiles)
        """
        QiWorkTree.__init__(self, work_tree)
        self.build_type        = build_type
        self.build_config      = build_config
        self.cmake_flags       = cmake_flags
        self.cmake_generator   = cmake_generator
        self.build_folder_name = None

        # List of objects of type qibuild.project.Project.
        self.projects          = list()

        # List of objects of type qitoolchain.toolchain.Packages,
        # provided by the current toolchain, if any
        self.packages          = list()

        # If toolchain_name is None, it was not given on command line,
        # look for it in the configuration:
        if not toolchain_name:
            toolchain_name = self.configstore.get("general", "build", "toolchain")
        # If it's not in the configuration, assume the name is
        # "system":
        if not toolchain_name:
            toolchain_name = "system"

        self.toolchain = qitoolchain.Toolchain(toolchain_name)
        self.packages = self.toolchain.packages

        if not self.build_config:
            self.build_config = self.configstore.get("general", "build", "config", default=None)

        if not self.cmake_generator:
            self.cmake_generator = self.configstore.get("general", "build" ,
                    "cmake_generator", default="Unix Makefiles")

        # Useful vars:
        self.using_visual_studio = "Visual Studio" in self.cmake_generator
        self.vc_version = self.cmake_generator.split()[-1]
        self.using_nmake =  "NMake" in self.cmake_generator

        self._set_build_folder_name()

        # self.buildable_projects has been set by QiWorkTree.__init__
        for pname, ppath in self.buildable_projects.iteritems():
            project = Project(ppath)
            project.update_build_config(self, self.build_folder_name)
            project.update_depends(self)
            self.projects.append(project)

        self.set_build_env()



    def _set_build_folder_name(self):
        """Get a reasonable build folder.
        The point is to be sure we don't have two incompatible build configurations
        using the same build dir.

        Return a string looking like
        build-linux-release
        build-cross-debug ...
        """
        res = ["build"]
        if self.toolchain.name != "system":
            res.append(self.toolchain.name)
        else:
            res.append("sys-%s-%s" % (platform.system().lower(), platform.machine().lower()))
        if not self.using_visual_studio and self.build_type != "debug":
            # When using cmake + visual studio, sharing the same build dir with
            # several build config is mandatory.
            # Otherwise, it's not a good idea, so we always specify it
            # when it's not "debug"
            res.append(self.build_type)

        if self.build_config:
            res.append(self.build_config)

        if self.using_visual_studio:
            # When using visual studio, different version of the compilator
            # produces incompatible binaries, so put vc version in the build dir
            # nane
            res.append("vs%s" % self.vc_version())

        if self.using_nmake:
            # TODO: guess vc version from general.env.bat_file?
            res.append("nmake")

        self.build_folder_name = "-".join(res)

    def get_project(self, project_name):
        """Return a project from a name.

        Return None if project was not in the known projects
        of this toc object

        """
        res = [p for p in self.projects if p.name == project_name]
        if len(res) == 1:
            return res[0]
        else:
            return None


    def get_sdk_dirs(self, project_name):
        """ return a list of sdk, needed to build a project """
        dirs = list()

        known_project_names = [p.name for p in self.projects]
        if project_name not in known_project_names:
            raise Exception("%s is not a buildable project" % project_name)

        dep_solver = DependenciesSolver(projects=self.projects, packages=self.toolchain.packages)
        (project_names, package_names, not_found) = dep_solver.solve([project_name])

        project_names.remove(project_name)

        for package_name in package_names:
            dirs.append(self.toolchain.get(package_name))
        for project_name in project_names:
            project = self.get_project(project_name)
            dirs.append(project.get_sdk_dir())

        if not_found and self.toolchain_name != "system":
            LOGGER.warning("Could not find projects %s", ", ".join(not_found))

        LOGGER.debug("sdk_dirs for %s : %s", project_name, dirs)
        return dirs


    def set_build_env(self):
        """Update os.environ using the qibuild configuration file

        """
        env = self.configstore.get("general", "env")
        if not env:
            return
        path = env.get("path")
        if not path:
            return
        path = path.strip()
        path = path.replace("\n", "")
        env_path = os.environ["PATH"]
        if not env_path.endswith(";"):
            env_path += ";"
        env_path += path
        os.environ["PATH"] = env_path
        bat_file = env.get("bat_file")
        if not bat_file:
            return
        # Quick hack to get env vars from a .bat script
        # (stolen idea from distutils/msvccompiler)
        # TODO: handle non asccii chars?
        # Hint: decode("mcbs") ...
        if not os.path.exists(bat_file):
            raise BadBuildConfig("general.env.bat_file (%s) does not exists", bat_file)

        interesting = set(("INCLUDE", "LIB", "LIBPATH", "PATH"))
        result = {}

        popen = subprocess.Popen('"%s"& set' % (bat_file),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        stdout, stderr = popen.communicate()
        if popen.wait() != 0:
            raise BadBuildConfig("Calling general.env.bat_file failed!: %s", stderr)

        for line in stdout.split("\n"):
            if '=' not in line:
                continue
            line = line.strip()
            key, value = line.split('=', 1)
            key = key.upper()
            if key in interesting:
                if value.endswith(os.pathsep):
                    value = value[:-1]
                result[key] = value

        LOGGER.debug("Updating os.environ with %s" , result)
        os.environ.update(result)


def toc_open(work_tree, args, use_env=False):
    build_config   = args.build_config
    build_type     = args.build_type
    toolchain_name = args.toolchain_name
    try:
        cmake_flags = args.cmake_flags
    except:
        cmake_flags = list()

    cmake_generator = args.cmake_generator

    if not work_tree:
        work_tree = qitools.qiworktree.guess_work_tree(use_env)
    if not work_tree:
        work_tree = qitools.qiworktree.search_manifest_directory(os.getcwd())
    if work_tree is None:
        raise Exception("Could not find toc work tree, please go to a valid work tree.")
    return Toc(work_tree,
               build_type=build_type,
               toolchain_name=toolchain_name,
               build_config=build_config,
               cmake_flags=cmake_flags,
               cmake_generator=cmake_generator)


def create(directory, args):
    """
    Create a new toc work_tree by configuring
    the template in qibuild/templates/build.cfg

    """
    # FIXME: could  this be interactive?
    qitools.qiworktree.create(directory)
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    template = os.path.join(cur_dir, "..", "qibuild", "templates", "build.cfg")
    cfg_path = os.path.join(directory, ".qi", "build.cfg")
    qitools.sh.configure_file(template, cfg_path, copy_only=True)


def resolve_deps(toc, args, runtime=False):
    """ Return the list of project specified in args. This is usefull to extract
        a project list from command line arguments. The returned list contains

        case handled:
          - nothing specified: get the project from the cwd
          - args.single: do not resolve dependencies
          - args.only_deps: only return dependencies
          - args.use_deps: take dependencies into account
    """
    if args.projects == [ None ]:
        project_names = list()
    else:
        project_names = args.projects

    if not project_names:
        LOGGER.debug("no project specified, guessing from current working directory")
        project_dir = qitools.qiworktree.search_manifest_directory(os.getcwd())
        if project_dir:
            LOGGER.debug("Found %s from current working directory",
                os.path.split(project_dir)[-1])
            project_names = [ os.path.split(project_dir)[-1] ]

    dep_solver = DependenciesSolver(projects=toc.projects,
                                    packages=toc.toolchain.packages)
    return dep_solver.solve(project_names,
        single=args.single,
        all=args.all,
        runtime=runtime)




open = toc_open
