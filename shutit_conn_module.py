"""
Base class for connection modules.
"""


from shutit_module import ShutItModule


class ShutItConnModule(ShutItModule):

	def __init__(self, *args, **kwargs):
		super(ShutItConnModule, self).__init__(*args, **kwargs)

	def _setup_prompts(self, shutit, target_child):
		cfg = shutit.cfg
		# Now let's have a host_child
		shutit.log('Creating host child')
		shutit.log('Spawning host child')
		host_child = pexpect.spawn('/bin/bash')
		shutit.log('Spawning done')
		# Some pexpect settings
		shutit.pexpect_children['host_child'] = host_child
		shutit.pexpect_children['target_child'] = target_child
		shutit.log('Setting default expect')
		shutit.set_default_expect(cfg['expect_prompts']['base_prompt'])
		shutit.log('Setting default expect done')
		host_child.logfile_send = target_child.logfile_send = sys.stdout
		host_child.logfile_read = target_child.logfile_read = sys.stdout
		host_child.maxread = target_child.maxread = 2000
		host_child.searchwindowsize = target_child.searchwindowsize = 1024
		delay = cfg['build']['command_pause']
		host_child.delaybeforesend = target_child.delaybeforesend = delay
		# Set up prompts and let the user do things before the build
		# host child
		shutit.log('Setting default child')
		shutit.set_default_child(host_child)
		shutit.log('Setting default child done')
		shutit.log('Setting up default prompt on host child')
		shutit.log('Setting up prompt')
		shutit.setup_prompt('real_user_prompt', prefix='REAL_USER')
		shutit.log('Setting up prompt done')
		# target child
		shutit.set_default_child(target_child)
		shutit.log('Setting up default prompt on target child')
		shutit.setup_prompt('pre_build', prefix='PRE_BUILD')
		shutit.get_distro_info()
		shutit.setup_prompt('root_prompt', prefix='ROOT')

	def _add_begin_build_info(self, shutit, command):
		cfg = shutit.cfg
		# Create the build directory and put the config in it.
		shutit.send('mkdir -p ' + cfg['build']['build_db_dir'] + \
			 '/' + cfg['build']['build_id'])
		# Record the command we ran and the python env if in debug.
		if shutit.cfg['build']['debug']:
			shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
			    cfg['build']['build_id'] + '/python_env.sh', \
			    str(sys.__dict__), log=False)
			shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
			    cfg['build']['build_id'] + '/command.sh', \
			    ' '.join(command), log=False)
		shutit.pause_point('Anything you want to do now the ' +
		    'target is connected to?', level=2)

	def _add_end_build_info(self, shutit):
		cfg = shutit.cfg
		# Put build info into the target
		shutit.send('mkdir -p ' + cfg['build']['build_db_dir'] + '/' + \
		    cfg['build']['build_id'])
		shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
		    cfg['build']['build_id'] + '/build.log', \
		    shutit_util.get_commands(shutit))
		shutit.send_file(cfg['build']['build_db_dir'] + '/' + \
		    cfg['build']['build_id'] + '/build_commands.sh', \
		    shutit_util.get_commands(shutit))
		shutit.add_line_to_file(cfg['build']['build_id'], \
		    cfg['build']['build_db_dir'] + '/builds')
