# 云雀文件分享工具

这是一个好用的局域网分享文件的工具，解决日常工作和生活中需要局域网快速分享文件，定时文件、数据库备份的需求。

我的博客：[www.gaojunxin.cn](https://www.gaojunxin.cn)

## 功能
1. 定时文件备份并上传到服务端（已经实现）
2. 定时mysql备份并上传到服务端（已经实现）
3. 局域网文件上传和下载（尚未实现）


## 客户端
客户端实现了根据配置文件`config.yml`来定时备份数据库和文件夹，然后自动上传备份文件到服务端。

### 安装执行环境
1. 安装python环境
2. 安装pipenv
```shell
pip install pipenv
```
3. 安装脚本依赖
```shell
pipenv install
```
### 启动

1. 修改config.yml中的配置，并将整个agent文件夹放置在需要执行备份任务的计算机上。
2. 启动客户端
```bash
# 进入agent目录
cd agent
# 安装依赖
pipenv install
# 执行启动程序
pipenv run python agent.py
```

![image.png](http://image.gaojunxin.cn/i/2024/03/15/65f3f1aa841c4.png)

## 服务端

服务端采用flask实现了一个简单的文件上传，待完善更多功能。

### 安装执行环境
同客户端

### 启动

2. 启动服务端
```bash
# 进入agent目录
cd server
# 安装依赖
pipenv install
# 执行启动程序
pipenv run python app.py
```

提示如下日志，则启动成功

```log
❯ pipenv run python app.py
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 142-650-752
```
目前只实现了客户端自动上传到服务端，没有界面上的过多操作，等待后续补充操作界面。