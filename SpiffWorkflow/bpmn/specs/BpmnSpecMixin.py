from SpiffWorkflow.Task import Task
from SpiffWorkflow.operators import Operator
from SpiffWorkflow.specs.TaskSpec import TaskSpec

__author__ = 'matth'

class _BpmnCondition(Operator):

    def __init__(self, *args):
        if len(args) > 1:
            raise TypeError("Too many arguments")
        super(_BpmnCondition, self).__init__(*args)

    def _matches(self, task):
        return task.workflow.script_engine.evaluate(task, self.args[0])

class SequenceFlow(object):
    def __init__(self, id, name, task_spec):
        self.id = id
        self.name = name
        self.task_spec = task_spec

class BpmnSpecMixin(TaskSpec):


    def __init__(self, parent, name, lane=None, **kwargs):
        super(BpmnSpecMixin, self).__init__(parent, name, **kwargs)
        self.outgoing_sequence_flows = {}
        self.outgoing_sequence_flows_by_id = {}
        self.lane = lane

    def connect_outgoing(self, taskspec, sequence_flow_id, sequence_flow_name):
        self.connect(taskspec)
        s = SequenceFlow(sequence_flow_id, sequence_flow_name, taskspec)
        self.outgoing_sequence_flows[taskspec.name] = s
        self.outgoing_sequence_flows_by_id[sequence_flow_id] = s

    def connect_outgoing_if(self, condition, taskspec, sequence_flow_id, sequence_flow_name):
        self.connect_if(_BpmnCondition(condition), taskspec)
        s = SequenceFlow(sequence_flow_id, sequence_flow_name, taskspec)
        self.outgoing_sequence_flows[taskspec.name] = s
        self.outgoing_sequence_flows_by_id[sequence_flow_id] = s

    def get_outgoing_sequence_flow_by_spec(self, task_spec):
        return self.outgoing_sequence_flows[task_spec.name]

    def get_outgoing_sequence_flow_by_id(self, id):
        return self.outgoing_sequence_flows_by_id[id]

    def has_outgoing_sequence_flow(self, id):
        return id in self.outgoing_sequence_flows_by_id

    def get_outgoing_sequence_names(self):
        return sorted([s.name for s in self.outgoing_sequence_flows_by_id.itervalues()])

    def accept_message(self, my_task, message):
        return False

    ######### Hooks for Custom BPMN tasks ##########

    def entering_waiting_state(self, my_task):
        pass

    def entering_ready_state(self, my_task):
        pass

    def entering_complete_state(self, my_task):
        pass

    def entering_cancelled_state(self, my_task):
        pass

    ################################################

    def _on_complete_hook(self, my_task):
        super(BpmnSpecMixin, self)._on_complete_hook(my_task)
        if isinstance(my_task.parent.task_spec, BpmnSpecMixin):
            my_task.parent.task_spec._child_complete_hook(my_task)
        if not my_task.workflow._is_busy_with_restore():
            self.entering_complete_state(my_task)

    def _child_complete_hook(self, child_task):
        pass

    def _on_cancel(self, my_task):
        super(BpmnSpecMixin, self)._on_cancel(my_task)
        my_task.workflow._task_cancelled_notify(my_task)
        if not my_task.workflow._is_busy_with_restore():
            self.entering_cancelled_state(my_task)

    def _update_state_hook(self, my_task):
        prev_state = my_task.state
        super(BpmnSpecMixin, self)._update_state_hook(my_task)
        if prev_state != Task.WAITING and my_task.state == Task.WAITING and not my_task.workflow._is_busy_with_restore():
            self.entering_waiting_state(my_task)

    def _on_ready_before_hook(self, my_task):
        super(BpmnSpecMixin, self)._on_ready_before_hook(my_task)
        if not my_task.workflow._is_busy_with_restore():
            self.entering_ready_state(my_task)


