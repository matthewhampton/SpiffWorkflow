__author__ = 'matth'

class GlobalTaskParser(object):

    def __init__(self, parser, node, filename=None):
        self.parser = parser
        self.node = node
        self.filename = filename

    def get_id(self):
        """
        Returns the process ID
        """
        return self.node.get('id')

    def get_name(self):
        """
        Returns the process name (or ID, if no name is included in the file)
        """
        return self.node.get('name', default=self.get_id())

    def parse_node(self):
        """
        Parse any extension elements
        """