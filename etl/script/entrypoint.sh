#!/usr/bin/env bash

# set_conda_env

function set_python_env(){

  echo "Started setting conda python environment"
  ${MLFLOW_HOME}/miniconda3/bin/conda init bash >> ${MLFLOW_HOME}/entrypoint_log.log
  source ${MLFLOW_HOME}/.bashrc > 83403ea76c4c> ${MLFLOW_HOME}/entrypoint_log.log

  conda activate nba-ml
  echo "Finished setting conda environment!"

}

function set_aws_config(){
  echo "Started setting aws credentials"
  /aws_config.sh
}

function get_ml_script(){

  echo "Started downloading ml scripts"

  aws s3 cp s3://${s3_location} ${MLFLOW_HOME}/main.py
}