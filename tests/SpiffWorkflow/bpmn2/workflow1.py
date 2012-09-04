import os
import unittest
from SpiffWorkflow.Task import Task
from SpiffWorkflow.bpmn2.Bpmn2Loader import Parser
from SpiffWorkflow.bpmn2.BpmnWorkflow import BpmnWorkflow

__author__ = 'matth'


class WorkflowTest(unittest.TestCase):

    def load_workflow_spec(self, filename, process_name):
        f = os.path.join(os.path.dirname(__file__), 'data', filename)
        p = Parser()
        p.add_bpmn_files_by_glob(f)
        return p.get_spec(process_name)

    def do_next_exclusive_step(self, step_name, with_save_load=False, set_attribs=None, choice=None):
        if with_save_load:
            self.save_restore()

        self.workflow.do_engine_steps()
        tasks = self.workflow.get_tasks(Task.READY)
        self._do_single_step(step_name, tasks, set_attribs, choice)

    def do_next_named_step(self, step_name, with_save_load=False, set_attribs=None, choice=None):
        if with_save_load:
            self.save_restore()

        self.workflow.do_engine_steps()
        tasks = filter(lambda t: t.task_spec.name == step_name or t.task_spec.description == step_name, self.workflow.get_tasks(Task.READY))
        self._do_single_step(step_name, tasks, set_attribs, choice)

    def assertTaskNotReady(self, step_name):
        tasks = filter(lambda t: t.task_spec.name == step_name or t.task_spec.description == step_name, self.workflow.get_tasks(Task.READY))
        self.assertEquals([], tasks)

    def _do_single_step(self, step_name, tasks, set_attribs=None, choice=None):

        self.assertEqual(len(tasks), 1)

        self.assertTrue(tasks[0].task_spec.name == step_name or tasks[0].task_spec.description == step_name,
            'Expected step %s, got %s (%s)' % (step_name, tasks[0].task_spec.description, tasks[0].task_spec.name))
        if not set_attribs:
            set_attribs = {}

        if choice:
            set_attribs['choice'] = choice

        if set_attribs:
            tasks[0].set_attribute(**set_attribs)
        tasks[0].complete()

    def save_restore(self):
        state = self.workflow.get_workflow_state()
        self.restore(state)

    def restore(self, state):
        self.workflow = BpmnWorkflow(self.spec)
        self.workflow.restore_workflow_state(state)


class Workflow1Test(WorkflowTest):
    def setUp(self):
        self.spec = self.load_workflow1_spec()

    def load_workflow1_spec(self):
        return self.load_workflow_spec('workflow1.bpmn', 'MOC')

    def testRunThroughHappy(self):

        self.workflow = BpmnWorkflow(self.spec)
        self.do_next_exclusive_step('Stage_1.Prepare_MOC_Proposal')
        self.do_next_exclusive_step('Stage_1.Review', set_attribs={'choice': 'Approve'})
        self.do_next_exclusive_step('Stage_1.Record_on_MOC_agenda')
        self.do_next_exclusive_step('Stage_2.Register_MOC_Proposal_Form')
        self.do_next_exclusive_step('Stage_2.Proposal_Form_Review', set_attribs={'choice': 'Approve'})

    def testSaveRestore(self):

        self.workflow = BpmnWorkflow(self.spec)

        self.save_restore()

        self.do_next_exclusive_step('Stage_1.Prepare_MOC_Proposal')

        self.save_restore()

        self.do_next_exclusive_step('Stage_1.Review', set_attribs={'choice': 'Approve'})
        self.save_restore()
        self.do_next_exclusive_step('Stage_1.Record_on_MOC_agenda')
        self.save_restore()

        self.do_next_exclusive_step('Stage_2.Register_MOC_Proposal_Form')
        self.save_restore()

        self.do_next_exclusive_step('Stage_2.Proposal_Form_Review', set_attribs={'choice': 'Approve'})

        self.save_restore()


