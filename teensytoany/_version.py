# -*- coding: utf-8 -*-
# This file is part of 'miniver': https://github.com/jbweston/miniver
#
import os
from collections import namedtuple

Version = namedtuple("Version", ("release", "dev", "labels"))

# No public API
__all__ = []

package_root = os.path.dirname(os.path.realpath(__file__))
package_name = os.path.basename(package_root)

STATIC_VERSION_FILE = "_static_version.py"


def get_version(version_file=STATIC_VERSION_FILE):
    version_info = get_static_version_info(version_file)
    version = version_info["version"]
    if version == "__use_git__":
        version = get_version_from_git()
        if not version:
            version = get_version_from_git_archive(version_info)
        if not version:
            version = Version("unknown", None, None)
        return pep440_format(version)
    else:
        return version


def get_static_version_info(version_file=STATIC_VERSION_FILE):
    version_info = {}
    with open(os.path.join(package_root, version_file), "rb") as f:
        exec(f.read(), {}, version_info)
    return version_info


def version_is_from_git(version_file=STATIC_VERSION_FILE):
    return get_static_version_info(version_file)["version"] == "__use_git__"


def pep440_format(version_info):
    release, dev, labels = version_info

    version_parts = [release]
    if dev:
        # prefer PEP440 over strict adhesion to semver
        version_parts.append(".post{}".format(dev))

    if labels:
        version_parts.append("+")
        version_parts.append(".".join(labels))

    return "".join(version_parts)


def get_version_from_git():
    import subprocess

    # The '--long' flag gets us the 'dev' version and
    # The '--dirty' flag helps identify if files have been modified
    # git hash, '--always' returns the git hash even if there are no tags.
    for opts in [[]]:
        try:
            p = subprocess.Popen(
                ["git", "describe", "--long", "--always", "--dirty", "--tags"] + opts,
                cwd=package_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError:
            return
        if p.wait() == 0:
            break
    else:
        return

    description = (
        p.communicate()[0]
        .decode()
        .lstrip("v")  # Tags can have a leading 'v', but the version should not
        .rstrip("\n")
        .split("-")  # Split the latest tag, commits since tag, and hash
    )

    try:
        release, dev, git = description[:3]
    except ValueError:  # No tags, only the git hash
        # prepend 'g' to match with format returned by 'git describe'
        git = "g{}".format(*description)
        release = "unknown"
        dev = None

    labels = []
    if dev == "0":
        dev = None
    else:
        labels.append(git)

    if description[-1] == "dirty":
        labels.append("dirty")

    return Version(release, dev, labels)


# TODO: change this logic when there is a git pretty-format
#       that gives the same output as 'git describe'.
#       Currently we can only tell the tag the current commit is
#       pointing to, or its hash (with no version info)
#       if it is not tagged.
def get_version_from_git_archive(version_info):
    try:
        refnames = version_info["refnames"]
        git_hash = version_info["git_hash"]
    except KeyError:
        # These fields are not present if we are running from an sdist.
        # Execution should never reach here, though
        return None

    if git_hash.startswith("$Format") or refnames.startswith("$Format"):
        # variables not expanded during 'git archive'
        return None

    VTAG = "tag: v"
    refs = set(r.strip() for r in refnames.split(","))
    version_tags = set(r[len(VTAG):] for r in refs if r.startswith(VTAG))
    if version_tags:
        release, *_ = sorted(version_tags)  # prefer e.g. "2.0" over "2.0rc1"
        return Version(release, dev=None, labels=None)
    else:
        return Version("unknown", dev=None, labels=["g{}".format(git_hash)])


__version__ = get_version()


# The following section defines a 'get_cmdclass' function
# that can be used from setup.py. The '__version__' module
# global is used (but not modified).


def _write_version(fname):
    # This could be a hard link, so try to delete it first.  Is there any way
    # to do this atomically together with opening?
    try:
        os.remove(fname)
    except OSError:
        pass
    with open(fname, "w", encoding='utf-8') as f:
        f.write(
            "# This file has been created by setup.py.\n"
            "version = '{}'\n".format(__version__)
        )


def get_cmdclass(pkg_source_path):
    from setuptools.command.build_py import build_py as build_py_orig
    from setuptools.command.sdist import sdist as sdist_orig

    class _build_py(build_py_orig):
        def run(self):
            super().run()

            src_marker = "".join(["src", os.path.sep])

            if pkg_source_path.startswith(src_marker):
                path = pkg_source_path[len(src_marker):]
            else:
                path = pkg_source_path
            _write_version(
                os.path.join(
                    self.build_lib, path, STATIC_VERSION_FILE
                )
            )

    class _sdist(sdist_orig):
        def make_release_tree(self, base_dir, files):
            super().make_release_tree(base_dir, files)
            _write_version(
                os.path.join(base_dir, pkg_source_path, STATIC_VERSION_FILE)
            )

    return dict(sdist=_sdist, build_py=_build_py)
