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
利用ZoomEye的官方api，结合[开发文档](https://www.zoomeye.org/doc#user)，做了这么一个GUI界面的搜索器。目前支持查询`主机搜索`、`域名/IP`、`个人信息`

- 支持本地`access_token.txt`文件的读取(免登陆)
- 支持读取`config.json`文件进行登陆
- 支持GUI界面账号(邮箱)+密码登录和API-KEY登陆
- 查询显示结果仅为部分，完整内容保存至`指定文件`
- 支持查询用户个人信息

---
## 💡 使用方式
->Run  
- 填写当前目录的`config.json`文件进行登陆(优先读取`API-KEY`)  
- 或在GUI界面进行登陆

->Build
```
pip install -r requirements.txt
```
> Recommend Python version: 3.8+
---
## 💻 TODO List
- [x] 代码重构
- [x] 优化登陆模式
- [ ] 增加web应用搜索模块
- [ ] 增加多种结果导出模式
---
## 🏝 更新日志

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
![](pic/ThunderSearch.png)

![](https://serverless-page-bucket-lv779z7b-1307395653.cos-website.ap-shanghai.myqcloud.com/ThunderSearch/ThunderSearch_txt.png)
