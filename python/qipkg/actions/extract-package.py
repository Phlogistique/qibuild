""" Extract the contents of a package """

import os
import zipfile

from qisys import ui
import qisys.parsers
import qipkg.package

def configure_parser(parser):
    qisys.parsers.default_parser(parser)
    parser.add_argument("pkg_path")
    parser.add_argument("--cwd", "-C", dest="output_path")

def do(args):
    pkg_path = args.pkg_path
    output_path = args.output_path
    if not output_path:
        output_path = os.getcwd()
    # Extract the manfist to a tempfile to
    # parse it
    archive = zipfile.ZipFile(pkg_path)
    name = None
    version = None
    pkg_name = None
    with qisys.sh.TempDir() as tmp:
        for name in archive.namelist():
            if name == "manifest.xml":
                archive.extract("manifest.xml", path=tmp)
                manifest_xml_path = os.path.join(tmp, "manifest.xml")
                pkg_name = qipkg.package.pkg_name(manifest_xml_path)
                break

    if pkg_name is not None:
        to_make = os.path.join(output_path, os.path.basename(pkg_name))
        output_path = os.path.join(output_path, pkg_name)
    qisys.sh.mkdir(to_make, recursive=True)
    archive.extractall(output_path)
    archive.close()
    ui.info(ui.green, "Package extracted to", ui.reset,
            ui.bold, output_path)
