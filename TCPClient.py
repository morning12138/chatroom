import socket
import tkinter as tk
import threading
import json
import tkinter.messagebox as mesBox
from tkinter import filedialog
import os
import sys
import struct
from tkinter.scrolledtext import ScrolledText
import pyaudio
import wave
import ast

clientIP = ''
clientPort = ''
user = ''
usersBox = ''
users = []
files = []

# 录音功能
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE= 44100
record_count = 1

# 登录窗口和登录功能
loginBox = tk.Tk()
loginBox.geometry("300x150")
loginBox.title("聊天室")
loginBox.resizable(0,0)
one = tk.Label(loginBox, text='登录')
one.pack()

# 设置默认值172.24.250.227:12345
inputIP = tk.StringVar(value='172.24.250.227:12564')
inputUser = tk.StringVar(value="wang")

labelIP = tk.Label(loginBox, text='IP:port')
labelIP.place(x=20, y=30, width=100, height=40)
entryIP = tk.Entry(loginBox, width=60, textvariable=inputIP)
entryIP.place(x=120, y=35, width=100, height=30)

labelUSER = tk.Label(loginBox, text='用户名')
labelUSER.place(x=20, y=75, width=100, height=40)
entryUSER = tk.Entry(loginBox, width=60, textvariable=inputUser)
entryUSER.place(x=120, y=80, width=100, height=30)

def Login(*args):
    global clientIP, clientPort, user
    if entryIP.get() == '':
        mesBox.showerror('warning', message='ip地址和端口为空！')
    clientIP, clientPort = entryIP.get().split(":")
    print(clientPort, clientIP)
    user = entryUSER.get()
    if not user:
        mesBox.showwarning('warning', message='用户名为空！')
    else:
        loginBox.destroy()


loginButton = tk.Button(loginBox, text="登录", command=Login)
loginButton.place(x=135, y=120, width=40, height=25)
loginBox.bind('<Return>', Login)

loginBox.mainloop()

# 建立连接
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 防止黏包
s.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)

s.connect((clientIP, int(clientPort)))

# 将新用户发送给服务端
if user:
    s.send(user.encode('utf-8'))
else:
    s.send(''.encode('utf-8'))
    user = clientIP + ':' + clientPort

# 聊天窗口
chatBox = tk.Tk()
chatBox.geometry('640x480')
chatBox.title('聊天室')
chatBox.resizable(0, 0)

# 消息界面
listBox = ScrolledText(chatBox)
listBox.place(x=5, y=0, width=640, height=320)
listBox.tag_config('tag1', foreground='red')
listBox.insert(tk.END, '欢迎进入聊天室！', 'tag1')

# 输入框
inputMes = tk.StringVar()
inputMes.set("")
entryInput = tk.Entry(chatBox, width=120, textvariable=inputMes)
entryInput.place(x=5, y=320, width=580, height=170)

# 在线用户列表
usersBox = tk.Listbox(chatBox)
usersBox.place(x=510, y=0, width=130, height=320)


def send(*args):
    # 处理黏包，设置包头
    cmd = 4
    ver = 1
    message = entryInput.get() + '^' + user
    message = json.dumps(message)
    print(message)
    header = [message.__len__(), cmd, ver]
    headPack = struct.pack('!3I', *header)
    sendData = headPack+message.encode('utf-8')
    print(sendData)
    s.send(sendData)
    inputMes.set("")


# 发送消息按钮
sendButton = tk.Button(chatBox, text='发送', anchor='center', command=send)
sendButton.place(x=585, y=320, width=55, height=300)
chatBox.bind('<Return>', send)


