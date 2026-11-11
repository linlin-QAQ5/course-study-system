# 课程学习记录系统

作者：张逸霖  
学号：202612190002  
课程：Docker容器技术  
选题：容器化Web应用（前端＋后端＋数据库）

## 一、简介

本项目用于记录课程学习内容，支持新增记录、查询记录、
修改完成状态和删除记录。

项目使用Nginx、Flask和MySQL三个容器，通过Docker Compose
统一部署。数据库使用命名卷持久化，服务通过自定义网络通信。

本项目为课程实验，没有用户登录和权限控制，不用于保存敏感信息。
如在云服务器演示，应限制访问来源，演示结束后停止服务。

## 二、架构

| 服务 | 技术 | 容器端口 | 功能 |
|---|---|---|---|
| web | Nginx | 80 | 提供页面，将/api/请求转发给后端 |
| api | Flask＋Gunicorn | 5000 | 处理业务请求并访问数据库 |
| db | MySQL 8.0 | 3306 | 保存课程学习记录 |

默认仅web发布宿主机8080端口。
api和db不发布宿主机端口，通过app-net网络通信。

数据库文件存放于db_data命名卷。
实际卷和网络名称带Compose项目名前缀。

后端Dockerfile包括builder和runtime两个阶段。
builder安装Python依赖，runtime复制依赖环境和应用代码，
以非root用户运行Gunicorn。

主要文件：
- compose.yml：服务、网络、卷、健康检查与启动依赖。
- .env.example：环境变量模板。
- api/app.py：后端接口。
- api/requirements.txt：Python直接依赖版本。
- api/Dockerfile：后端多阶段构建。
- web/index.html：前端页面。
- web/default.conf：Nginx反向代理配置。
- web/Dockerfile：前端镜像构建。
- db/init.sql：首次初始化数据库表。

## 三、部署

### 环境要求

目标机器应已安装Docker Engine和Docker Compose插件，
并能够下载基础镜像和Python依赖。
默认端口8080应空闲。

浏览器可使用Chrome、Edge等现代浏览器。
无需在宿主机安装Python、Nginx或MySQL。

### 获取代码

```bash
git clone https://github.com/linlin-QAQ5/course-study-system.git
cd course-study-system
```

也可以在GitHub选择Code → Download ZIP，解压后进入项目目录。

### 准备配置

```bash
cp .env.example .env
```

编辑.env，将MYSQL_ROOT_PASSWORD和MYSQL_PASSWORD替换为
两组不同的实验密码。建议使用较长的随机字母数字串。
.env包含实际密码，不提交到仓库。

默认配置使用Docker Hub和PyPI。
如果所在网络访问困难，可在.env中配置可访问的镜像与依赖源。
本项目搭建时采用过以下设置，但第三方服务的可用性可能变化：

```dotenv
MYSQL_IMAGE=docker.m.daocloud.io/library/mysql:8.0
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim-bookworm
NGINX_IMAGE=docker.m.daocloud.io/library/nginx:alpine
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

### 启动

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

等待db和api显示healthy，web显示Up。

未修改代码时，后续启动可使用：

```bash
docker compose up -d
```

浏览器访问：

```text
http://localhost:8080
```

若部署在云服务器，则在电脑浏览器访问服务器公网IP的8080端口，
并根据需要设置安全组来源。后端和数据库端口无需对外开放。

停止并删除容器与网络，同时保留数据：

```bash
docker compose down
```

## 四、使用

1. 填写课程名称和学习内容，点击“保存记录”。
2. 在列表中查看已保存的记录。
3. 点击“标记完成”或“改为待完成”，修改学习状态。
4. 点击“删除”并确认，删除对应记录。
5. 点击“刷新列表”或刷新浏览器，重新查询数据。

页面显示的创建时间为UTC。

接口：
- GET /api/records：查询记录。
- POST /api/records：新增记录。
- PATCH /api/records/<id>：修改完成状态。
- DELETE /api/records/<id>：删除记录。
- 后端内部GET /health：检查数据库表是否可访问。

## 五、测试

### 启动与访问

```bash
docker compose ps
curl -I http://localhost:8080
curl -i http://localhost:8080/api/records
docker compose logs --tail=30 db api web
```

预期页面与列表接口返回HTTP 200。
初次启动且未新增记录时，列表接口返回空数组。

### 功能测试

在网页新增正式记录，修改完成状态，刷新后检查结果。
另建一条临时记录并删除，确认列表正确更新。
保留正式记录用于持久化测试。

### 持久化测试

```bash
docker compose down
docker compose up -d
docker compose ps
```

等待服务恢复健康后刷新网页，原记录和完成状态应保留。
测试过程中不能重新插入原记录。

### 复现检查

在另一台安装Docker与Compose的机器上重新获取代码，
复制.env.example为.env并配置密码，然后执行启动命令。
首次启动应能自动创建数据表。

同机换目录测试只能验证部署路径的独立性，
不能代替另一台机器的完整复现测试。
若两套系统同时运行，应使用不同的项目目录名和WEB_PORT。

## 六、常见问题

### 1. 8080端口被占用

检查其他容器或进程，或修改.env中的WEB_PORT。
修改后使用相应端口访问页面。

### 2. 镜像或依赖下载超时

检查网络和镜像源。
可通过.env修改MYSQL_IMAGE、PYTHON_IMAGE、NGINX_IMAGE和
PIP_INDEX_URL，再重新构建。

### 3. 后端或数据库不健康

运行：

```bash
docker compose logs --tail=80 db api
```

检查数据库初始化、连接参数及报错信息。
不要在未判断原因时删除数据卷。

### 4. 修改.env密码后连接失败

MySQL初始化变量主要作用于空数据目录的首次初始化。
已有数据卷中的数据库密码不会因修改.env而自动更新。
应恢复原配置，或通过数据库管理命令正确修改密码。

### 5. 修改init.sql后没有生效

/docker-entrypoint-initdb.d中的脚本只在数据目录首次初始化时执行。
已有数据库的表结构修改需要通过SQL迁移完成。

### 6. 为什么不用docker compose down -v停止项目

down默认保留命名卷，down -v会删除本项目声明的命名卷，
使学习记录丢失。仅在明确要彻底清空实验数据时使用-v。

### 7. 服务器curl成功，但电脑浏览器打不开

检查是否使用服务器公网IP、http协议以及正确端口，
并检查云安全组和服务器防火墙规则。

### 8. 修改网页或后端代码后没有更新

重新构建并启动：

```bash
docker compose up -d --build
```
