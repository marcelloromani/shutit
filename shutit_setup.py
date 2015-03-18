"""
shutit.tk.setup (core ShutIt setup module)

Nomenclature:
    - Host machine: Machine on which this pexpect script is run.
    - Target:       Environment on which we deploy (docker container, ssh, or bash shell)
    - Container:    Docker container created to run the modules on.

    - target_child    pexpect-spawned child created to build on target
    - host_child      pexpect spawned child living on the host machine
"""

#The MIT License (MIT)
#
#Copyright (C) 2014 OpenBet Limited
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#ITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from shutit_module import ShutItModule
import pexpect
import sys
import os
import shutit_util
import time
import re
import subprocess
import os
from distutils import spawn


def conn_module():
	"""Connects ShutIt to something
	"""
	return [
		ConnDocker(
			'shutit.tk.conn_docker', -0.1,
			description='Connect ShutIt to docker'
		),
		ConnSSH(
			'shutit.tk.conn_ssh', -0.1,
			description='Connect ShutIt to a host via ssh'
		),
		ConnBash(
			'shutit.tk.conn_bash', -0.1,
			description='Connect ShutIt to a host via bash'
		),
	]


class setup(ShutItModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def build(self, shutit):
		"""Initializes target ready for build, setting password
		and updating package management.
		"""
		do_update = shutit.cfg[self.module_id]['do_update']
		shutit.send("touch ~/.bashrc")
		# Remvoe the 
		shutit.send("sed -i 's/.*HISTSIZE=[0-9]*$//' ~/.bashrc") 
		# eg centos doesn't have this
		if shutit.file_exists('/etc/bash.bashrc'):
			shutit.send("sed -i 's/.*HISTSIZE=[0-9]*$//' /etc/bash.bashrc") 
		shutit.send("sed -i 's/.*HISTSIZE=[0-9]*$//' /etc/profile") 
		shutit.add_to_bashrc('export HISTSIZE=99999999')
		# Ignore leading-space commands in the history.
		shutit.add_to_bashrc('export HISTCONTROL=ignorespace:cmdhist')
		shutit.add_to_bashrc('export LANG=' + shutit.cfg['target']['locale'])
		if shutit.cfg['target']['install_type'] == 'apt':
			shutit.add_to_bashrc('export DEBIAN_FRONTEND=noninteractive')
			if do_update:
				shutit.send('apt-get update', timeout=9999, check_exit=False)
			shutit.install('lsb-release')
			shutit.lsb_release()
			shutit.send('dpkg-divert --local --rename --add /sbin/initctl')
			shutit.send('ln -f -s /bin/true /sbin/initctl')
		elif shutit.cfg['target']['install_type'] == 'yum':
			if do_update:
				# yum updates are so often "bad" that we let exit codes of 1
				# through. TODO: make this more sophisticated
				shutit.send('yum update -y', timeout=9999, exit_values=['0', '1'])
		shutit.pause_point('Anything you want to do to the target host ' + 
			'before the build starts?', level=2)
		return True

	def remove(self, shutit):
		"""Removes anything performed as part of build.
		"""
		cfg = shutit.cfg
		return True

	def get_config(self, shutit):
		"""Gets the configured core pacakges, and whether to perform the package
		management update.
		"""
		shutit.get_config(self.module_id, 'do_update', True, boolean=True)
		return True


def module():
	return setup('shutit.tk.setup', 0.0, description='Core ShutIt setup')

