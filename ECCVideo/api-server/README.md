
# API-Server
------------------------------------

基础环境：

```
操作系统：ubuntu；
编程语言：Python 3.5.2；
关系数据库：Postgres 9.5.14；
```

- 安装docker、docker-compose、harbor、mosquitto

- 安装harbor，修改harbor.cfg、docker-compose.yml，1880映射80

- 安装关系数据库Postgres：`apt install postgresql`

- 创建数据库：
  - `sudo -u postgres psql`
  - postgres=# `\password`
  - postgres=# `CREATE DATABASE edgeai;`

- 或者使用docker容器提供数据库服务：
  - `docker run -d -e POSTGRES_DB=edgeai -p 5432:5432 --name edgeaiPostgres postgres`

- 提供redis服务供channels使用channel-layer：
  - `docker run -d -p 6379:6379 --name edgeaiRedis redis:2.8`

- 安装Python依赖：`pip3 install -r requirements.txt`

- 初始化数据库：`python3 manage.py makemigrations api_server`

- 迁移数据库：`python3 manage.py migrate`

- 创建管理用户：`python3 manage.py createsuperuser`

- 启动服务：`python3 manage.py runserver 0.0.0.0:8000`
