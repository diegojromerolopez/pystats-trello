
class TrelloBoardWorkflow(object):

    def __init__(self, name, list_name_order, done_list_name_order):
        self.name = name
        self.list_name_order = list_name_order
        self.done_list_names = done_list_name_order

        # Attributes that will need external initialization
        self.lists = None
        self.done_lists = None
        self.all_lists = None

    def init_lists(self, lists, done_lists):
        """
        Initializes all the lists of the configuration
        :param lists:
        :param done_lists:
        :return:
        """
        self.lists = lists
        self.done_lists = done_lists

        # We want to preserve the order of the lists
        self.all_lists = []
        all_lists_dict = {}
        for list_ in lists + done_lists:
            if list_.id not in all_lists_dict:
                all_lists_dict[list_.id] = list_
                self.all_lists.append(list_)
