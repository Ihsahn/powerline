# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import re

from powerline.lib.vcs import get_branch_name, get_file_status
from powerline.lib.shell import readlines
from powerline.lib.path import join
from powerline.lib.shell import which

_ref_url = re.compile(br'<url>(.+)</url>')
_ref_root = re.compile(br'<root>(.+)</root>')


class SvnRepository(object):
    __slots__ = ('directory', 'create_watcher')

    def __init__(self, directory, create_watcher):
        self.directory = os.path.abspath(directory)
        self.create_watcher = create_watcher

    def status(self, path=None):
        if path:
            return get_file_status(
                directory=self.directory,
                dirstate_file=join(self.directory, '.svn', 'nofile'),
                file_path=path,
                ignore_file_name=join(self.directory, '.svn', 'nofile'),
                get_func=self.do_status,
                create_watcher=self.create_watcher,
            )
        return self.do_status(self.directory, path)

    def branch(self, url, root):
        return url.replace(root + "/", "").replace("branches/", "b/").replace("tags/", "t/")


class Repository(SvnRepository):
    def __init__(self, *args, **kwargs):
        if not which('svn'):
            raise OSError('svn executable is not available')
        super(Repository, self).__init__(*args, **kwargs)

    def do_status(self, directory, path):
        if path is not None:
            return get_file_status(
                directory=self.directory,
                dirstate_file=None,
                #join(self.directory, '.svn', '.nofile'),
                file_path=path,
                ignore_file_name=None,
                #join(self.directory, '.svn', '.nofile'),
                get_func=self.do_status,
                create_watcher=self.create_watcher,
            )
        dirtied = ' '
        untracked = ' '
        '''
        :'D?': dirty (tracked modified files: added, removed, deleted, modified),
        :'?U': untracked-dirty (added, but not tracked files)
        :None: clean (status is empty)
        '''
        if path:
            lines = self._svncmd(directory, "status", "--non-interactive", path)
        else:
            lines = self._svncmd(directory, "status", "--non-interactive", "--depth", "infinity",
                                 "--ignore-externals", directory)
        for line in lines:
            if dirtied == 'D' and untracked == 'U':
                break;
            if len(line) > 1 and line[0] in 'ADRMC!~':
                dirtied = 'D'
            elif len(line) > 1 and line[0] == '?':
                untracked = 'U'
        ans = dirtied + untracked
        return ans if ans.strip() else None

    def _svncmd(self, directory, *args):
        return readlines(('svn',) + args, directory)

    def branch(self):
        url = "<unknown>"
        root = ""
        for line in self._svncmd(self.directory, 'info', '--non-interactive', '--depth', 'empty', '--xml'):
            mUrl = _ref_url.match(line)
            if mUrl is not None:
                url = mUrl.group(1)
            else:
                mRoot = _ref_root.match(line)
                if mRoot is not None:
                    root = mRoot.group(1)
        return super(Repository, self).branch(url, root)
