from posixpath import split
from flask import Flask, send_from_directory,request
import json
import subprocess
import os
import yaml
from shutil import copyfile
from pathlib import Path


app = Flask(__name__,static_url_path='', static_folder='ww')

source = os.getcwd()
#parent = source
parent = os.path.dirname(source)
cp4d_config_path = os.path.join(parent,'sample-configurations/web-ui-base-config/cloud-pak')
ocp_config_path = os.path.join(parent,'sample-configurations/web-ui-base-config/ocp')
inventory_config_path = os.path.join(parent,'sample-configurations/web-ui-base-config/inventory')
confg_dir=str(os.getenv('CONFIG_DIR'))
status_dir=str(os.getenv('STATUS_DIR'))
target_config=confg_dir+'/config'
target_inventory=confg_dir+'/inventory'
Path( target_config ).mkdir( parents=True, exist_ok=True )
Path( target_inventory ).mkdir( parents=True, exist_ok=True )

@app.route('/')
def index():
    return send_from_directory(app.static_folder,'index.html')


@app.route('/api/v1/deploy',methods=["POST"])
def deploy():
    body = json.loads(request.get_data())
    env ={}
    if body['cloud']=='ibm-cloud':
      env = {'IBM_CLOUD_API_KEY': body['env']['ibmCloudAPIKey'],
             'CP_ENTITLEMENT_KEY': body['env']['entilementKey'],
             'CONFIG_DIR':confg_dir,
             'STATUS_DIR':status_dir}
      process = subprocess.run([parent+'/cp-deploy.sh', 'env', 'apply','-e env_id={}'.
                               format(body['envId']),'-e ibm_cloud_region={}'.format(body['region']), '--check-only'], 
                           stdout=subprocess.PIPE,
                           universal_newlines=True,
                           env=env)
      process.stdout
    return 'runing'

@app.route('/api/v1/cartridges/<cloudpak>',methods=["GET"])
def getCartridges(cloudpak):
    cartridges_list=[]
    with open(cp4d_config_path+'/{}.yaml'.format(cloudpak),encoding='UTF-8') as f:
        read_all = f.read()
        read_all = read_all.replace('{{ env_id }}' , "env_id")
        docs =yaml.load_all(read_all, Loader=yaml.FullLoader)
        for doc in docs:
            if cloudpak in doc.keys():
               cartridges_list = doc[cloudpak][0]['cartridges']
               break
    return json.dumps(cartridges_list)

@app.route('/api/v1/logs',methods=["GET"])
def getLogs():
    result={}
    result["logs"]='waiting'
    log_path=status_dir+'/log/cloud-pak-deployer.log'
    print(log_path)
    if os.path.exists(log_path):
        result["logs"]=open(log_path,"r").read()
    return json.dumps(result)

@app.route('/api/v1/storages/<cloud>',methods=["GET"])
def getStorages(cloud):
   ocp_config=""
   with open(ocp_config_path+'/{}.yaml'.format(cloud), encoding='UTF-8') as f:
    read_all = f.read()

    read_all = read_all.replace('{{ env_id }}' , "env_id").replace('{{ ibm_cloud_region }}', 'ibm_cloud_region')

    datas = yaml.load_all(read_all, Loader=yaml.FullLoader)
    for data in datas:
      if 'openshift' in data.keys():
        ocp_config = data['openshift'][0]['openshift_storage']
        break
   return json.dumps(ocp_config)

def update_cartridges(path,cartridges):
    
    return

@app.route('/api/v1/loadConfig',methods=["POST"])
def loadConfig():
    body = json.loads(request.get_data())
    env_id=body['envId']
    cloud=body['cloud']
    #cartridges=body['cartridges']

    source_cp4d_config_path = cp4d_config_path+'/cp4d.yaml'
    generated_cp4d_yaml_path = target_config+'/{}-cp4d.yaml'.format(env_id)
    
    
    copyfile(source_cp4d_config_path,generated_cp4d_yaml_path)
    source_ocp_config_path = ocp_config_path+'/{}.yaml'.format(cloud)
    generated_ocp_yaml_path = target_config+'/{}-ocp.yaml'.format(env_id)
    copyfile(source_ocp_config_path,generated_ocp_yaml_path)
    source_inventory_config_path=inventory_config_path+'/{}.inv'.format(cloud)
    generated_inventory_yaml_path = target_inventory+'/{}.inv'.format(env_id)
    copyfile(source_inventory_config_path,generated_inventory_yaml_path)
   
    result={}
    result["cp4d"]=open(generated_cp4d_yaml_path,"r").read()
    result["envId"]=open(generated_ocp_yaml_path, "r").read()
    return json.dumps(result)
            
        
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='32080', debug=False)    