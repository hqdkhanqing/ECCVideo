class GlobalVar: 
  forward_client = None 
  sub_client = None 
def set_forward_client(forward_client): 
  GlobalVar.forward_client = forward_client
def get_forward_client(): 
  return GlobalVar.forward_client 
def set_sub_client(sub_client): 
  GlobalVar.sub_client = sub_client 
def get_sub_client(): 
  return GlobalVar.sub_client 