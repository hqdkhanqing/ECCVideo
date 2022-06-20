import shutil
import os
import subprocess
import configparser
# from utils import *
from threading import Thread
import time
import logging
import json
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import ruamel.yaml
from pathlib import Path
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=4, sequence=6, offset=4)

ECCI_DOCKER_COMPOSE_YML_PATH = os.getenv("ECCI_DOCKER_COMPOSE_YML_PATH",default="./data/apps/")

def delete_app(app_id,app_path):
    app_composeyml_list = os.listdir(app_path)
    for compose_file_name in app_composeyml_list:
        docker_compose_file = f"{app_path}/{compose_file_name}"
        command = f"docker-compose -f {docker_compose_file} down --rmi all -v"
        logger.info(f"execute {compose_file_name} down --rmi all -v")
        result = subprocess.getoutput(command)
        print(f"down all result = {result}")
        # cmd = command.split(" ")
        # p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        
    # 删除该应用的文件夹及其内部的compose.yml文件
    shutil.rmtree(app_path)
    logger.info(f"execute {app_id} delete")


def compose_handle(app_id, handleType, yml=None, compose_type=None):
    logger.info("=========enter compose handle")
    logger.info("=========handleType="+handleType)
    if compose_type != None:
        logger.info("=========compose_type="+compose_type)
    try:
        logger.info("=========app_id="+app_id)
        # cf = configparser.ConfigParser()
        # cf.read("./data/configs/config.ini")
        # DOCKER_COMPOSE_YML_PATH = cf.get("docker-compose", "docker_compose_yml_path")
        app_path = ECCI_DOCKER_COMPOSE_YML_PATH + app_id

        # docker_compose_file 不单纯docker-compose.yml
        # docker_compose_file = app_path + '/docker-compose.yml'
        
        logger.info("=====os.path.exists(app_path)="+str(os.path.exists(app_path)))
    except Exception as e:
        print(e)
    if handleType == 'up':
        print("===enter up handler")
        try:
            if not os.path.exists(app_path):
                os.makedirs(app_path)
            
            # docker_compose_file不再只是单纯的docker-compose.yml,
            # 分为docker-compose-controller.yml和docker-compose-component.yml
            docker_compose_file = f"{app_path}/docker-compose-{compose_type}.yml"
            path = Path(docker_compose_file)
            yaml.dump(yml, path)
        except Exception as e:
            print(e)
            raise Exception("error")
        
        logger.info("write compose finished")
            # else:
            #     logger.info("===sync operate,no need to modify ymlContent")
        # subprocess.getoutput("docker-compose -f {} up -d".format(docker_compose_file))
        # logger.info(result)

        # try:
        #     command = f"docker-compose -f {docker_compose_file} up -d &"
        #     logger.debug("compose_handle command"+str(command))
        # except Exception as e:
        #     print(e)
        command = f"docker-compose -f {docker_compose_file} up -d"
        # command = f"docker-compose -f {docker_compose_file} pull && docker-compose -f {docker_compose_file} up -d"
        logger.debug("compose_handle command"+str(command))
        # subprocess.getoutput(command)

        # 12.28===========================
        cmd = command.split(" ")
        p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        # 12.28===========================


        # cmd = command.split(" ")
        # p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        # while p.poll() is None:
        #     line = p.stdout.readline()
        #     line = line.strip()
        #     if line:
        #         logger.info('Subprogram output: [{}]'.format(line))

        # for line in p.stdout:
        #     logger.info(line.rstrip("\n"))

        
        # if p.returncode == 0:
        #     logger.info('Subprogram success')
        # else:
        #     logger.info('Subprogram failed')

        logger.info("execute compose up")
        # TODO(gyf): maybe delete agent database
        # insertAppContentDB(app_id, handleType, ymlTime, updatetime)
    elif handleType == 'down' and os.path.exists(app_path):
        logger.info("remove test")
        app_composeyml_list = os.listdir(app_path)
        for compose_file_name in app_composeyml_list:
            docker_compose_file = f"{app_path}/{compose_file_name}"
            command = f"docker-compose -f {docker_compose_file} down"
            cmd = command.split(" ")
            p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            logger.info(f"execute {compose_file_name} down")
        logger.info(f"execute {app_id} down")
        # subprocess.getoutput(f"docker-compose -f {docker_compose_file} down &")
        # # TODO(gyf): maybe delete agent database
        # # updateAppContentDB(app_id, handleType, updatetime)
        # logger.info(result)
    elif handleType == 'start' and os.path.exists(app_path):
        logger.info("start test")
        docker_compose_file = f"{app_path}/docker-compose-{compose_type}.yml"
        if os.path.isfile(docker_compose_file):
            command = f"docker-compose -f {docker_compose_file} restart"
            cmd = command.split(" ")
            p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            logger.info(f"execute {docker_compose_file} start")
        # subprocess.getoutput(f"docker-compose -f {docker_compose_file} restart &")
        # # TODO(gyf): maybe delete agent database
        # # updateAppContentDB(app_id, handleType, updatetime)
        # logger.info(result)
    elif handleType == 'stop' and os.path.exists(app_path):
        logger.info("stop test")
        app_composeyml_list = os.listdir(app_path)
        for compose_file_name in app_composeyml_list:
            docker_compose_file = f"{app_path}/{compose_file_name}"
            command = f"docker-compose -f {docker_compose_file} stop"
            cmd = command.split(" ")
            p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            logger.info(f"execute {compose_file_name} stop")
        logger.info(f"execute {app_id} down")
        # subprocess.getoutput(f"docker-compose -f {docker_compose_file} stop &")
        # # TODO(gyf): maybe delete agent database
        # # updateAppContentDB(app_id, handleType, updatetime)
        # logger.info(result)
    elif handleType == 'clean' and os.path.exists(app_path):
        logger.info("clean test")
        app_composeyml_list = os.listdir(app_path)
        for compose_file_name in app_composeyml_list:
            docker_compose_file = f"{app_path}/{compose_file_name}"
            command = f"docker-compose -f {docker_compose_file} down --rmi all -v"
            cmd = command.split(" ")
            p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            logger.info(f"execute {compose_file_name} down --rmi all -v")
        logger.info(f"execute {app_id} down")
        # subprocess.getoutput(f"docker-compose -f {docker_compose_file} down --rmi all -v &")
        # shutil.rmtree(app_path)
        # # TODO(gyf): maybe delete agent database
        # # deleteAppContentDB(app_id)
        # logger.info(result)
    elif handleType == 'delete' and os.path.exists(app_path):
        logger.info(f"delete test, clean and delete {app_id} folder")
        
        delete_th = Thread(target=delete_app,args=(app_id, app_path))
        delete_th.start()
        # app_composeyml_list = os.listdir(app_path)
        # for compose_file_name in app_composeyml_list:
        #     docker_compose_file = f"{app_path}/{compose_file_name}"
        #     command = f"docker-compose -f {docker_compose_file} down --rmi all -v"
        #     cmd = command.split(" ")
        #     p = subprocess.Popen(cmd,shell=False, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        #     logger.info(f"execute {compose_file_name} down --rmi all -v")
        # # 删除该应用的文件夹及其内部的compose.yml文件
        # shutil.rmtree(app_path)
        # logger.info(f"execute {app_id} delete")