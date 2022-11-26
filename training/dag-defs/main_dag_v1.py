'''dag declaration for apache airflow
'''
from datetime import timedelta, datetime
import boto3

from airflow import DAG
from airflow.operators.python import PythonOperator


# Client settings
SERVICE_NAME = "ecs"
REGION_NAME = "us-east-1"
DELAY = 6
MAX_ATTEMPTS = 1000


# settings for running task
LAUNCH_TYPE = "FARGATE"
CLUSTER_NAME = "NBA-ML-FLOW-CLUSTER"
PLATFORM_VERSION = "LATEST"
CONTAINER_NAME = "nba-mlflow-container"
NETWORK_CONFIG = {
    'awsvpcConfiguration': {
        'subnets': ['subnet-0387bc990898b9097','subnet-0fcf53881946f87a8'],
        'assignPublicIp': 'ENABLED',
        'securityGroups': ["sg-0e266710159c321dc"]
    }
}

main_command = [
    'bash', '-c', (
        'source /entrypoint.sh && set_python_env && get_ml_script'
        '&& python ${MLFLOW_HOME}/ml-scripts/main.py --year-arr ${YEAR_ARR}'
    )
]

main_command_0 = ['bash', '-c', ('source /entrypoint.sh && set_python_env ')]

# Args to run_ecs_task function so that they run intended python script/ml dag
TASK_GAMELOG_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_get_gamelog.env',
    "description": "get_gamelog"
}


TASK_GAMEROTATION_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command_0,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_get_gamerotation.env',
    "description": "get_gamerotation"
}


TASK_DAYSTAT_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command_0,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_get_daystat.env',
    "description": "get_daystat"
}


TASK_TRANSFORM_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_transform.env',
    "description": "transform"
}

TASK_TRAINING_DATA_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_training_data.env',
    "description": "get_training_data"
}


TASK_DYNAMODB_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_dynamodb.env',
    "description": "write_to_dynamodb"
}

TASK_TRAIN_MODEL_KWARGS = {
    "task_def": 'nba_mlflow_vtrial',
    "task_command": main_command,
    "task_env": 'arn:aws:s3:::mert-kurttutan-nba-ml-files/env-files/cfg_train_model.env',
    "description": "train_model"
}


def run_ecs_task(
    task_def: str, task_env: str, task_command: list[str], description: str
):
    '''ecs task for dag run'''

    client = boto3.client(service_name=SERVICE_NAME, region_name=REGION_NAME)
    response = client.run_task(
        taskDefinition=task_def,
        launchType=LAUNCH_TYPE,
        cluster=CLUSTER_NAME,
        platformVersion=PLATFORM_VERSION,
        count=1,
        networkConfiguration=NETWORK_CONFIG,
        overrides={
            'containerOverrides': [{
                "name": CONTAINER_NAME,
                'command': task_command,
                'environmentFiles': [{
                    'value': task_env,
                    'type': 's3'
                }]
            }]
        }
    )
    print(f"Started running task {description}...")

    task_arn = response["tasks"][0]["containers"][0]["taskArn"]

    # Wait until task is stopped
    waiter = client.get_waiter('tasks_stopped')

    waiter.wait(
        cluster=CLUSTER_NAME,
        tasks=[task_arn],
        WaiterConfig={
            'Delay': DELAY,
            'MaxAttempts': MAX_ATTEMPTS
        }
    )

    print(f"Task {description} is finished ...")
    task_description = client.describe_tasks(
        cluster=CLUSTER_NAME,
        tasks=[task_arn]
    )


one_days_ago = datetime.combine(
    datetime.today() - timedelta(1), datetime.min.time()
)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': one_days_ago,
    'email': ['kurttutan.mert@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    #'schedule': '@once',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}


dag = DAG('nba_main_dag', default_args=default_args)


t_gamelog = PythonOperator(
    task_id = TASK_GAMELOG_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_GAMELOG_KWARGS,
    dag=dag,
)

t_gamerotation = PythonOperator(
    task_id = TASK_GAMEROTATION_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_GAMEROTATION_KWARGS,
    dag=dag,
)

t_daystat = PythonOperator(
    task_id = TASK_DAYSTAT_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_DAYSTAT_KWARGS,
    dag=dag,
)

t_transform = PythonOperator(
    task_id = TASK_TRANSFORM_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_TRANSFORM_KWARGS,
    dag=dag,
)

t_training_data = PythonOperator(
    task_id = TASK_TRAINING_DATA_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_TRAINING_DATA_KWARGS,
    dag=dag,
)

t_dynamodb = PythonOperator(
    task_id = TASK_DYNAMODB_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_DYNAMODB_KWARGS,
    dag=dag,
)

t_train_model = PythonOperator(
    task_id = TASK_TRAIN_MODEL_KWARGS["description"],
    python_callable = run_ecs_task,
    op_kwargs = TASK_TRAIN_MODEL_KWARGS,
    dag=dag,
)

t_gamelog #>> t_gamerotation

# t_gamerotation >> t_transform

# t_daystat >> t_transform

# t_transform >> t_training_data

# t_transform >> t_dynamodb

# t_training_data >> t_train_model