def record_audio():
    global record_count
    wave_out_path = user+'_record'+str(record_count)+'.wav'
    record_count += 1
    # 录音时间
    record_seconds = 5
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer=CHUNK)
    print("开始录音，请说话...")

    frames = []
    for i in range(0, int(RATE / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("录音结束")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(wave_out_path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


#录音按钮
getVoiceButton = tk.Button(chatBox, text='录音', anchor='center', command=record_audio)
getVoiceButton.place(x=135, y=290, width=60, height=30)
getVoiceButton.bind('<Return>', record_audio)

def uploadFile(*args):
    # 获得文件路径
    root = tk.Tk()
    root.withdraw()

    filePath = filedialog.askopenfilename()
    print("文件路径：", filePath)

    if os.path.isfile(filePath):
        # 显示上传文件
        message = '上传文件：' + os.path.basename(filePath) + '^' + user
        cmd = 4
        ver = 1
        message = json.dumps(message)
        print(message)
        header = [message.__len__(), cmd, ver]
        headPack = struct.pack('!3I', *header)
        sendData = headPack + message.encode('utf-8')
        s.send(sendData)

        # 定义文件信息
        # fileinfo_size = struct.calcsize('128sl')
        # fhead = struct.pack('128sl', os.path.basename(filePath).encode('utf-8'), os.stat(filePath).st_size)
        # print(fhead)
        cmd = 5
        fileSize =int(os.stat(filePath).st_size)
        print('filesize :'+str(fileSize))
        filename = os.path.basename(filePath)
        header = [filename.__len__(), cmd, fileSize]
        headPack = struct.pack('!3I', *header)
        sendData = headPack + filename.encode('utf-8')
        s.send(sendData)

        # 将文件以二进制分次上传至服务器
        fp = open(filePath, 'rb')
        while 1:
            data = fp.read(1024)
            if not data:
                print('{0} file send over ...'.format(os.path.basename(filePath)))
                break
            s.send(data)
        # with fp as f:
        #     data = f.read()
        #     print(data)
        #     s.sendall(data)
        #     print("\nsend over\n")
    return filePath


# 上传文件按钮
sendFileButton = tk.Button(chatBox, text='上传文件', anchor='center', command=uploadFile)
sendFileButton.place(x=5, y=290, width=60, height=30)
sendFileButton.bind('<Return>', uploadFile)

def downloadFile():
    fileBox = tk.Tk()
    fileBox.geometry('320x240')
    fileBox.title('群文件')
    fileBox.resizable(0, 0)
    fileList = tk.Listbox(fileBox)
    fileList.place(x=0, y=0, width=320, height=240)
    for x in range(len(files)):
        fileList.insert(tk.END, files[x])
    fileList.mainloop()
    return 0


# 下载文件按钮
downloadFileButton = tk.Button(chatBox, text='下载文件', anchor='center', command=downloadFile)
downloadFileButton.place(x=70, y=290, width=60, height=30)
downloadFileButton.bind('<Return>', downloadFile)


def dataHandleUserList(headPack, body):
    body = body.decode('unicode_escape')
    # print(body)
    global users
    print("bodySize:%s, cmd:%s, ver:%s" % headPack)
    users = ast.literal_eval(body)
    usersBox.delete(0, tk.END)
    usersBox.insert(tk.END, "当前在线用户")
    usersBox.insert(tk.END, '------Group chat------')
    for x in range(len(users)):
        usersBox.insert(tk.END, users[x])
    users.append('------Group chat------')


def dataHandleFileList(headPack, body):
    body = body.decode('unicode_escape')
    global files
    print("bodySize:%s, cmd:%s, ver:%s" % headPack)
    files = ast.literal_eval(body)

def dataHandleMessage(headPack, body):
    body=body.decode('unicode_escape')
    data = body.split('^')
    print(data)
    message = '\n' + data[0]
    userName = data[1]
    print(data[1])
    print("bodySize:%s, cmd:%s, ver:%s" % headPack)
    if userName[0:-1] == user:
        # 自己的消息
        listBox.tag_config('tag2', foreground='red')
        listBox.insert(tk.END, message, 'tag2')
    else:
        listBox.insert(tk.END, message)
    listBox.see(tk.END)


def receive():
    dataBuffer = bytes()
    headerSize = 12
    global users, files
    while True:
        data = s.recv(1024)
        if data:
            dataBuffer += data
            # print(data)
            # json 解析用户列表，失败则是正常的消息
            while True:
                if len(dataBuffer) < headerSize:
                    # print("数据包（%s Byte）小于消息头部长度，跳出小循环" % len(dataBuffer))
                    break

                # 读取包头
                headPack = struct.unpack('!3I', dataBuffer[:headerSize])
                bodySize = headPack[0]
                cmd = headPack[1]

                if len(dataBuffer) < headerSize + bodySize:
                    # print("数据包（%s Byte）不完整（总共%s Byte），跳出小循环" % (len(dataBuffer), headerSize + bodySize))
                    break;

                # 读取正文内容
                body = dataBuffer[headerSize:headerSize+bodySize]

                # 根据cmd来选择操作 1是操作users，2是操作files
                if cmd == 1:
                    dataHandleUserList(headPack, body)
                elif cmd == 2:
                    dataHandleFileList(headPack, body)
                elif cmd == 3:
                    dataHandleMessage(headPack, body)
                #黏包情况的处理 获取下一个数据包
                dataBuffer = dataBuffer[headerSize+bodySize:]



r = threading.Thread(target=receive)
r.start()

chatBox.mainloop()
s.close()