class ApprovalsTest(WorkflowTest):
    def setUp(self):
        self.spec = self.load_workflow1_spec()

    def load_workflow1_spec(self):
        #Start (StartTask:0xb6b4204cL)
        #   --> Approvals.First_Approval_Wins (CallActivity)
        #          --> Start (StartTask:0xb6b4266cL)
        #          |      --> First_Approval_Wins.Supervisor_Approval (ManualTask)
        #          |      |      --> First_Approval_Wins.Supervisor_Approved (EndEvent)
        #          |      |             --> First_Approval_Wins.EndJoin (EndJoin)
        #          |      |                    --> End (Simple)
        #          |      --> First_Approval_Wins.Manager_Approval (ManualTask)
        #          |             --> First_Approval_Wins.Manager_Approved (EndEvent)
        #          |                    --> [shown earlier] First_Approval_Wins.EndJoin (EndJoin)
        #          --> Approvals.First_Approval_Wins_Done (ManualTask)
        #                 --> Approvals.Gateway4 (ParallelGateway)
        #                        --> Approvals.Manager_Approval__P_ (ManualTask)
        #                        |      --> Approvals.Gateway5 (ParallelGateway)
        #                        |             --> Approvals.Parallel_Approvals_Done (ManualTask)
        #                        |                    --> Approvals.Parallel_SP (CallActivity)
        #                        |                           --> Start (StartTask)
        #                        |                           |      --> Parallel_Approvals_SP.Step1 (ManualTask)
        #                        |                           |      |      --> Parallel_Approvals_SP.Supervisor_Approval (ManualTask)
        #                        |                           |      |             --> Parallel_Approvals_SP.End2 (EndEvent)
        #                        |                           |      |                    --> Parallel_Approvals_SP.EndJoin (EndJoin)
        #                        |                           |      |                           --> End (Simple)
        #                        |                           |      --> Parallel_Approvals_SP.Manager_Approval (ManualTask)
        #                        |                           |             --> [shown earlier] Parallel_Approvals_SP.End2 (EndEvent)
        #                        |                           --> Approvals.Parallel_SP_Done (ManualTask)
        #                        |                                  --> Approvals.End1 (EndEvent)
        #                        |                                         --> Approvals.EndJoin (EndJoin)
        #                        |                                                --> End (Simple)
        #                        --> Approvals.Supervisor_Approval__P_ (ManualTask)
        #                               --> [shown earlier] Approvals.Gateway5 (ParallelGateway)
        return self.load_workflow_spec('Approvals.bpmn', 'Approvals')

    def testRunThroughHappy(self):

        self.workflow = BpmnWorkflow(self.spec)

        self.do_next_named_step('First_Approval_Wins.Manager_Approval')
        self.do_next_exclusive_step('Approvals.First_Approval_Wins_Done')

        self.do_next_named_step('Approvals.Manager_Approval__P_')
        self.do_next_named_step('Approvals.Supervisor_Approval__P_')
        self.do_next_exclusive_step('Approvals.Parallel_Approvals_Done')

        self.do_next_named_step('Parallel_Approvals_SP.Step1')
        self.do_next_named_step('Parallel_Approvals_SP.Manager_Approval')
        self.do_next_named_step('Parallel_Approvals_SP.Supervisor_Approval')
        self.do_next_exclusive_step('Approvals.Parallel_SP_Done')

    def testRunThroughHappyOtherOrders(self):

        self.workflow = BpmnWorkflow(self.spec)

        self.do_next_named_step('First_Approval_Wins.Supervisor_Approval')
        self.do_next_exclusive_step('Approvals.First_Approval_Wins_Done')

        self.do_next_named_step('Approvals.Supervisor_Approval__P_')
        self.do_next_named_step('Approvals.Manager_Approval__P_')
        self.do_next_exclusive_step('Approvals.Parallel_Approvals_Done')

        self.do_next_named_step('Parallel_Approvals_SP.Manager_Approval')
        self.do_next_named_step('Parallel_Approvals_SP.Step1')
        self.do_next_named_step('Parallel_Approvals_SP.Supervisor_Approval')
        self.do_next_exclusive_step('Approvals.Parallel_SP_Done')

    def testSaveRestore(self):

        self.workflow = BpmnWorkflow(self.spec)

        self.do_next_named_step('First_Approval_Wins.Manager_Approval')
        self.save_restore()
        self.do_next_exclusive_step('Approvals.First_Approval_Wins_Done')

        self.save_restore()
        self.do_next_named_step('Approvals.Supervisor_Approval__P_')
        self.do_next_named_step('Approvals.Manager_Approval__P_')
        self.do_next_exclusive_step('Approvals.Parallel_Approvals_Done')

        self.save_restore()
        self.do_next_named_step('Parallel_Approvals_SP.Manager_Approval')
        self.do_next_exclusive_step('Parallel_Approvals_SP.Step1')
        self.do_next_exclusive_step('Parallel_Approvals_SP.Supervisor_Approval')
        self.do_next_exclusive_step('Approvals.Parallel_SP_Done')


    def testSaveRestoreWaiting(self):

        self.workflow = BpmnWorkflow(self.spec)

        self.do_next_named_step('First_Approval_Wins.Manager_Approval')
        self.save_restore()
        self.do_next_exclusive_step('Approvals.First_Approval_Wins_Done')

        self.save_restore()
        self.do_next_named_step('Approvals.Supervisor_Approval__P_')
        self.save_restore()
        self.do_next_named_step('Approvals.Manager_Approval__P_')
        self.save_restore()
        self.do_next_exclusive_step('Approvals.Parallel_Approvals_Done')

        self.save_restore()
        self.do_next_named_step('Parallel_Approvals_SP.Manager_Approval')
        self.save_restore()
        self.do_next_exclusive_step('Parallel_Approvals_SP.Step1')
        self.save_restore()
        self.do_next_exclusive_step('Parallel_Approvals_SP.Supervisor_Approval')
        self.save_restore()
        self.do_next_exclusive_step('Approvals.Parallel_SP_Done')



def suite():
    return unittest.TestLoader().loadTestsFromTestCase(Workflow1Test)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())