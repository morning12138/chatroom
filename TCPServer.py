import socket
import threading
import queue
import json
import os
import os.path
import sys
import struct

# common variables
serverIP = '172.24.250.227'
serverPort = 12564
# use to save messages from clients
messages = queue.Queue()
users = []  # tuple:(name, connection)
lock = threading.Lock()
files = []
# filesString = ''
filePath = 'D:\\python_project\\serverFile'

def usersNameList():
    USERNAMES = []
    for i in range(len(users)):
        USERNAMES.append(users[i][0])
    return USERNAMES

class ServerMain(threading.Thread):
    global users, que, lock, filesString, files, filePath

    def __init__(self):
        threading.Thread.__init__(self)
        # TCP
        self.soc =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        # os.chdir(sys.path[0])


    # 接受数据
    def Load(self, data, addr):
        # 锁
        lock.acquire()
        try:
            messages.put((addr, data))
        finally:
            lock.release()

    def sendData(self):
        while True:
            if not messages.empty():
                message = messages.get()
                # print(message)
                # print(users)
                if isinstance(message[1], str):
                    # 自定义协议处理黏包
                    # 3 代表消息
                    data = " " + message[1]
                    # print("hello")
                    # print(data)
                    cmd = 3
                    ver = 1
                    header = [data.__len__(), cmd, ver]
                    headPack = struct.pack("!3I", *header)
                    sendData = headPack + data.encode('utf-8')
                    # print(data + "world\n")
                    # users[0][1].send(sendData)
                    print(users)
                    for i in range(len(users)):
                        # print(data + "world\n")
                        users[i][1].send(sendData)
                        # print(data+"world\n")

                if isinstance(message[1], list):
                    data = json.dumps(message[1])
                    # 自定义协议处理黏包
                    # 1 代表用户列表
                    cmd = 1
                    ver = 1
                    header = [data.__len__(), cmd, ver]
                    headPack = struct.pack("!3I", *header)
                    sendData = headPack + data.encode('utf-8')
                    print(data)
                    for i in range(len(users)):
                        try:
                            users[i][1].send(sendData)
                        except:
                            pass


    # 添加新用户
    def receiveUser(self, conn, addr):
        user = conn.recv(1024).decode('utf-8')
        global files
        # 用户名为空
        if user == '':
            user = addr[0] + ":" + str(addr[1])

        # 检验重名并给出编号
        tag = 1
        for i in range(len(users)):
            if users[i][0] == user:
                user = user + str(tag)
                tag += 1
        users.append((user, conn))
        USERNAMES = usersNameList()
        print(USERNAMES)
        self.Load(USERNAMES, addr)

        # 新增用户的时候传输文件列表
        # 自定义协议处理黏包
        # 2 代表文件列表
        print(files)
        print('\n')
        filedata = json.dumps(files)
        cmd = 2
        ver = 1
        header = [filedata.__len__(), cmd, ver]
        headPack = struct.pack("!3I", *header)
        sendData = headPack + filedata.encode('utf-8')
        users[-1][1].send(sendData)

        dataBuffer = bytes()
        headerSize = 12
        # 不断接受数据
        # print("hello")
        try:
            while True:
                data = conn.recv(1024)
                if data:
                    dataBuffer += data
                    while True:
                        if len(dataBuffer) < headerSize:
                            break;
                        # 读取包头
                        headPack = struct.unpack('!3I', dataBuffer[:headerSize])
                        bodySize = headPack[0]
                        cmd = headPack[1]
                        ver = headPack[2]
                        if len(dataBuffer) < headerSize + bodySize:
                            break
                        body = dataBuffer[headerSize:headerSize+bodySize]
                        print(body.decode('utf-8'))
                        # 数据处理
                        if cmd == 4:
                            message = body.decode()[1:]
                            message = user + ":" + message
                            self.Load(message, addr)
                        # elif cmd == 5:
                        elif cmd == 5:
                            print("\nno bad!")
                            # 有bug！会报错
                            print(ver)
                            fn = body.strip(b'\00').decode('utf-8')
                            print("filename is "+fn+'\n')
                            print('file new name is {0}, filesize is {1}'.format(str(fn), ver))
                            recvd_size = 0
                            fp = open('./serverFile/' + str(fn), 'wb')
                            print('start receiving...')
                            while not recvd_size == ver:
                                if ver - recvd_size > 1024:
                                    data = conn.recv(1024)
                                    recvd_size += len(data)
                                else:
                                    print("last turn")
                                    data = conn.recv(ver - recvd_size)
                                    print(data)
                                    recvd_size = ver
                                print("recvd_size:" + str(recvd_size))
                                fp.write(data)
                            fp.close()
                            files.append(str(fn))
                            print(files)
                            print('end receive...')
                            # filesize = headPack[2]
                            # print("filesize is "+filesize)
                        # elif cmd == 5:
                        #     fileinfo_size = struct.calcsize('128sl')
                        #     buf = conn.recv(fileinfo_size)
                        #     if data:
                        #         filename, filesize = struct.unpack('128sl', data)
                        #         fn = filename.strip(b'\00')
                        #         fn = fn.decode('utf-8')
                        #         print('file new name is {0}, filesize if {1}'.format(str(fn), filesize))
                        #
                                # recvd_size = 0
                                # fp = open('./serverFile/' + str(fn), 'wb')
                                # print('start receiving...')
                                # while not recvd_size == filesize:
                                #     if filesize - recvd_size > 1024:
                                #         data = conn.recv(1024)
                                #         recvd_size += len(data)
                                #     else:
                                #         data = conn.recv(filesize - recvd_size)
                                #         recvd_size = filesize
                                #     fp.write(data)
                                # fp.close()
                                # files.append(str(fn))
                                # print(files)
                                # print('end receive...')

                        # 处理黏包
                        dataBuffer = dataBuffer[headerSize+bodySize:]
                # if message[0:4] == '上传文件':
                #     message = user + ":" + message
                #     self.Load(message, addr)
                #     print("hello")ze('128sl')
                #     buf = conn.recv(fileinfo_size)
                #     fileinfo_size = struct.calcsi
                #     if (buf):
                #         filename, filesize = struct.unpack('128sl', buf)
                #         fn = filename.strip(b'\00')
                #         fn = fn.decode()
                #         print('file new name is {0}, filesize if {1}'.format(str(fn), filesize))
                #
                #         recvd_size = 0
                #         fp = open('./serverFile/' + str(fn), 'wb')
                #         print('start receiving...')
                #
                #         while not recvd_size == filesize:
                #             if filesize - recvd_size > 1024:
                #                 data = conn.recv(1024)
                #                 recvd_size += len(data)
                #             else:
                #                 data = conn.recv(filesize - recvd_size)
                #                 recvd_size = filesize
                #             fp.write(data)
                #         fp.close()
                #         files.append(str(fn))
                #         print(files)
                #         print('end receive...')
                # # else:
                #     message = user + ":" + message
                #     self.Load(message, addr)


            conn.close()
        except:
            # 删除退出的用户
            print("delete user")
            index = 0
            for one in users:
                if one[0] == user:
                    users.pop(index)
                    break
                index += 1

            # 更新用户列表
            USERNAMES = usersNameList()
            self.Load(USERNAMES, addr)
            conn.close()

    def run(self):
        self.soc.bind((serverIP, serverPort))
        self.soc.listen(5)
        q = threading.Thread(target=self.sendData)
        q.start()
        while True:
            conn, addr = self.soc.accept()
            t = threading.Thread(target=self.receiveUser, args = (conn, addr))
            t.start()
        self.soc.close()


if __name__ == '__main__':
    # global files
    for i, j, k in os.walk(filePath):
        files = k
        print(files)
        print('\n')
    runServer = ServerMain()
    runServer.start()

