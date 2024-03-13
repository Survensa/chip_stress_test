import time,sys,random,os
#TODO remove this reference
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

from matter_qa.library.base_test_cases.base_test_case import BaseTestCase
from matter_qa.library.helper_libs.exceptions import IterationError
from matter_qa.library.helper_libs.logger import log


class TC_Pair(BaseTestCase):
    # In case TC wants to overwrite
    def pre_iteration(self,iteration):
        if not self.iteration_log_created:
            self._create_iteration_log_file(iteration)
        log.info("I am test case pre-iteration")
        super().pre_iteration(iteration)
        log.info("I am in derived class pre-iteration ")
    # In case TC wants to overwrite
    def post_iteration(self):
        log.info("I am in derived class post-iteration ")
        # call this after TC Post iteration done, otherwise iteration log is closed.
        super().post_iteration()
    
    def end_of_test(self):
        log.info("I am in derived class end of test ")

    def pair_dut(self):
        log.info("I am in pairing")
        if not bool(random.getrandbits(1)):
            raise IterationError(custom_kwarg='')
        
    def unpair_dut(self):
        log.info("I am in unpairing")

    def test_tc_pair_unpair(self):

        @BaseTestCase.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        def pair_unpair_dut(*args,**kwargs):
            try:
                self.pair_dut()
                time.sleep(1)
                self.dut.factory_reset_dut(True)
                self.unpair_dut()
            # write specific exception here, if required.
            # otherwise control to the exception in base class.
            except IOError:
                log.info("An exception occurred")
        
        #core piece of the test case. 
        pair_unpair_dut(self)

    def run(self, **kwargs):
        super().start_test(**kwargs)
        self.test_tc_pair_unpair()

TC_Pair().run()