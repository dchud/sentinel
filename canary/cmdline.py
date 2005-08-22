import optparse
import os

class CommandLine:
    """A helper class for canary command line tools. When you use
    CommandLine you will get a --config option for free, and a handy
    method for instantiating a Context() object.

    cmdline = CommandLine()
    cmdline.parse_args()
    con = cmdline.context()
    """
    
    def __init__(self):
        self.parser = optparse.OptionParser('usage: %prog [options]')
        self.parser.add_option('-c', '--config', 
            dest='config', help='path to configuration file')
        self._ran = False

    def __getattr__(self,name):
        """To support attribute lookups.
        """
        if hasattr(self,name):
            return self.name
        elif hasattr(self.options,name):
            return getattr(self.options,name)
        else:
            raise AttributeError

    def add_option(self,*args,**kwargs):
        """Similar to OptionParser.add_option

        cmdline.add_option('-f', '--foo', help='foo bar')
        """
        self.parser.add_option(*args,**kwargs)

    def parse_args(self):
        """Similar to OptionParser.parse_args 

        options,args = cmdline.parse_args()
        """
        if not self._ran:
            self.options,self.args = self.parser.parse_args()
            self._ran = True
        return self.options, self.args

    def context(self):
        """After you've called parse_args() you should be able 
        to fetch a canary.context.Context object.

        context = cmdline.context()
        """
        if not self.options.config:
            self.guess_canary_config()

        from canary.context import CanaryConfig, Context
        config = CanaryConfig()
        config.read_file(self.options.config)
        return Context(config)

    def guess_canary_config(self):
        def find(arg,dname,fnames):
            if 'canary_config.py' in fnames:
                fnames = []
                self.options.config = dname + '/canary_config.py'
        os.path.walk(os.environ['HOME'],find,None)
        print "using canary config at %s" % self.options.config
        return self.options.config

