
from direct import direct_func
from label import label_func

class orchestration(object):
    def __init__(self, orchestrating_data):
        self.orchestrating_data = orchestrating_data
        func_dict = {"direct": self.direct, "label": self.label, "other": self.other_func}
        self.orchestrate_func = func_dict.get(self.orchestrating_data['map_info']['policy'], self.func_None)
    
    def direct(self):
        print('aaaa')
        return direct_func(self.orchestrating_data['logical_topology'],self.orchestrating_data['map_info'],self.orchestrating_data['label_agent'])
 
    def label(self):
        return label_func(self.orchestrating_data['logical_topology'], self.orchestrating_data['map_info'], self.orchestrating_data['label_agent'])
    
    def other_func(self):
        print('Other orchestration function to be developed')

    def func_None(self):
        print('Orchestration of this policy is not supported')
    
    
    
