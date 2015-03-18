"""
Connects ShutIt to a machine via bash.

Assumes no docker daemon available for tagging and pushing.
"""

from shutit_conn_module import ShutItConnModule


class ConnBash(ShutItConnModule):

	def is_installed(self, shutit):
		"""Always considered false for ShutIt setup.
		"""
		return False

	def get_config(self, shutit):
		return True

	def build(self, shutit):
		"""Sets up the machine ready for building.
		"""
		cfg = shutit.cfg
		command = '/bin/bash'
		target_child = pexpect.spawn(command)
		target_child.expect(cfg['expect_prompts']['base_prompt'].strip(), 10)
		self._setup_prompts(shutit, target_child)
		self._add_begin_build_info(shutit, command)
		return True

	def finalize(self, shutit):
		"""Finalizes the target, exiting for us back to the original shell
		and performing any repository work required.
		"""
		self._add_end_build_info(shutit)
		# Finish with the target
		shutit.pexpect_children['target_child'].sendline('exit')
		return True

