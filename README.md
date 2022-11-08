# <h1 align="center" >ThunderSearch 闪电搜索器</h1>
<p align="center">
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/stars/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/releases"><img alt="ThunderSearch" src="https://img.shields.io/github/release/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/issues"><img alt="ThunderSearch" src="https://img.shields.io/github/issues/xzajyjs/ThunderSearch"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/followers/xzajyjs?color=red&label=Followers"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/ThunderSearch-green"></a>
</p>

## 🎸 Intro介绍 ([EN_README](README_EN.md))
ThunderSearch（闪电搜索器）是一款使用多个(目前支持Fofa、Zoomeye、360Quake，未来将支持Hunter、Shodan等)网络空间搜索引擎官方api开发的GUI界面的信息搜集工具。具体支持查询项[点此](Intro/Statistics.md)

- 支持通过通过图形化修改配置信息
- 支持账号密码和API-KEY登陆
- 支持多个网络资产搜索引擎
- 查询显示结果仅为部分，完整内容保存至`指定文件`或`数据库`
- 支持查询用户个人信息

---
## 💡 使用方式
### -> Run  
- 直接运行即可。每次通过GUI修改配置后务必`保存配置`
- Zoomeye支持两种登录方式(账户密码/API-KEY)，选其一即可，优先使用API-KEY登录。Fofa需同时填写邮箱和API-KEY。Quake仅需填写API-KEY

#### 配置文件`config.json`说明
```
"language": "ch"
"zoomeye_username": ""
"zoomeye_password": ""
"zoomeye_api": ""
"fofa_username": ""
"fofa_api": ""
"quake_api": ""
"file": ""
"host": ""
"port": ""
"database": ""
"username": ""
"password": ""
```

> 修改language的参数，可修改语言。目前支持：`ch`(中文), `en`(英文)

### -> Build
```
pip3 install -r requirements.txt
```
> Recommend Python version: 3.8+
---
## 📡 支持统计内容

[查看详情](Intro/Statistics.md)

---
## 💻 TODO List
- [x] 代码重构
- [x] 优化登陆模式
- [x] 增加web应用搜索模块
- [x] 增加多种结果导出模式
- [ ] 支持更多搜索引擎(目前支持Fofa、Zoomeye和Quake)，如Shodan、Hunter等
---
## 🏝 更新日志

[查看详情](Intro/Update.md)

---
## 🌏 效果演示
![](pic/fofa.png) 
![](pic/quake.png) 
![](pic/config.png)  
![](pic/mysql.png)  
![](pic/csv.png)