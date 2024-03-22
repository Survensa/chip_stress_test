import time,sys,random,os,logging,datetime
#TODO remove this reference
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import matter_qa.library.helper_libs.logger
from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.exceptions import IterationError
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main


log = logging.getLogger("tc_logger")

class TC_GeneralTestCase(MatterQABaseTestCaseClass):
    def __init__(self, *args) -> None:
        self.tc_name = "general_test_case"
        self.tc_id = "stress_1_1"
        super().__init__(*args)
    # In case TC wants to overwrite
    def pre_iteration(self,iteration):
        if not self.iteration_log_created:
            self._create_iteration_log_file(iteration)
        log.info("I am test case pre-iteration")
        super().pre_iteration(iteration)
        log.info("I am in derived class pre-iteration ")
    # In case TC wants to overwrite
    def post_iteration(self, *args):
        log.info("I am in derived class post-iteration ")
        # call this after TC Post iteration done, otherwise iteration log is closed.
        super().post_iteration(*args)
    
    def end_of_test(self, *args):
        log.info("I am in derived class end of test ")
        super().end_of_test(*args)

    def pair_dut(self):
        log.info("I am in pairing")
        if not bool(random.getrandbits(1)):
            raise IterationError(custom_kwarg='')
        if not bool(random.getrandbits(1)):
            try:
                r = 1/0
            except ZeroDivisionError as e:
                log.error(f"Failed to open the commissioning window :{str(e)}")
        
    def unpair_dut(self):
        date = datetime.datetime.now
        log.info("I am in unpairing %s",date)

    def test_tc_pair_unpair(self):
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        def pair_unpair_dut(*args,**kwargs):
            try:
                self.pair_dut()
                time.sleep(1)
                self.dut.factory_reset_dut()
                self.unpair_dut()
            # write specific exception here, if required.
            # otherwise control to the exception in base class.
            except IOError:
                log.info("An exception occurred")
        
        #core piece of the test case. 
        pair_unpair_dut(self)
"""
    def run(self, **kwargs):
        super().start_test(**kwargs)
        self.test_tc_pair_unpair()

TC_Pair().run()
"""

if __name__ == "__main__":
    #test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_GeneralTestCase,do_not_commision_first=True)