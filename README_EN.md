# <h1 align="center" >ThunderSearch</h1>
<p align="center">
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/stars/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/releases"><img alt="ThunderSearch" src="https://img.shields.io/github/release/xzajyjs/ThunderSearch.svg"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch/issues"><img alt="ThunderSearch" src="https://img.shields.io/github/issues/xzajyjs/ThunderSearch"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/python-3.8+-blue"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/github/followers/xzajyjs?color=red&label=Followers"></a>
    <a href="https://github.com/xzajyjs/ThunderSearch"><img alt="ThunderSearch" src="https://img.shields.io/badge/ThunderSearch-green"></a>
</p>

## 🎸 Intro ([CN_README](README.md))
ThunderSearch is an information collection tool with GUI interface developed using the official api of multiple cyberspace search engines(Including `Fofa`, `Shodan`, `Hunter`, `Zoomeye`, `Quake`). Specific support query items [click here](Intro/Statistics.md).

- Support for modifying configuration information through graphics
- Support account password and API-KEY login
- Supports multiple cyberspace search engines
- The query display result is only partial, and the complete content is saved to the `specified file` or `database`
- Support query user personal information

---
## 💡 Usage
### -> Run  
- Just run the packaged application。Remember to click the button `SaveConfig`
- Zoomeye supports two ways to login(Acc and Pass/API-KEY), just choose one of them is OK. Use API-KEY to log in first. Fofa needs to fill in the E-mail and API-KEY at the same time. Quake only needs to fill in the API-KEY.

#### `config.json`
```
"language": "ch"
"zoomeye_username": ""
"zoomeye_password": ""
"zoomeye_api": ""
"fofa_username": ""
"fofa_api": ""
"quake_api": ""
"shodan_api": ""
"hunter_api": ""
"file": ""
"host": ""
"port": ""
"database": ""
"username": ""
"password": ""
```

> Modify the language through the `Language` option in the interface. At the same time, the value of `language` can also be modified by modifying the language parameter. You can change language from `ch`(Chinese) to `en`(English).

### -> Build and Run
```
pip3 install -r requirements.txt
python3 ThunderSearch.py
```
> Recommend Python version: 3.8+
---
## 📡 Statistical content

[For details](Intro/Statistics.md)

---

## 🏝 Update Log

[For details](Intro/Update_EN.md)

---
## 🌏 Screenshots
![](pic/fofa.png) 
![](pic/quake.png) 
![](pic/shodan.jpg)
![](pic/hunter.jpg)
![](pic/config.jpg)  
![](pic/mysql.png)  
![](pic/csv.png)