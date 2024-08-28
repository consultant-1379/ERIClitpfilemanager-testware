"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2018
@author:    Monika Penkova
@summary:   Dummy test to test pylint
"""
from litp_generic_test import GenericTest


class Dummy(GenericTest):
    """
    Dummy
    """

    def setUp(self):
        """Setup variables for every test"""
        # 1. Call super class setup
        super(Dummy, self).setUp()
        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filenames()[0]
        self.mn_nodes = self.get_managed_node_filenames()

    def tearDown(self):
        """Runs for every test"""
        super(Dummy, self).tearDown()

    def test_rhelv(self):
        """
        Dummy
        """
        self.log("info", "1.Check version of RHEL'")
        version = self.execute_cli_get_rhelver_from_node(self.ms_node)
        self.assertTrue("6.6" in version)
