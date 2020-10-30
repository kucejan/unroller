
import os

import subprocess

from mininet.cli import CLI
from appcontroller import AppController
from appprocrunner import AppProcRunner, AppProcess

CONSOLE = 'bash'
SWITCH_CLI = 'simple_switch_CLI'

# List of switch IDs visited before the loop
UNROLLER_B = [1]

# List of switch IDs making the loop
UNROLLER_L = [6, 3, 2, 7]

# The threshold for reporting a loop
UNROLLER_TH = 1

class CustomAppController(AppController):

    def __init__(self, *args, **kwargs):
        AppController.__init__(self, *args, **kwargs)

    def generateDefaultCommands(self):
        pass

    def writeRegister(self, register, idx, value, thrift_port=9090, sw=None):
        if sw: thrift_port = sw.thrift_port
        p = subprocess.Popen([self.cli_path, '--thrift-port', str(thrift_port)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input="register_write %s %d %d" % (register, idx, value))

    def nexthopSwitch(self, swid):
        self.writeRegister("cfg_swid_reg", 0, swid)
        self.writeRegister("cfg_thcnt_reg", 0, UNROLLER_TH)

        host = self.net.get('h1')
        generator = host.popen('./tools/packet_generator.py')
        retval = generator.wait()
        stdout, stderr = generator.communicate()
        print stdout, #stderr,
        print

        return retval == 0

    def stop(self):
        AppController.stop(self)

        container = os.environ['HOSTNAME']

        print 'To open the container console run:'
        print '  docker exec -t -i %s %s' % (container, CONSOLE)
        print

        print 'To open the switch CLI run:'
        print '  docker exec -t -i %s %s' % (container, SWITCH_CLI)
        print

        controller = subprocess.Popen('/tmp/tools/digest_client.py')

        while len(UNROLLER_B) > 0:
            retval = self.nexthopSwitch(UNROLLER_B[0])
            if not retval: break
            UNROLLER_B.pop(0)

        in_loop_hop = 0
        while len(UNROLLER_B) == 0 and len(UNROLLER_L) > 0:
            retval = self.nexthopSwitch(UNROLLER_L[in_loop_hop % len(UNROLLER_L)])
            if not retval: break
            in_loop_hop += 1

        controller.terminate()
        print

        #CLI(self.net)
        #print

class CustomAppProcRunner(AppProcRunner):

    def __init__(self, *args, **kwargs):
        AppProcRunner.__init__(self, *args, **kwargs)

    def startAllProcs(self):
        AppProcRunner.startAllProcs(self)
