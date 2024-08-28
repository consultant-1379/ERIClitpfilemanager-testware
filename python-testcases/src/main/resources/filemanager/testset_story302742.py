"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     November 2018
@author:    Karen Flannery
@summary:   TORF-302742
            As a LITP User, I want a new file plugin that gives the ability to
            change file permissions on specific executables in order to improve
            security vulnerabilities
"""

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
import test_constants


class Story302742(GenericTest):
    """
        As a LITP User, I want a new file plugin that gives the ability to
        change file permissions on specific executables in order to improve
        security vulnerabilities
    """

    def setUp(self):
        """
            Runs before every single test
        """

        super(Story302742, self).setUp()
        self.cli = CLIUtils()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nodes_list = [self.ms_node] + self.mn_nodes
        self.file_path = "/tmp/story302742_testfile_{0}.txt"
        self.managed_file_type = "managed-file"
        self.managed_file_name = "story302742_file{0}"
        self.infra_managed_file_path = self.find(self.ms_node,
                                                 "/infrastructure",
                                                 "collection-of-managed-file"
                                                 "-base")
        self.ms_managed_file_path = self.find(self.ms_node, "/ms",
                                              "ref-collection-of-managed-file"
                                              "-base")
        self.nodes_managed_file_path = self.find(
            self.ms_node, "/deployments", "ref-collection-of-managed-file-base"
        )
        self.duplicate_error = 'ValidationError    Create plan failed: ' \
                               'Managed-file "{0}" is duplicated on "{1}" in' \
                               ' locations: {2}, {3}'
        self.invalid_location_error = "InvalidLocationError    Not found"

    def tearDown(self):
        """
            Runs after every single test
        """
        super(Story302742, self).tearDown()

    def create_files_in_deployment(self, num):
        """
            Creates test files in the deployment

            Args:
                num (int): Number of files to create
        """
        for i in xrange(num):
            for node in self.nodes_list:
                self.create_file_on_node(node, self.file_path.format(i),
                                         ['test file content'])

    def create_managed_file(self, file_name, file_path, mode):
        """
            Creates a managed-file in the deployment

            Args:
                file_name (str): Name of managed-file in model
                file_path (str): Path to file in the deployment to be managed
                    by LITP
                mode (str): File permissions of the managed-file
        """
        self.execute_cli_create_cmd(self.ms_node, "{0}/{1}".format(
            self.infra_managed_file_path[0], file_name),
                                    self.managed_file_type,
                                    "path={0}".format(file_path),
                                    "mode={0}".format(mode))

    def inherit_managed_file_to_node(self, url, file_name):
        """
            Inherits managed-file to node

            Args:
                url (str): LITP path to create
                file_name (str): Name of managed-file in model
        """
        self.execute_cli_inherit_cmd(self.ms_node, "{0}/{1}".format(
            url, file_name), "{0}/{1}".format(self.infra_managed_file_path[0],
                                              file_name))

    def get_file_mode_on_node(self, node, file_path):
        """
            Returns the mode of a file in deployment

            Args:
                node (str): node cmd will be ran on
                file_path (str): Path to file on node
            Returns:
                 (str). mode of file in deployment

        """
        cmd = 'stat -c "%a %n" {0}'.format(file_path)
        mode_on_node, _, _ = self.run_command(node, cmd)
        mode = mode_on_node[0].split(" " + file_path)
        return mode

    def verify_file_permissions_on_ms(self, file_path, managed_file_name):
        """
            Gets mode of managed-file in model, gets mode of file in deployment
             and asserts that they are equal

            Args:
                file_path (str): Path to file on ms
                managed_file_name (str): Name of managed-file in the model
        """
        mode = self.get_file_mode_on_node(self.ms_node, file_path)
        mode_on_model = self.get_props_from_url(
            self.ms_node, "{0}/{1}".format(self.ms_managed_file_path[0],
                                           managed_file_name),
            filter_prop="mode")
        self.assertEqual(mode_on_model, mode[0],
                         "Difference between mode on the ms({0}) "
                         "and model({1})".format(mode[0], mode_on_model))

    @attr('all', 'revert', 'story302742', 'story302742_tc03')
    def test_01_p_multiple_managed_files(self):
        """
            @tms_id: torf_302742_tc03
            @tms_requirements_id: TORF-302742
            @tms_title: Create multiple managed-files
            @tms_description: Create multiple managed-files and inherit to ms
                and peer nodes. Create and run plan. Verify file permissions
                are updated to those specified in the model.
            @tms_test_steps:
             @step: Create test files in deployment
             @result: Test files are created
             @step: Create multiple managed files in model and inherit to ms
                 and nodes. Create and run plan.
             @result: Plan ran successfully. Multiple managed-files are created
                 in the model and inherited to ms and nodes
             @step: Verify file permissions in deployment match those in the
                 model
             @result: File permissions are the same between model and
                 deployment
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        num_of_files = 12
        mode = "666"
        self.log("info", "#1. Create test files in deployment")
        self.create_files_in_deployment(num_of_files)

        self.log("info", "#2. Create multiple managed files in model and "
                         "inherit to ms and nodes")
        for i in xrange(num_of_files):
            self.create_managed_file(self.managed_file_name.format(i),
                                     self.file_path.format(i), mode)

            node_paths = [self.ms_managed_file_path[0],
                          self.nodes_managed_file_path[1],
                          self.nodes_managed_file_path[2]]

            for path in node_paths:
                self.inherit_managed_file_to_node(path, self.managed_file_name
                                                  .format(i))

        self.log("info", "#3. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#4. File permissions are the same between model and "
                         "deployment")
        for node in self.nodes_list:
            for i in xrange(num_of_files):
                self.assertEqual(self.get_file_mode_on_node(
                    node, self.file_path.format(i))[0], mode,
                        "Difference between mode in model and deployment")

    @attr('all', 'revert', 'story302742',
          'story302742_tc04, story302742_tc05, story302742_tc06, '
          'story302742_tc09')
    def test_02_p_update_managed_file_permissions_persisted_remove(self):
        """
            @tms_id: torf_302742_tc04, torf_302742_tc05, torf_302742_tc06,
                torf_302742_tc09
            @tms_requirements_id: TORF-302742
            @tms_title: Update/File Permissions Persisted/Remove managed-file
            @tms_description: Update the file path of an existing managed-file.
                Change file permissions on the file in the deployment. Wait for
                 puppet run and verify file permissions are restored to those
                 set in the model. Remove managed-file.
            @tms_test_steps:
             @step: Create test files in deployment
             @result: Test files are created
             @step: Create managed-file in model and inherit to ms, create and
                 run plan.
             @result: Plan ran successfully. Managed-file is created in the
                 model and inherited to ms
             @step: Update file path in model. Create and run plan.
             @result: Plan ran successfully. File path is updated in model
             @step: Change file permissions on file in deployment. Start and
                 wait for puppet run and verify that the file permissions are
                 restored to those specified in the model.
             @result: File permissions are restored to those specified in the
                 model.
             @step: Remove managed-file. Create and run plan.
             @result: Plan ran successfully. Managed-file is removed.
             @step: Execute show cmd to verify that the managed-file has been
                 removed
             @result: managed-file is no longer present
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create test files in deployment")
        self.create_files_in_deployment(2)

        self.log("info", "#2. Create managed file in model")
        self.create_managed_file(self.managed_file_name.format("A"),
                                 self.file_path.format(0), "755")

        self.log("info", "#3. Inherit to ms")
        self.inherit_managed_file_to_node(self.ms_managed_file_path[0],
                                          self.managed_file_name.format("A"))

        self.log("info", "#4. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#5. Update path")
        self.execute_cli_update_cmd(self.ms_node, "{0}/{1}".format(
            self.infra_managed_file_path[0], self.managed_file_name.format("A")
        ), "path={0}".format(self.file_path.format(1)))

        self.log("info", "#6. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#7. Change permissions on file in deployment")
        cmd = 'chmod 666 {0}'.format(self.file_path.format(1))
        self.run_command(self.ms_node, cmd)

        self.log("info", "#8. Start and wait for puppet run")
        self.start_new_puppet_run(self.ms_node)
        self.wait_full_puppet_run(self.ms_node)

        self.log("info", "#9. Verify permissions are equal in model and"
                         " deployment")
        self.verify_file_permissions_on_ms(self.file_path.format(1),
                                           self.managed_file_name.format("A"))

        self.log("info", "#10. Remove managed-file")
        self.execute_cli_remove_cmd(self.ms_node, "{0}/{1}".format(
            self.infra_managed_file_path[0], self.managed_file_name.format("A")
        ))
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#11. Verify managed-file is no longer present")
        _, show_cmd_error, _ = self.execute_cli_show_cmd(
            self.ms_node, "{0}/{1}".format(self.infra_managed_file_path[0],
                self.managed_file_name.format("A")), expect_positive=False)
        self.assertEqual(show_cmd_error[1], self.invalid_location_error,
                         "Managed-file was not removed")

    @attr('all', 'revert', 'story302742', 'story302742_tc15')
    def test_03_p_mode_handles_3_digits(self):
        """
            @tms_id: torf_302742_tc15
            @tms_requirements_id: TORF-302742
            @tms_title: Mode handles 3 digits
            @tms_description: Mode can be in 3 or 4 digits. This test is to
                verify 0755 is handled the same as 755.
            @tms_test_steps:
             @step: Create test files in deployment
             @result: Test files are created
             @step: Create 2 managed-files in model, one with mode=755 and the
                 other with mode=0755, inherit to ms. Create and run plan.
             @result: Plan ran successfully. 2 managed-files are created in
                 the model with the same mode.
             @step: Verify file permissions on both files in deployment are
                 the same.
             @result: File permissions on both files are the same.
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create test files in deployment")
        self.create_files_in_deployment(2)

        self.log("info", "#2. Create 2 managed files in model with mode=755 "
                         "and mode=0755")
        file_details = {0: ["A", "755"], 1: ["B", "0755"]}
        for file_no, filedetails in file_details.iteritems():
            self.create_managed_file(self.managed_file_name.format
                (filedetails[0]), self.file_path.format(file_no),
                                     filedetails[1])

        for filedetails in file_details.itervalues():
            self.inherit_managed_file_to_node(self.ms_managed_file_path[0],
                                              self.managed_file_name.format
                                              (filedetails[0]))

        self.log("info", "#3. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#4. verify that both files have the same "
                         "permissions on the ms")
        self.assertEqual(
            self.get_file_mode_on_node(self.ms_node,
                                       self.file_path.format("0"))[0],
            self.get_file_mode_on_node(self.ms_node,
                                       self.file_path.format("1"))[0],
            "mode1 is not the same as mode2")

    @attr('all', 'revert', 'story302742', 'story302742_tc10')
    def test_04_n_fail_plan_recreate(self):
        """
            @tms_id: torf_302742_tc10
            @tms_requirements_id: TORF-302742
            @tms_title: Plan fails when file does not exist
            @tms_description: Test to verify that the plan fails when a
                managed-file is created in the model that does not exist in the
                 deployment. Also verifies that once the file exists, recreate
                 and run plan succeeds.
            @tms_test_steps:
             @step: Create managed-file in model and inherit to ms, create and
                 run plan expecting the plan to fail as file does not exist in
                 the deployment
             @result: Plan fails.
             @step: Create test file in deployment
             @result: Test file is created
             @step: Recreate and run plan.
             @result: Plan ran successfully. Managed-file is created
                 in the model and inherited to ms.
             @step: Verify file permissions in deployment match those in the
                 model
             @result: File permissions are the same between model and
                 deployment
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create managed file in model")
        self.create_managed_file(self.managed_file_name.format("A"),
                                 self.file_path.format(0), "644")

        self.log("info", "#2. Inherit to ms")
        self.inherit_managed_file_to_node(self.ms_managed_file_path[0],
                                          self.managed_file_name.format
                                          ("A"))

        self.log("info", "#3. Run plan expecting it to fail")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_FAILED, 5)

        self.create_files_in_deployment(1)
        self.log("info", "#4. Recreate and run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE,
                                plan_timeout_mins=5)

        self.log("info", "#5. Verify file permissions are the same in "
                         "deployment as model")
        self.verify_file_permissions_on_ms(self.file_path.format(0),
                                           self.managed_file_name.format
                                           ("A"))

    @attr('all', 'revert', 'story302742', 'story302742_tc11')
    def test_05_n_fail_plan_resume(self):
        """
            @tms_id: torf_302742_tc11
            @tms_requirements_id: TORF-302742
            @tms_title: Resume plan succeeds when the cause of a failed task
                        is fixed
            @tms_description: Test to verify that the plan fails when a
                managed-file is created in the model that does not exist in the
                 deployment. Also verifies that once the file exists,
                 "run_plan --resume" succeeds.
            @tms_test_steps:
             @step: Create managed-file in model and inherit to ms, create and
                 run plan expecting the plan to fail as file does not exist in
                 the deployment
             @result: Plan fails.
             @step: Create test file in deployment
             @result: Test file is created
             @step: Execute run_plan --resume.
             @result: Plan resumes and runs successfully. Managed-file is
                 created in the model and inherited to ms.
             @step: Verify file permissions in deployment match those in the
                 model
             @result: File permissions are the same between model and
                 deployment
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create managed file in model")
        self.create_managed_file(self.managed_file_name.format("A"),
                                 self.file_path.format(0), "777")

        self.log("info", "#2. Inherit to ms")
        self.inherit_managed_file_to_node(self.ms_managed_file_path[0],
                                          self.managed_file_name.format
                                          ("A"))

        self.log("info", "#3. Run plan expecting it to fail")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_FAILED, 5)

        self.log("info", "#4. Create file in deployment")
        self.create_files_in_deployment(1)

        self.log("info", "#5. Execute litp run_plan --resume")
        self.run_command(self.ms_node, self.cli.get_run_plan_cmd(
            args="--resume"))
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_COMPLETE),
                        "Plan did not complete successfully")

        self.log("info", "#6. Verify file permissions are the same in "
                         "deployment as model")
        self.verify_file_permissions_on_ms(self.file_path.format(0),
                                           self.managed_file_name.format
                                           ("A"))

    @attr('all', 'revert', 'story302742', 'story302742_tc16')
    def test_06_p_node_supersedes_cluster(self):
        """
            @tms_id: torf_302742_tc16
            @tms_requirements_id: TORF-302742
            @tms_title: Node level permissions supersede those set at cluster
                 level
            @tms_description: Test to verify file permissions specified at node
                 level supersede those set at cluster level
            @tms_test_steps:
             @step: Create test file in deployment
             @result: Test file is created
             @step: Create 2 managed files in model with the same file path
                 and different modes, inherit one to cluster level and the
                 other to node1. Create and run plan.
             @result: Plan ran successfully. 2 managed-files are created in the
                 model, with one inherited to cluster level and the other to
                 node1.
             @step: Verify file permissions on node1 are those specified in the
                 model at node level and on node2 are those at cluster level
             @result: File permissions on node1 are those specified in the
                 model at node level and on node2 are those at cluster level
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create test file in deployment")
        self.create_files_in_deployment(1)

        self.log("info", "#2. Create 2 managed files in model with the same "
                         "file path and different modes. Inherit file0 to "
                         "cluster level and file1 to node1")
        file_details = {0: "755", 1: "666"}
        for filename, mode in file_details.iteritems():
            self.create_managed_file(self.managed_file_name.format(filename),
                                     self.file_path.format(0), mode)

        for i in file_details.iterkeys():
            self.inherit_managed_file_to_node(self.nodes_managed_file_path[i],
                                              self.managed_file_name.format(i))

        self.log("info", "#3. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#4. Verify that the node file permissions supersede "
                         "the cluster.")
        self.assertEqual(self.get_file_mode_on_node(
            self.mn_nodes[0], self.file_path.format(0))[0],
                         file_details.values()[1],
                         "Mode on node1 is not as expected (666)")
        self.assertEqual(self.get_file_mode_on_node(
            self.mn_nodes[1], self.file_path.format(0))[0],
                         file_details.values()[0],
                         "Mode on node2 is not as expected (755)")

    @attr('all', 'revert', 'story302742', 'story302742_tc17')
    def test_07_p_path_must_be_unique_on_each_node(self):
        """
            @tms_id: torf_302742_tc17
            @tms_requirements_id: TORF-302742
            @tms_title: File path must be unique on each node
            @tms_description: Test to verify that file path must be unique on
                each node
            @tms_test_steps:
             @step: Create test file in deployment
             @result: Test file is created
             @step: Create 2 managed-files in the deployment both with the same
                  file path. Inherit to ms. Create plan expecting it to fail
                  with ValidationError.
             @result: Plan fails with ValidationError
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        self.log("info", "#1. Create test file in deployment")
        self.create_files_in_deployment(1)

        self.log("info", "#2. Create managed file in model and inherit to ms")
        file_details = {"A": "755", "B": "644"}
        for filename, mode in file_details.iteritems():
            self.create_managed_file(self.managed_file_name.format(filename),
                                     self.file_path.format(0), mode)

        for filename in file_details.keys():
            self.inherit_managed_file_to_node(self.ms_managed_file_path[0],
                                              self.managed_file_name.format(
                                                  filename))

        self.log("info", "#3. create_plan expecting to fail")
        _, create_plan_err, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)

        self.log("info", "#4. Verifies ValidationError")
        self.assertEqual(create_plan_err[0], self.duplicate_error.format(
            self.file_path.format(0), self.ms_node, "{0}/{1}".format(
                self.ms_managed_file_path[0], self.managed_file_name.format
                ("A")), "{0}/{1}".format(
                self.ms_managed_file_path[0], self.managed_file_name.format
                ("B"))), "ValidationError was not as expected")

    @attr('all', 'revert', 'story302742', 'story302742_tc18')
    def test_08_p_managed_file_list(self):
        """
            @tms_id: torf_302742_tc18
            @tms_requirements_id: TORF-302742
            @tms_title: Create managed-file-list
            @tms_description: Test to verify that you can create a
                managed-file-list.
            @tms_test_steps:
             @step: Create test files in deployment
             @result: Test files are created
             @step: Create managed-file-list with 3 managed-files.
                 Inherit to ms, cluster level and node1. Create and run plan.
             @result: Plan ran successfully. Managed-files are created on ms
                 and nodes.
             @step: Verify file permissions are updated to those specified in
                 the model.
             @result: File permissions in the deployment are the same as those
                specified in the model
            @tms_test_precondition: NA
            @tms_execution_type: Automated
        """

        managed_list_type = "managed-file-list"
        managed_file_list = "managed_file_list"
        managed_list_name = "story302742_managed_file_list"

        self.log("info", "#1. Create test files in deployment")
        self.create_files_in_deployment(3)

        self.log("info", "#2. Create a managed-file-list with 3 managed-files")
        self.execute_cli_create_cmd(self.ms_node, "{0}/{1}".format(
            self.infra_managed_file_path[0], managed_list_name),
                                    managed_list_type)

        infra_managed_list_path = self.find(self.ms_node, "/infrastructure",
                                            "managed-file-list")
        url = "{0}/{1}/{2}".format(infra_managed_list_path[0],
                                   managed_file_list, self.managed_file_name.
                                   format("{0}"))
        property_path = "path={0}".format(self.file_path.format("{0}"))
        property_mode = "mode={0}"

        file_details = {0: "755", 1: "666", 2: "644"}
        for file_no, mode in file_details.iteritems():
            self.execute_cli_create_cmd(self.ms_node, url.format(file_no),
                self.managed_file_type, property_path.format(file_no),
                                        property_mode.format(mode))

        self.log("info", "#3. Inherit managed-list to ms, cluster and node1")
        for node in self.ms_managed_file_path + self.nodes_managed_file_path:
            self.inherit_managed_file_to_node(node, managed_list_name)

        self.log("info", "#4. Run plan successfully")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 5)

        self.log("info", "#5. Verify permissions on ms and peer nodes")
        for node in self.nodes_list:
            for file_no, mode in file_details.iteritems():
                self.assertEqual(self.get_file_mode_on_node(
                    node, self.file_path.format(file_no))[0], mode,
                        "Difference between mode in model and deployment")
