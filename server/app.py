import os
import time

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 设置上传文件的保存路径
app.config['UPLOAD_FOLDER'] = 'upload'


@socketio.on('connect')
def connect(message):
    client_ip = request.environ.get('REMOTE_ADDR')
    print(f'建立连接成功: {client_ip}')


@socketio.on('disconnect')
def disconnect(message):
    client_ip = request.environ.get('REMOTE_ADDR')
    print(f'关闭连接成功: {client_ip}')


@socketio.on('keepalive')
def keepalive(message):
    print('保持心跳连接')
    emit('keepalive', message)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = file.filename
        # 上传文件路径
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'])

        # 完整的文件保存路径
        file_path = os.path.join(upload_dir, filename)

        # 文件存放的父目录
        base_dir = os.path.dirname(file_path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file.save(file_path)
        return {'msg': 'success'}


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True, debug=True)
