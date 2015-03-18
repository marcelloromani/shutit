"""
Connects ShutIt to docker daemon and starts the container.
"""

from shutit_conn_module import ShutItConnModule


class ConnDocker(ShutItConnModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def _check_docker(self, shutit):
		"""Private function. Do some docker capability checking
		"""
		cfg = shutit.cfg

		# If we have sudo, kill any current sudo timeout. This is a bit of a
		# hammer and somewhat unfriendly, but tells us if we need a password.
		if spawn.find_executable('sudo') is not None:
			if subprocess.call(['sudo', '-k']) != 0:
				shutit.fail("Couldn't kill sudo timeout")

		# Check the executable is in the path. Not robust (as it could be sudo)
		# but deals with the common case of 'docker.io' being wrong.
		docker = cfg['host']['docker_executable'].split(' ')
		if spawn.find_executable(docker[0]) is None:
			msg = ('Didn\'t find %s on the path, what is the ' +\
			       'executable name (or full path) of docker?') % (docker[0],)
			cfg['host']['docker_executable'] = \
				shutit.prompt_cfg(msg, 'host', 'docker_executable')
			return False

		# First check we actually have docker and password (if needed) works
		check_cmd = docker + ['--version']
		str_cmd = ' '.join(check_cmd)
		cmd_timeout = 10
		needed_password = False
		fail_msg = ''
		try:
			shutit.log('Running: ' + str_cmd, force_stdout=True, prefix=False)
			child = pexpect.spawn(check_cmd[0], check_cmd[1:],
			timeout=cmd_timeout)
		except pexpect.ExceptionPexpect:
			msg = ('Failed to run %s (not sure why this has happened)...try ' +
			       'a different docker executable?') % (str_cmd,)
			cfg['host']['docker_executable'] = shutit.prompt_cfg(msg,
			    'host', 'docker_executable')
			return False
		try:
			if child.expect(['assword', pexpect.EOF]) == 0:
				needed_password = True
				if cfg['host']['password'] == '':
					msg = ('Running "%s" has prompted for a password, please ' +
					       'enter your host password') % (str_cmd,)
					cfg['host']['password'] = shutit.prompt_cfg(msg, 'host',
					    'password', ispass=True)
				child.sendline(cfg['host']['password'])
				child.expect(pexpect.EOF)
		except pexpect.ExceptionPexpect:
			fail_msg = '"%s" did not complete in %ss' % (str_cmd, cmd_timeout)
		child.close()
		if child.exitstatus != 0:
			fail_msg = '"%s" didn\'t return a 0 exit code' % (str_cmd,)

		if fail_msg:
			# TODO: Ideally here we'd split up our checks so if it asked for a
			# password, kill the sudo timeout and run `sudo -l`. We then know if
			# the password is right or not so we know what we need to prompt
			# for. At the moment we assume the password if it was asked for.
			if needed_password:
				msg = (fail_msg + ', your host password or ' +
				       'docker_executable config may be wrong (I will assume ' +
				       'password).\nPlease confirm your host password.')
				sec, name, ispass = 'host', 'password', True
			else:
				msg = (fail_msg + ', your docker_executable ' +
				       'setting seems to be wrong.\nPlease confirm your docker ' +
				       'executable, eg "sudo docker".')
				sec, name, ispass = 'host', 'docker_executable', False
			cfg[sec][name] = shutit.prompt_cfg(msg, sec, name, ispass=ispass)
			return False

		## Now check connectivity to the docker daemon
		#check_cmd = docker + ['info']
		#str_cmd = ' '.join(check_cmd)
		#child = pexpect.spawn(check_cmd[0], check_cmd[1:], timeout=cmd_timeout)
		#try:
		#	if child.expect(['assword', pexpect.EOF]) == 0:
		#		child.sendline(cfg['host']['password'])
		#		child.expect(pexpect.EOF)
		#except pexpect.ExceptionPexpect:
		#	shutit.fail('"' + str_cmd + '" did not complete in ' +
		#	str(cmd_timeout) + 's, ' +
		#	'is the docker daemon overloaded?')
		#child.close()
		#if child.exitstatus != 0:
		#	msg = ('"' + str_cmd + '" didn\'t return a 0 exit code, is the ' +
		#	       'docker daemon running? Do you need to set the ' +
		#	       'docker_executable config to use sudo? Please confirm the ' +
		#	       'docker executable.')
		#	cfg['host']['docker_executable'] = shutit.prompt_cfg(msg, 'host',
		#	    'docker_executable')

		return True

	def build(self, shutit):
		"""Sets up the target ready for building.
		"""
		# Uncomment for testing for "failure" cases.
		#sys.exit(1)
		while not self._check_docker(shutit):
			pass

		cfg = shutit.cfg
		docker = cfg['host']['docker_executable'].split(' ')

		# Always-required options
		if not os.path.exists('/tmp/shutit/cidfiles'):
			os.makedirs('/tmp/shutit/cidfiles')
		cfg['build']['cidfile'] = '/tmp/shutit/cidfiles' + cfg['host']['username'] +\
		    '_cidfile_' + cfg['build']['build_id']
		cidfile_arg = '--cidfile=' + cfg['build']['cidfile']

		# Singly-specified options
		privileged_arg = ''
		lxc_conf_arg   = ''
		name_arg       = ''
		hostname_arg   = ''
		volume_arg     = ''
		rm_arg         = ''
		net_arg        = ''
		if cfg['build']['privileged']:
			privileged_arg = '--privileged=true'
		else:
			# TODO: put in to ensure serve always works. --cap-add is now an option.
			# Need better solution in place, eg refresh builder when build
			# needs privileged
			if cfg['action']['serve']:
				privileged_arg = '--privileged=true'
		if cfg['build']['lxc_conf'] != '':
			lxc_conf_arg = '--lxc-conf=' + cfg['build']['lxc_conf']
		if cfg['target']['name'] != '':
			name_arg = '--name=' + cfg['target']['name']
		if cfg['target']['hostname'] != '':
			hostname_arg = '-h=' + cfg['target']['hostname']
		if cfg['host']['artifacts_dir'] != '':
			volume_arg = '-v=' + cfg['host']['artifacts_dir'] + ':/artifacts'
		if cfg['build']['net'] != '':
			net_arg        = '--net="' + cfg['build']['net'] + '"'
		# Incompatible with do_repository_work
		if cfg['target']['rm']:
			rm_arg = '--rm=true'

		# Multiply-specified options
		port_args  = []
		dns_args   = []
		ports_list = cfg['target']['ports'].strip().split()
		dns_list   = cfg['host']['dns'].strip().split()
		for portmap in ports_list:
			port_args.append('-p=' + portmap)
		for dns in dns_list:
			dns_args.append('--dns=' + dns)

		docker_command = docker + [
			arg for arg in [
				'run',
				cidfile_arg,
				privileged_arg,
				lxc_conf_arg,
				name_arg,
				hostname_arg,
				volume_arg,
				rm_arg,
				net_arg,
				] + port_args + dns_args + [
				'-t',
				'-i',
				cfg['target']['docker_image'],
				'/bin/bash'
			] if arg != ''
		]
		if cfg['build']['interactive'] >= 3:
			print('\n\nAbout to start container. ' +
			      'Ports mapped will be: ' + ', '.join(port_args) +
			      '\n\n[host]\nports:<value>\n\nconfig, building on the ' +
			      'configurable base image passed in in:\n\n    --image <image>\n' +
			      '\nor config:\n\n    [target]\n    docker_image:<image>)\n\n' +
			      'Base image in this case is:\n\n    ' + 
			      cfg['target']['docker_image'] +
			      '\n\n' + shutit_util.colour('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input(shutit=shutit)
		shutit.cfg['build']['docker_command'] = ' '.join(docker_command)
		shutit.log('\n\nCommand being run is:\n\n' + shutit.cfg['build']['docker_command'],
		force_stdout=True, prefix=False)
		shutit.log('\n\nThis may download the image, please be patient\n\n',
		force_stdout=True, prefix=False)

		target_child = pexpect.spawn(docker_command[0], docker_command[1:])
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip(), \
		          'Waiting', 'ulling', 'endpoint', 'Download']
		res = target_child.expect(expect, 9999)
		while True:
			shutit.log(target_child.before + target_child.after, prefix=False,
				force_stdout=True)
			if res == 0:
				shutit.log('...')
				res = shutit.send(cfg['host']['password'], \
				    child=target_child, expect=expect, timeout=9999, \
				    check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				shutit.log('Prompt found, breaking out')
				break
			else:
				res = target_child.expect(expect, 9999)
				continue
		# Get the cid
		time.sleep(1) # cidfile creation is sometimes slow...
		shutit.log('Slept')
		cid = open(cfg['build']['cidfile']).read()
		shutit.log('Opening file')
		if cid == '' or re.match('^[a-z0-9]+$', cid) == None:
			shutit.fail('Could not get container_id - quitting. ' +
			            'Check whether ' +
			            'other containers may be clashing on port allocation or name.' +
			            '\nYou might want to try running: sudo docker kill ' +
			            cfg['target']['name'] + '; sudo docker rm ' +
			            cfg['target']['name'] + '\nto resolve a name clash or: ' +
			            cfg['host']['docker_executable'] + ' ps -a | grep ' +
			            cfg['target']['ports'] + ' | awk \'{print $1}\' | ' +
			            'xargs ' + cfg['host']['docker_executable'] + ' kill\nto + '
			            'resolve a port clash\n')
		shutit.log('cid: ' + cid)
		cfg['target']['container_id'] = cid

		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, docker_command)

		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')

		cfg = shutit.cfg
		host_child = shutit.pexpect_children['host_child']
		shutit.set_default_child(host_child)
		shutit.set_default_expect(cfg['expect_prompts']['real_user_prompt'])
		# Tag and push etc
		shutit.pause_point('\nDoing final committing/tagging on the overall \
		                   target and creating the artifact.', \
		                   child=shutit.pexpect_children['host_child'], \
		                   print_input=False, level=3)
		shutit.do_repository_work(cfg['repository']['name'], \
		           docker_executable=cfg['host']['docker_executable'], \
		           password=cfg['host']['password'])
		# Final exits
		host_child.sendline('rm -f ' + cfg['build']['cidfile']) # Exit raw bash
		host_child.sendline('exit') # Exit raw bash
		return True

