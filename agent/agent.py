import os
import time

import socketio
import requests
from apscheduler.events import EVENT_ALL, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import yaml
from colorama import init, Fore
import zipfile
from loguru import logger
import sqlite3

# 0未获取 1已连接 2保持连接 3已断开
server_status = 0


def heart_beat_task():
    """
    与服务器保持心跳链接，暂时先不使用，尝试阶段
    :return:
    """
    server_config = config.get("server", {})
    server_host = server_config.get("host")
    server_port = server_config.get("port")
    uri = f"http://{server_host}:{server_port}/"
    # 创建 Socket.IO 客户端实例
    sio = socketio.Client()

    # 定义连接成功时的处理函数
    @sio.on('connect')
    def connect():
        global server_status
        print('连接到服务器成功')
        server_status = 1

    # 定义断开连接时的处理函数
    @sio.on('disconnect')
    def disconnect():
        global server_status
        print('服务器断开连接')
        server_status = 3

    @sio.on('keepalive')
    def keepalive(msg):
        global server_status
        print('保持心跳连接')
        server_status = 2

    # 连接到 Flask-SocketIO 服务器
    sio.connect(uri)

    try:
        while True:
            sio.emit('keepalive', 'this is ok')
            sio.sleep(1)

    except KeyboardInterrupt:
        global server_status
        # 断开连接并退出
        sio.disconnect()
        server_status = 3


def backup_database(host, port, user, password, database, backup_dir):
    """
    创建mysql数据库备份
    :param host:
    :param port:
    :param user:
    :param password:
    :param database:
    :param backup_dir:
    :return:
    """
    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 获取当前时间
    current_time = time.strftime('%Y%m%d%H%M%S', time.localtime())

    # 构造备份文件名
    backup_file = os.path.join(backup_dir, f'{database}_{current_time}.sql')

    # 构造备份命令
    backup_cmd = f'mysqldump -h {host} -P {port} -u {user} -p{password} {database} > {backup_file}'

    # 执行备份命令
    os.system(backup_cmd)
    return backup_file


def upload_file(file_path, upload_url):
    """
    上传文件到服务器
    :param file_path:
    :param upload_url:
    :return:
    """
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(upload_url, files=files)

        if response.status_code == 200:
            print(f'File {file_path} uploaded successfully.')
        else:
            print(f'Failed to upload file {file_path}. Status code: {response.status_code}')


# 根据目录压缩文件
def zip_dir(directory, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory)
                zipf.write(file_path, arcname)


def db_backup_task():
    """
    数据库备份任务
    :return:
    """
    print("mysql备份任务执行，时间：", time.strftime("%Y-%m-%d %H:%M:%S"))
    mysql_config = config.get("mysql_task", {})
    mysql_host = mysql_config.get("host")
    mysql_port = mysql_config.get("port")
    mysql_username = mysql_config.get("username")
    mysql_password = mysql_config.get("password")
    database = mysql_config.get("database")
    backupDir = mysql_config.get("backupDir")
    backup_file = backup_database(mysql_host, mysql_port, mysql_username, mysql_password, database, backupDir)

    server_config = config.get("server", {})
    if server_config == {}:
        return
    server_host = server_config.get("host")
    server_port = server_config.get("port")
    upload_url = f"http://{server_host}:{server_port}/upload"
    try:
        upload_file(backup_file, upload_url)
    except Exception:
        print(f"{Fore.YELLOW}警告：服务器上传失败，暂不进行上传，请根据本地备份手动进行上传.{Fore.RESET}")


def file_backup_task():
    """
    文件备份任务
    :return:
    """
    print("文件备份任务执行，时间：", time.strftime("%Y-%m-%d %H:%M:%S"))
    file_config = config.get("file_task", {})
    backupDir = file_config.get("backupDir")
    name = file_config.get("name")

    # 执行文件压缩
    current_time = time.strftime('%Y%m%d%H%M%S', time.localtime())

    file_backup_dir = "file_backup"
    # 创建备份目录
    if not os.path.exists(file_backup_dir):
        os.makedirs(file_backup_dir)
    file_path = f'{file_backup_dir}/{name}-{current_time}.zip'
    zip_dir(backupDir, file_path)

    server_config = config.get("server", {})
    if server_config == {}:
        return
    server_host = server_config.get("host")
    server_port = server_config.get("port")
    upload_url = f"http://{server_host}:{server_port}/upload"
    try:
        upload_file(file_path, upload_url)
    except Exception:
        print(f"{Fore.YELLOW}警告：服务器上传失败，暂不进行上传，请根据本地备份手动进行上传.{Fore.RESET}")


def print_banner():
    banner = r"""
           ______      _                                   
 .' ___  |    (_)                                  
/ .'   \_|    __  _   __    .--.   _ .--.   .--.   
| |   ____   [  |[ \ [  ] / .'`\ \[ '/'`\ \( (`\]  
\ `.___]  |_  | | > '  <  | \__. | | \__/ | `'.'.  
 `._____.'[ \_| |[__]`\_]  '.__.'  | ;.__/ [\__) ) 
           \____/                 [__|             

        """
    print(banner)


if __name__ == '__main__':
    init()
    # 打印banner
    print_banner()

    # 加载配置文件
    with open("config.yml", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 启动心跳检测线程，暂不启用
    # thread = threading.Thread(target=heart_beat_task)
    # thread.start()

    # 单次任务测试
    # db_backup_task()

    db_path = "task.db"
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        logger.info("数据库文件已创建.")
        conn.close()

    executes = {
        "default": ThreadPoolExecutor(5)
    }

    job_default = {
        'coalesce': False,
        'max_instances': 3
    }

    # 启动定时任务
    scheduler = BlockingScheduler(executes=executes, job_default=job_default)
    jobstore = SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
    scheduler.add_jobstore(jobstore=jobstore)


    # 任务事件监听函数
    def task_listener(event):
        job = scheduler.get_job(event.job_id)
        if event.exception:
            # 处理作业执行异常事件
            logger.info(f"任务 {job.name} 发生错误: {event.exception}")
        else:
            # 处理作业执行成功事件
            logger.info(f"任务 {job.name} 执行成功")


    scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # 每分钟执行一次，测试用
    # scheduler.add_job(db_backup_task, 'interval', minutes=1)

    # mysql备份任务
    mysql_task_config = config.get("mysql_task", {})
    task_crontab = mysql_task_config.get("crontab")
    if task_crontab:
        trigger = CronTrigger.from_crontab(task_crontab)
        job_id = 'mysql_backup'
        scheduler.add_job(db_backup_task, trigger=trigger, id=job_id, name="mysql备份任务", max_instances=2,
                          replace_existing=True)

    # 文件备份任务
    file_task_config = config.get("file_task", {})
    task_crontab = file_task_config.get("crontab")
    if task_crontab:
        trigger = CronTrigger.from_crontab(task_crontab)
        job_id = 'file_backup'
        scheduler.add_job(file_backup_task, trigger=trigger, id=job_id, name="文件备份任务", max_instances=2,
                          replace_existing=True)
    try:
        scheduler.print_jobs()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("终止调度器，等待正在执行的任务结束自动退出")
        logger.info(scheduler.get_jobs())
        scheduler.shutdown(wait=True)
