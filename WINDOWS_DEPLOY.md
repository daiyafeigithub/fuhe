# Windows 一键部署说明（小白版）

这份说明给不懂技术的同事使用，按步骤做就可以。

## 这个脚本会自动做什么

- 自动下载并安装必须软件：Git、Python、Node.js、Nginx
- 自动从 Gitee 拉取最新代码：`https://gitee.com/daiyafeigitee/fuhe.git`
- 自动编译前端并启动后端
- 自动放行防火墙端口，支持同一内网访问
- 默认使用 SQLite 数据库（不需要单独安装 MySQL）
- 自动处理端口占用（端口被占用会自动换可用端口）

## 你只需要做 3 步

1. 在 Windows 上把 `deploy_windows.ps1` 放到任意文件夹。
2. 以管理员身份打开 PowerShell。
3. 进入脚本所在目录，运行：

```powershell
.\deploy_windows.ps1
```

如果你有 `deploy_windows.bat`，也可以直接双击它。

## 默认安装位置

- 安装目录：`D:\fuhe_deploy`
- 项目目录：`D:\fuhe_deploy\fuhe`
- 下载缓存：`D:\fuhe_deploy\downloads`
- 数据库文件：`D:\fuhe_deploy\data\zyyz_fuping.db`

说明：如果电脑没有 D 盘，脚本会自动改用 `C:\fuhe_deploy`。

## 数据会不会丢

- 正常不会丢。
- SQLite 数据文件放在 `data` 目录，不在代码目录里。
- 以后重复执行一键部署，会更新程序，但会继续使用原数据库文件。

## 默认登录账号

- 账号：`admin`
- 密码：`admin123`

## 端口被占用怎么办

- 脚本优先使用：前端 `80`，后端 `8000`
- 如果被占用，脚本会自动切换到其他可用端口
- 部署完成后，窗口会打印“实际使用端口”和访问地址

## 部署完成后怎么访问

- 本机访问：看脚本最后输出的 `Local access`
- 内网访问：看脚本最后输出的 `LAN access`
- 接口文档：看脚本最后输出的 `Backend docs`

## 后续启动和停止

部署成功后会生成两个文件：

- 启动：`D:\fuhe_deploy\start_fuhe.bat`
- 停止：`D:\fuhe_deploy\stop_fuhe.bat`

以后重启系统后，双击 `start_fuhe.bat` 就能恢复服务。

## 常见问题

1. 运行脚本报权限问题：
请确认 PowerShell 是“以管理员身份运行”。

2. 其他电脑打不开：
先确认在同一个局域网，再使用脚本输出的 `LAN access` 地址访问。

3. 首次部署比较慢：
首次需要下载和安装软件，时间会长一些；再次部署会复用缓存，速度会更快。

## 可选参数（一般不用改）

```powershell
.\deploy_windows.ps1 -InstallRoot "D:\fuhe_deploy" -NginxPort 80 -BackendPort 8000
```
