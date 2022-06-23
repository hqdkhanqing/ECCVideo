# 应用逻辑说明
应用共包含cloud、edge1、edge2三个容器，其中cloud位于中心云服务器、edge1、edge2位于边缘云服务器

## 第一步
edge1容器启动后，告知cloud已经启动，进入阻塞

edge2容器启动后，告知cloud已经启动，等待接收数据

cloud容器启动后，得知edge1、edge2都已经准备好，向edge1发送启动控制命令

## 第二步
edge1容器收到启动控制命令后，开始连续发出10条发送时间的mqtt消息至edge2

发完后，edge1容器进入循环等待控制命令

## 第三步
mqtt消息到达edge2后，edge2容器添加接收到的时间并将消息发送到cloud容器

## 第四步
cloud容器收到10条mqtt消息后，计算并打印每一段的传输时间，并向edge1容器发送请求发送file控制命令

## 第四步
edge1收到发送file控制命令后，连续3次将字符串以content形式发送到edge2

## 第五步
edge2容器收到后，先同样以content形式下载，再将3条字符串存储到testFile.txt本地文件中，再将文件以file形式发送到cloud

## 第六步
cloud容器收到后，以文件形式保存，并读文件输出
