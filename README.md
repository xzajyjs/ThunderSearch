# <h1 align="center" >ThunderSearch 闪电搜索器</h1>
<p align="center">
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/stars/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/releases"><img alt="ThunderSearch" src="https://img.shields.io/github/release/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/issues"><img alt="ThunderSearch" src="https://img.shields.io/github/issues/xzajyjs/ThunderSearch"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/followers/xzajyjs?color=red&label=Followers"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/ThunderSearch-green"></a>
</p>

## 🎸 Intro介绍
ThunderSearch（闪电搜索器）是一款使用多个(暂时支持Fofa和Zoomeye，未来将支持Hunter、360Quake、Shodan等)网络空间搜索引擎官方api开发的GUI界面的信息搜集工具。支持查询`主机搜索`、`域名/IP`、`web应用搜索`、`个人信息`

- 支持通过通过图形化修改配置信息
- 支持账号密码和API-KEY登陆
- 支持多个网络资产搜索引擎
- 查询显示结果仅为部分，完整内容保存至`指定文件`或`数据库`
- 支持查询用户个人信息

---
## 💡 使用方式
### -> Run  
- 直接运行即可。每次通过GUI修改配置后务必`保存配置`
- Zoomeye支持两种登录方式(账户密码/API-KEY)，选其一即可，优先使用API-KEY登录。Fofa需同时填写邮箱和API-KEY

#### 配置文件`config.json`说明
```
"zoomeye_username": ""
"zoomeye_password": ""
"zoomeye_api": ""
"fofa_username": ""
"fofa_api": ""
"file": ""
"host": ""
"port": ""
"database": ""
"username": ""
"password": ""
```

### -> Build
```
pip install -r requirements.txt
```
> Recommend Python version: 3.8+
---
## 📡 支持统计内容
### Zoomeye
#### 主机搜索
| 统计项 | 类型 | 说明 |
| :-----: | :----: | :----: |
| ip | string | ip地址 |
| port | string | 端口 |
| os | string | 操作系统 |
| app | string | 应用、设备等 |
| version | string | 应用版本号 |
| title | string | 标题 |
| city | string | 城市 |
| country | string | 国家 |
| continents | string | 大洲 |

#### 域名/IP
| 统计项 | 类型 | 说明 |
| :-----: | :----: | :----: |
| ip | string | ip地址 |
| name | string | 域名 |

#### web应用搜索
| 统计项 | 类型 | 说明 |
| :-----: | :----: | :----: |
| ip | string | ip地址 |
| site | string | 站点 |
| title | string | 网站标题 |
| city | string | 城市 |
| country | string | 国家 |
| continent | string | 大洲 |
| isp | string | 网络服务提供商 |

---

### Fofa
| 统计项 | 类型 | 说明 |
| :-----: | :----: | :----: |
| ip | string | ip地址 |
| port | string | 端口 |
| protocol | string | 协议名 |
| country_name | string | 国家名 |
| region | string | 地区 |
| city | string | 城市 |
| as_organization | string | asn组织 |
| host | string | 主机名 |
| domain | string | 域名 |
| os | string | 操作系统 |
| server | string | 网站server |
| icp | string | icp备案号 |
| title | string | 网站标题 |
| jarm | string | jarm指纹 |

---
## 💻 TODO List
- [x] 代码重构
- [x] 优化登陆模式
- [x] 增加web应用搜索模块
- [x] 增加多种结果导出模式
- [ ] 支持更多搜索引擎(目前支持Fofa和Zoomeye)，如Shodan、Hunter、Quake等
---
## 🏝 更新日志
#### v2.2
- 增加Fofa搜索
- 优化了Zoomeye的部分搜索结果
- 增加了帮助标签页
- 调整了UI布局

#### v2.0
- 优化配置设置
- 全新界面
- 支持Fofa(即将开放)

#### v1.7.6
- 增加数据不保存模式

#### v1.7.5
- 增加web应用搜索
- 增加导出至mysql数据库
- 加入更多查询内容

#### v1.7
- 代码重构
- 优化登陆逻辑
- 修复bug

#### v1.6
- 增加读取json文件登陆
- 修改敏感信息为隐式显示
- 优化登陆逻辑

#### v1.5.1
- 修复致命bug(**建议更新至此版本及更新**)
- 增加API-KEY登陆
- 调整界面布局

#### v1.3
- 增加个人信息查询模式
- 设置界面不可缩放
- 汉化了模式选择菜单
> 注：从此版本后将不再发布windows打包版本

#### v1.2
- 新增域名/ip互查
- 修复二次查询后结果不清空的bug
- 调整界面布局

#### v1.0
- 多线程支持

---
## 🌏 效果演示
![](pic/fofa.png)  
![](pic/config.png)  
![](pic/mysql.png)  
![](pic/csv.png)