#!/usr/bin/env python3

"""
@author: xi
@since: 2017-02-16
"""

import getopt
import sys
import os
import json
import paramiko as pk


class ZA(object):

    sep = '//'
    za_path = '.za'
    conf_path = os.path.join(za_path, 'conf.json')
    remote_info_path = os.path.join(za_path, 'remote_info')

    def __init__(self, conf):
        self.dirs_to_create = []
        self.files_to_create = []
        self.dirs_to_remove = []
        self.files_to_remove = []
        self.local_info = {}
        self.remote_info = {}
        #
        # configs
        hostname = conf['hostname']
        tokens = hostname.split(':')
        if len(tokens) == 1:
            self.host = hostname
            self.port = 22
        elif len(tokens) == 2:
            self.host = tokens[0]
            self.port = int(tokens[1])
        else:
            raise ValueError('Invalid hostname {}.'.format(hostname))
        self.username = conf['username']
        self.password = conf['password']
        self.project_dir_path = conf['project_dir']
        self.ignore_list = conf['ignore_list'] if 'ignore_list' in conf else []

    def sync(self):
        self._load_local_info()
        self._load_remote_info()
        self._make_tasks()
        trans = None
        try:
            trans = pk.Transport((self.host, self.port))
            trans.connect(username=self.username, password=self.password)
            sftp = pk.SFTPClient.from_transport(trans)
            self._do_tasks(sftp)
        finally:
            if trans is not None:
                trans.close()
        self._dump_remote_info()
        print('All clear.')

    def _load_local_info(self, path='.'):
        local_info = {}
        self._traverse_dir(path, local_info)
        self.local_info = local_info

    def _traverse_dir(self, path, info):
        for name in os.listdir(path):
            if name.startswith('.'):
                continue
            if name in self.ignore_list:
                continue
            file_path = os.path.join(path, name)
            if os.path.isdir(file_path):
                info[file_path] = -1
                self._traverse_dir(file_path, info)
            else:
                mtime = os.path.getmtime(file_path)
                info[file_path] = mtime

    def _load_remote_info(self):
        if not os.path.exists(ZA.remote_info_path):
            return
        with open(ZA.remote_info_path, 'r') as f:
            lines = f.readlines()
        remote_info = {}
        for index, line in enumerate(lines):
            line = line.strip()
            if line == '':
                continue
            tokens = line.split(ZA.sep)
            if len(tokens) != 2:
                raise ValueError(
                    'Remote info file corrupted in line {}.'.format(index)
                )
            path, mtime = tokens
            remote_info[path] = float(mtime)
        self.remote_info = remote_info

    def _make_tasks(self):
        local_info = self.local_info
        remote_info = self.remote_info
        #
        # create tasks
        items_to_create = local_info.keys() - remote_info.keys()
        for item in items_to_create:
            if local_info[item] < 0:
                self.dirs_to_create.append(item)
            else:
                self.files_to_create.append(item)
        self.dirs_to_create.sort(key=lambda x: len(x))
        #
        # update tasks
        items_to_update = local_info.keys() & remote_info.keys()
        for item in items_to_update:
            local_mtime = local_info[item]
            remote_mtime = remote_info[item]
            if local_mtime < 0 and remote_mtime < 0:
                continue
            if (local_mtime >= 0 and remote_mtime >= 0) \
                    and (local_mtime <= remote_mtime):
                continue
            self.files_to_remove.append(item)
            self.files_to_create.append(item)
        #
        # remove tasks
        items_to_remove = remote_info.keys() - local_info.keys()
        for item in items_to_remove:
            if remote_info[item] < 0:
                self.dirs_to_remove.append(item)
            else:
                self.files_to_remove.append(item)
        self.dirs_to_remove.sort(key=lambda x: -len(x))

    def _do_tasks(self, sftp):
        try:
            sftp.mkdir(self.project_dir_path)
        except:
            pass
        for item in self.files_to_remove:
            try:
                path = self._to_server_side_path(item)
                sftp.remove(path)
                del self.remote_info[item]
                print('{} removed.'.format(path))
            except Exception as e:
                print('Failed to remove {}.'.format(path))
        for item in self.dirs_to_remove:
            try:
                path = self._to_server_side_path(item)
                sftp.rmdir(path)
                del self.remote_info[item]
                print('{} removed.'.format(path))
            except Exception as e:
                print('Failed to remove {}.'.format(path))
        for item in self.dirs_to_create:
            try:
                path = self._to_server_side_path(item)
                sftp.mkdir(path)
                self.remote_info[item] = self.local_info[item]
                print('{} created.'.format(path))
            except Exception as e:
                print('Failed to create {}.'.format(path))
        for item in self.files_to_create:
            try:
                path = self._to_server_side_path(item)
                sftp.put(item, path)
                self.remote_info[item] = self.local_info[item]
                print('{} created.'.format(path))
            except Exception as e:
                print('Failed to create {}.'.format(path))

    def _to_server_side_path(self, client_path):
        path = os.path.join(self.project_dir_path, client_path[2:])
        return path.replace('\\', '/')

    def _dump_remote_info(self):
        with open(ZA.remote_info_path, 'w') as f:
            for path, mtime in self.remote_info.items():
                line = '{}//{}'.format(path, mtime)
                f.write(line)
                f.write('\n')


def complete_conf(conf):
    if 'hostname' not in conf:
        conf['hostname'] = input_hostname()
    if 'username' not in conf:
        conf['username'] = input_username()
    if 'password' not in conf:
        conf['password'] = input_password()
    if 'project_dir' not in conf:
        conf['project_dir'] = input_project_dir()


def input_hostname():
    while 1:
        host = input('Input hostname: ').strip()
        if len(host) != 0:
            break
        print('Hostname cannot be empty.')
    return host


def input_username():
    while 1:
        username = input('Input username: ').strip()
        if len(username) != 0:
            break
        print('Username cannot be empty.')
    return username


def input_password():
    while 1:
        password = input('Input password: ').strip()
        if len(password) != 0:
            break
        print('Password cannot be empty.')
    return password


def input_project_dir():
    while 1:
        project_dir = input('Input project dir name: ').strip()
        if len(project_dir) != 0:
            break
        print('Project dir name cannot be empty.')
    return project_dir


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'nh:u:p:d:')
    conf = {'is_new': False}
    for name, value in opts:
        if name in ['-n']:
            conf['is_new'] = True
        elif name in ['-h']:
            conf['hostname'] = value
        elif name in ['-u']:
            conf['username'] = value
        elif name in ['-p']:
            conf['password'] = value
        elif name in ['-d']:
            conf['project_dir'] = value
    #
    # init
    if conf['is_new']:
        del conf['is_new']
        if not os.path.exists(ZA.za_path):
            os.mkdir(ZA.za_path)
        complete_conf(conf)
        with open(ZA.conf_path, 'w') as f:
            json.dump(conf, f, indent=4)
        if os.path.exists(ZA.remote_info_path):
            os.remove(ZA.remote_info_path)
        exit()
    #
    # no need to init
    del conf['is_new']
    if not os.path.exists(ZA.conf_path):
        print('The dir is not under ZA\'s control.')
        exit(1)
    with open(ZA.conf_path, 'r') as f:
        conf1 = json.load(f)
    if len(conf) != 0:
        for key, value in conf.items():
            conf1[key] = value
        complete_conf(conf1)
        with open(ZA.conf_path, 'w') as f:
            json.dump(conf1, f, indent=4)
    try:
        ZA(conf1).sync()
    except Exception as e:
        print(e)
    exit()
