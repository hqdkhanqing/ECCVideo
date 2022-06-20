class GlobalVar: 
  ws_client = None 
  mq_client = None 
def set_ws_client(ws): 
  GlobalVar.ws_client = ws
def get_ws_client(): 
  return GlobalVar.ws_client 
def set_mq_client(mq_cli): 
  GlobalVar.mq_client = mq_cli 
def get_mq_client(): 
  return GlobalVar.mq_client 