import ruamel.yaml
from ruamel.yaml.comments import CommentedMap      # CommentedMap用于解决ordereddict数据dump时带"!omap"这样的字段
from ruamel.yaml.scalarstring import SingleQuotedScalarString,DoubleQuotedScalarString
import re

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=4, sequence=6, offset=4)

import json

def compose_encapsulate(app_id, yml):
    compose_yml = json.loads(yml)
    print("compose_yml=",compose_yml)
    print(type(compose_yml))
    services = compose_yml['services']
    local_container = list(services.keys())
    for service_name in local_container:
        container_type = services[service_name].pop("type")
        container_env = services[service_name]['environment']
        container_env.update({"ECCI_APP_ID":app_id})
        container_name = re.findall(r"^edgeai_.*?_(.*)",service_name)[0]
        container_env.update({"ECCI_CONTAINER_NAME":container_name})
        container_env.update({"ECCI_LOCAL_CONTAINERS":DoubleQuotedScalarString(local_container)})
        container_env.update({"ECCI_LOCAL_BROKER_IP":"${ECCI_LOCAL_BROKER_IP}"})
        container_env.update({"ECCI_LOCAL_BROKER_PORT":"${ECCI_LOCAL_BROKER_PORT}"})
        container_env.update({"ECCI_LOCAL_BROKER_ID":"${ECCI_LOCAL_BROKER_ID}"})
        container_env.update({"ECCI_LOCAL_BROKER_USERNAME":"${ECCI_LOCAL_BROKER_USERNAME}"})
        container_env.update({"ECCI_LOCAL_BROKER_PASSWORD":"${ECCI_LOCAL_BROKER_PASSWORD}"})
        container_env.update({"ECCI_AGENT_ID":"${ECCI_AGENT_ID}"})
        container_env.update({"ECCI_APP_TYPE":container_type})
    return compose_yml

# def read_yml(file):
#     with open(file,'r') as stream:
#         logic_topo = yaml.load(stream)

#     return logic_topo
# if __name__ == "__main__":
#     app_id = "app_id"
#     yml = read_yml('./agent-cloud_manager_agent1.yml')
#     import json
#     yml = json.dumps(yml)
#     encapsulated_compose = compose_encapsulate(app_id,yml)
#     from pathlib import Path
#     path = Path("./encapsulated_compose.yml")
#     yaml.dump(encapsulated_compose,path)
