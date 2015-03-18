"""
Connects ShutIt to a machine via ssh.

Assumes no docker daemon available for tagging and pushing.
"""

from shutit_conn_module import ShutItConnModule


class ConnSSH(ShutItConnModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'ssh_host', '')
		shutit.get_config(self.module_id, 'ssh_port', '')
		shutit.get_config(self.module_id, 'ssh_user', '')
		shutit.get_config(self.module_id, 'password', '')
		shutit.get_config(self.module_id, 'ssh_key', '')
		shutit.get_config(self.module_id, 'ssh_cmd', '')
		return True

	def build(self, shutit):
		"""Sets up the machine ready for building.
		"""
		cfg = shutit.cfg
		ssh_host = cfg[self.module_id]['ssh_host']
		ssh_port = cfg[self.module_id]['ssh_port']
		ssh_user = cfg[self.module_id]['ssh_user']
		ssh_pass = cfg[self.module_id]['password']
		ssh_key  = cfg[self.module_id]['ssh_key']
		ssh_cmd  = cfg[self.module_id]['ssh_cmd']
		opts = [
			'-t',
			'-o', 'UserKnownHostsFile=/dev/null',
			'-o', 'StrictHostKeyChecking=no'
		]
		if ssh_pass == '':
			opts += ['-o', 'PasswordAuthentication=no']
		if ssh_port != '':
			opts += ['-p', ssh_port]
		if ssh_key != '':
			opts += ['-i', ssh_key]
		host_arg = ssh_host
		if host_arg == '':
			shutit.fail('No host specified for sshing', throw_exception=False)
		if ssh_user != '':
			host_arg = ssh_user + '@' + host_arg
		cmd_arg = ssh_cmd
		if cmd_arg == '':
			cmd_arg = 'sudo su -s /bin/bash -'
		ssh_command = ['ssh'] + opts + [host_arg, cmd_arg]
		if cfg['build']['interactive'] >= 3:
			print('\n\nAbout to connect to host.' +
				'\n\n' + shutit_util.colour('32', '\n[Hit return to continue]'))
			shutit_util.util_raw_input(shutit=shutit)
		shutit.cfg['build']['ssh_command'] = ' '.join(ssh_command)
		shutit.log('\n\nCommand being run is:\n\n' + shutit.cfg['build']['ssh_command'],
			force_stdout=True, prefix=False)
		target_child = pexpect.spawn(ssh_command[0], ssh_command[1:])
		expect = ['assword', cfg['expect_prompts']['base_prompt'].strip()]
		res = target_child.expect(expect, 10)
		while True:
			shutit.log(target_child.before + target_child.after, prefix=False,
				force_stdout=True)
			if res == 0:
				shutit.log('...')
				res = shutit.send(ssh_pass,
				             child=target_child, expect=expect, timeout=10,
				             check_exit=False, fail_on_empty_before=False)
			elif res == 1:
				shutit.log('Prompt found, breaking out')
				break
		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, ssh_command)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')
		# Finish with the host
		shutit.set_default_child(shutit.pexpect_children['host_child'])
		# Final exits
		host_child.sendline('exit') # Exit raw bash
		return True
