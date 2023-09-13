import os
import sys
import json
import ctypes
import sqlite3
import traceback

import pymysql
import requests
import tkinter as tk
from os import system
from threading import Thread
from tkinter import messagebox
from tkinter.ttk import Notebook, Treeview, Style

# zoomeye
import module.zoomeye.host_search as zoomeye_hostsearch
import module.zoomeye.domain_ip as zoomeye_domain_ip
import module.zoomeye.resource as zoomeye_resource
import module.zoomeye.web_search as zoomeye_websearch

# fofa
import module.fofa.search_all as fofa_search_all
import module.fofa.resource as fofa_resource

# quake
import module.quake.resource as quake_resource
import module.quake.host_search as quake_hostsearch
import module.quake.service_search as quake_servicesearch

# shodan
import module.shodan.search as shodan_search

# hunter
import module.hunter.search as hunter_search

VERSION = "v2.5.1"


class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.delete_access_token()
        self.createWidget()
        self.language = self.dic['language']
        self.setLanguage()
        self.pack(padx=0, pady=0, fill='both', expand=True)
        self.checkUpdate()

    def checkUpdate(self):
        url = "https://api.github.com/repos/xzajyjs/ThunderSearch/releases/latest"
        try:
            resp = requests.get(url, timeout=3).json()
            latest_version, latest_version_url = resp['name'], resp['html_url']
            if VERSION != latest_version:
                self.log_insert(f'[!] Update to new version {latest_version}: {latest_version_url}\n')
                return
        except Exception as e:
            if 'API rate limit' in resp['message']:
                self.log_insert("[!] CheckUpdate error: This IP has API limit.\n")
                return
            self.log_insert(f"[!] CheckUpdate error: {traceback.format_exc()}.\n")

    def createWidget(self):
        self.notebook = Notebook(self)
        self.search_frame = tk.Frame()
        self.config_frame = tk.Frame()
        self.help_frame = tk.Frame()
        self.notebook.add(self.search_frame, text='查询')
        self.notebook.add(self.config_frame, text='配置')
        self.notebook.add(self.help_frame, text='帮助')
        self.notebook.pack(padx=0, pady=0, fill='both', expand=True)

        self.initHelpFrame()
        self.initConfigFrame()
        self.initSearchFrame()

    def initSearchFrame(self):
        self.label_thread = tk.Label(self.search_frame, text='线程数:', width=6)
        self.label_thread.grid(row=0, column=0)
        self.thread_choice = tk.StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = tk.OptionMenu(self.search_frame, self.thread_choice, '1', '5', '10', '20', '30')
        self.THREAD.grid(row=0, column=1)
        self.label_page = tk.Label(self.search_frame, text='查询页数:')
        self.label_page.grid(row=0, column=2)
        self.page_choice = tk.StringVar(self)
        self.page_choice.set('1')
        self.PAGE = tk.OptionMenu(self.search_frame, self.page_choice, '1', '2', '3', '4', '5', '10', '15', '20', '30',
                                  '50', '80', '100', '200', '300', '500', '1000')
        self.PAGE.grid(row=0, column=3)
        self.label_mode = tk.Label(self.search_frame, text='模式:')
        self.label_mode.grid(row=0, column=4)

        self.mode_dict = {
            'Fofa': ['数据查询', '个人信息'],
            'Shodan': ['数据搜索'],
            'Hunter': ['数据搜索'],
            'Zoomeye': ['主机搜索', '域名/IP', 'web应用', '个人信息'],
            'Quake': ['主机搜索', '服务搜索', '个人信息']
        }

        self.query_mode_choice = tk.StringVar(self)
        self.MODE = tk.OptionMenu(self.search_frame, self.query_mode_choice, '')
        self.MODE.grid(row=0, column=5)

        self.search_engine_choice = tk.StringVar(self)
        self.search_engine_choice.trace('w', self.update_mode_menu)
        self.search_engine_choice.set('Fofa')

        self.label_saveMode = tk.Label(self.search_frame, text='存储模式:')
        self.label_saveMode.grid(row=0, column=6)
        self.save_mode_choice = tk.StringVar(self)
        self.save_mode_choice.set('不保存')
        self.SAVE_MODE = tk.OptionMenu(self.search_frame, self.save_mode_choice, '不保存', '存文件', 'mysql', 'sqlite')
        self.SAVE_MODE.grid(row=0, column=7)

        self.label_searchEngine = tk.Label(self.search_frame, text='搜索引擎:')
        self.label_searchEngine.grid(row=0, column=8)
        self.SEARCH_ENGINE = tk.OptionMenu(self.search_frame, self.search_engine_choice, *self.mode_dict.keys())
        self.SEARCH_ENGINE.grid(row=0, column=9)

        self.label_searchQuery = tk.Label(self.search_frame, text='查询语句:')
        self.label_searchQuery.grid(row=1, column=0)
        self.QUERY = tk.Entry(self.search_frame, width=60, borderwidth=1)
        self.QUERY.grid(row=1, column=1, columnspan=8, sticky=tk.EW)
        self.START = tk.Button(self.search_frame, text='查询', command=self.thread)
        self.START.grid(row=1, column=9)

        # windows hidpi treeview row_height
        multiple = 1 if "darwin" in sys.platform else 2
        if multiple == 2:
            Style().configure('Treeview', rowheight=40)
        self.TREEVIEW = Treeview(self.search_frame, show='headings')
        self.TREEVIEW.grid(row=3, column=0, columnspan=10, sticky=tk.NSEW)
        self.TREEVIEW['columns'] = ("ID", "IP", "PORT/DOMAIN", "OS", "TITLE")
        self.TREEVIEW.column("ID", width=50)
        self.TREEVIEW.column("IP", width=160)
        self.TREEVIEW.column("PORT/DOMAIN", width=235)
        self.TREEVIEW.column("OS", width=90)
        self.TREEVIEW.column("TITLE", width=200)
        self.TREEVIEW.heading("ID", text="ID")
        self.TREEVIEW.heading("IP", text="IP")
        self.TREEVIEW.heading("PORT/DOMAIN", text="PORT/DOMAIN")
        self.TREEVIEW.heading("OS", text="OS")
        self.TREEVIEW.heading("TITLE", text="TITLE")
        self.LOG = tk.Text(self.search_frame, relief=tk.SOLID, borderwidth=1, height=15, width=104, fg='gray')
        self.LOG.grid(row=4, column=0, columnspan=10, sticky=tk.EW)

        # 信息处理
        self.log_insert(
            f"@ Version: {VERSION}\n@ Author: xzajyjs\n@ E-mail: xuziang16@gmail.com\n@ Repo: https://github.com/xzajyjs/ThunderSearch\n")
        if not os.path.exists('config.json'):
            self.language = "ch"
            self.save_config()
        try:
            self.load_config()
        except Exception as e:
            messagebox.showerror(title='Error', message=f'Fail to load config.json, {e}')

        # 页面自适应
        for i in range(4):
            self.search_frame.rowconfigure(i + 1, weight=1)
        for j in range(9):
            self.search_frame.columnconfigure(j + 1, weight=1)

    def initConfigFrame(self):
        # zoomeye
        tk.Label(self.config_frame, text='Zoomeye', width=10).grid(row=0, column=1, sticky=tk.EW)
        self.label_zoomeyeUser = tk.Label(self.config_frame, text='账号:')
        self.label_zoomeyeUser.grid(row=1, column=0)
        self.label_zoomeyePass = tk.Label(self.config_frame, text='密码:')
        self.label_zoomeyePass.grid(row=2, column=0)
        tk.Label(self.config_frame, text='API-KEY:').grid(row=3, column=0)
        self.ZOOMEYE_USERNAME = tk.Entry(self.config_frame, width=24, borderwidth=1)
        self.ZOOMEYE_USERNAME.grid(row=1, column=1, sticky=tk.EW)
        self.ZOOMEYE_PASSWORD = tk.Entry(self.config_frame, width=24, show="*", borderwidth=1)
        self.ZOOMEYE_PASSWORD.grid(row=2, column=1, sticky=tk.EW)
        self.ZOOMEYE_API = tk.Entry(self.config_frame, width=24, borderwidth=1, show='*')
        self.ZOOMEYE_API.grid(row=3, column=1, sticky=tk.EW)

        # fofa
        tk.Label(self.config_frame, text='Fofa', width=10).grid(row=4, column=1, sticky=tk.EW)
        self.label_fofaEmail = tk.Label(self.config_frame, text='邮箱:')
        self.label_fofaEmail.grid(row=5, column=0)
        tk.Label(self.config_frame, text='API-KEY:').grid(row=6, column=0)
        self.FOFA_USERNAME = tk.Entry(self.config_frame, width=24, borderwidth=1)
        self.FOFA_USERNAME.grid(row=5, column=1, sticky=tk.EW)
        self.FOFA_API = tk.Entry(self.config_frame, width=24, borderwidth=1, show='*')
        self.FOFA_API.grid(row=6, column=1, sticky=tk.EW)

        # quake
        tk.Label(self.config_frame, text="360Quake").grid(row=7, column=1, sticky=tk.EW)
        tk.Label(self.config_frame, text="API-KEY").grid(row=8, column=0)
        self.QUAKE_API = tk.Entry(self.config_frame, width=24, show="*", borderwidth=1)
        self.QUAKE_API.grid(row=8, column=1, sticky=tk.EW)

        # shodan
        tk.Label(self.config_frame, text="Shodan").grid(row=9, column=1, sticky=tk.EW)
        tk.Label(self.config_frame, text="API-KEY").grid(row=10, column=0)
        self.SHODAN_API = tk.Entry(self.config_frame, width=24, show="*", borderwidth=1)
        self.SHODAN_API.grid(row=10, column=1, sticky=tk.EW)

        # hunter
        tk.Label(self.config_frame, text="Hunter").grid(row=11, column=1, sticky=tk.EW)
        tk.Label(self.config_frame, text="API-KEY").grid(row=12, column=0)
        self.HUNTER_API = tk.Entry(self.config_frame, width=24, show="*", borderwidth=1)
        self.HUNTER_API.grid(row=12, column=1, sticky=tk.EW)

        # 右侧配置
        self.label_fileConfig = tk.Label(self.config_frame, text='文件存储配置')
        self.label_fileConfig.grid(row=0, column=3, sticky=tk.EW)
        self.label_filePath = tk.Label(self.config_frame, text='文件路径')
        self.label_filePath.grid(row=1, column=2)
        self.label_dbConfig = tk.Label(self.config_frame, text='数据库配置(MySQL)')
        self.label_dbConfig.grid(row=2, column=3, sticky=tk.EW)
        self.label_dbHost = tk.Label(self.config_frame, text='主机')
        self.label_dbHost.grid(row=3, column=2)
        self.label_dbPort = tk.Label(self.config_frame, text='端口')
        self.label_dbPort.grid(row=4, column=2)
        self.label_dbName = tk.Label(self.config_frame, text='数据库名')
        self.label_dbName.grid(row=5, column=2)
        self.label_dbUser = tk.Label(self.config_frame, text='用户名')
        self.label_dbUser.grid(row=6, column=2)
        self.label_dbPass = tk.Label(self.config_frame, text='密码')
        self.label_dbPass.grid(row=7, column=2)
        self.label_sqliteConfig = tk.Label(self.config_frame, text='Sqlite配置')
        self.label_sqliteConfig.grid(row=8, column=3, sticky=tk.EW)
        self.label_sqlite = tk.Label(self.config_frame, text='Sqlite路径')
        self.label_sqlite.grid(row=9, column=2)
        self.label_otherConfig = tk.Label(self.config_frame, text='其他配置')
        self.label_otherConfig.grid(row=10, column=3, sticky=tk.EW)
        self.label_languageSet = tk.Label(self.config_frame, text='Language')
        self.label_languageSet.grid(row=11, column=2)

        self.FILE = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.FILE.grid(row=1, column=3, sticky=tk.EW)
        self.DATABASE_HOST = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.DATABASE_HOST.grid(row=3, column=3, sticky=tk.EW)
        self.DATABASE_PORT = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.DATABASE_PORT.grid(row=4, column=3, sticky=tk.EW)
        self.DATABASE_DATABASE = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.DATABASE_DATABASE.grid(row=5, column=3, sticky=tk.EW)
        self.DATABASE_USERNAME = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.DATABASE_USERNAME.grid(row=6, column=3, sticky=tk.EW)
        self.DATABASE_PASSWORD = tk.Entry(self.config_frame, width=30, borderwidth=1, show="*")
        self.DATABASE_PASSWORD.grid(row=7, column=3, sticky=tk.EW)
        self.SQLITE_FILENAME = tk.Entry(self.config_frame, width=30, borderwidth=1)
        self.SQLITE_FILENAME.grid(row=9, column=3, sticky=tk.EW)
        self.language_choice = tk.StringVar()
        # self.language_choice.set(self.dic['language'])
        self.LANGUAGE_BTN = tk.OptionMenu(self.config_frame, self.language_choice, 'ch', 'en')
        self.LANGUAGE_BTN.grid(row=11, column=3, sticky=tk.W)

        self.SAVE = tk.Button(self.config_frame, text='保存配置', command=self.save_config)
        self.SAVE.grid(row=3, column=4)
        self.LOAD = tk.Button(self.config_frame, text='读取配置', command=self.load_config)
        self.LOAD.grid(row=4, column=4)
        self.CLEAR = tk.Button(self.config_frame, text='清空配置', command=self.clear_config)
        self.CLEAR.grid(row=5, column=4)
        self.TESTDB = tk.Button(self.config_frame, text='数据库测试', command=self.db_test)
        self.TESTDB.grid(row=6, column=4)
        self.CLEARTOKEN = tk.Button(self.config_frame, text='清除token', command=self.delete_access_token)
        self.CLEARTOKEN.grid(row=7, column=4)

        self.config_frame.columnconfigure(1, weight=1)
        self.config_frame.columnconfigure(3, weight=1)

    def initHelpFrame(self):
        self.help_text = tk.Text(self.help_frame, relief=tk.SOLID, borderwidth=1, height=35, width=100, fg='gray')
        self.help_text.grid(row=0, column=0, sticky=tk.NSEW)
        text = """使用指南:
1.先填写配置选项卡中的选项(有选择性填写)
2.填写完配置请先点击保存
3.文件路径请填写绝对路径,如/Users/xxx/fofa.csv
4.查询页数在Fofa和Quake查询下乘以10即为查询数据条数
5.Shodan单页搜索为100条
6.Hunter单页搜索为20条
=============

Fofa语法
title="beijing" 从标题中搜索“北京"
header="elastic" 从http头中搜索“elastic"
body="网络空间测绘" 从html正文中搜索“网络空间测绘"
domain="qq.com" 搜索根域名带有qq.com的网站。
icon_hash="-247388890" 搜索使用此icon的资产。 仅限FOFA高级会员使用
host=".gov.cn" 从url中搜索".gov.cn" 搜索要用host作为名称
port="6379" 查找对应“6379"端口的资产
icp="京ICP证030173号" 查找备案号为“京ICP证030173号"的网站 搜索网站类型资产
ip="1.1.1.1" 从ip中搜索包含“1.1.1.1"的网站 搜索要用ip作为名称
ip="220.181.111.1/24" 查询IP为“220.181.111.1"的C网段资产
status_code="402" 查询服务器状态为“402"的资产
protocol="quic" 查询quic协议资产 搜索指定协议类型(在开启端口扫描的情况下有效)
country="CN" 搜索指定国家(编码)的资产。
region="HeNan" 搜索指定行政区的资产。
city="HanDan" 搜索指定城市的资产。
cert="baidu" 搜索证书(https或者imaps等)中带有baidu的资产。
cert.subject="Oracle Corporation" 搜索证书持有者是Oracle Corporation的资产
cert.issuer="DigiCert" 搜索证书颁发者为DigiCert Inc的资产
cert.is_valid=true 验证证书是否有效,true有效,false无效,仅限FOFA高级会员使用
banner=users && protocol=ftp 搜索FTP协议中带有users文本的资产。
type=service 搜索所有协议资产,支持subdomain和service两种。
os="centos" 搜索操作系统为CentOS资产。
server=="Microsoft-IIS/10" 搜索IIS 10服务器。
app="Microsoft-Exchange" 搜索Microsoft-Exchange设备
after="2017" && before="2017-10-01" 时间范围段搜索
asn="19551" 搜索指定asn的资产。
org="Amazon.com, Inc." 搜索指定org(组织)的资产。
base_protocol="udp" 搜索指定udp协议的资产。
is_fraud=false 排除仿冒/欺诈数据
is_honeypot=false 排除蜜罐数据,仅限FOFA高级会员使用
is_ipv6=true 搜索ipv6的资产,只接受true和false。
is_domain=true 搜索域名的资产,只接受true和false。
port_size="6" 查询开放端口数量等于"6"的资产,仅限FOFA会员使用
port_size_gt="6" 查询开放端口数量大于"6"的资产,仅限FOFA会员使用
port_size_lt="12" 查询开放端口数量小于"12"的资产,仅限FOFA会员使用
ip_ports="80,161" 搜索同时开放80和161端口的ip资产(以ip为单位的资产数据)
ip_country="CN" 搜索中国的ip资产(以ip为单位的资产数据)。
ip_region="Zhejiang" 搜索指定行政区的ip资产(以ip为单位的资产数据)。
ip_city="Hangzhou" 搜索指定城市的ip资产(以ip为单位的资产数据)。
ip_after="2021-03-18" 搜索2021-03-18以后的ip资产(以ip为单位的资产数据)。
ip_before="2019-09-09" 搜索2019-09-09以前的ip资产(以ip为单位的资产数据)。
============

Zoomeye语法
app:nginx　　           组件名
ver:1.0　　             版本
os:windows　　          操作系统
country:"China"　　     国家
city:"hangzhou"　　     城市
port:80　　             端口
hostname:google　　     主机名
site:thief.one　　      网站域名
desc:nmask　　          描述
keywords:nmask'blog　　 关键词
service:ftp　　         服务类型
ip:8.8.8.8　　          ip地址
cidr:8.8.8.8/24　　     ip地址段
city:"beijing" port:80 同时满足两个条件
============

Quake语法
https://quake.360.cn/quake/#/help?id=5eb238f110d2e850d5c6aec8&title=%E6%A3%80%E7%B4%A2%E5%85%B3%E9%94%AE%E8%AF%8D
============

Shodan语法
例如:product:"nginx" city:"Beijing" port:"8088"
https://www.shodan.io/search/filters
https://www.shodan.io/search/examples
============


Hunter语法
例如：domain.suffix="'qianxin.com" && title="北京"
https://hunter.qianxin.com/"""
        self.help_text.insert(tk.END, text)
        self.help_frame.rowconfigure(0, weight=1)
        self.help_frame.columnconfigure(0, weight=1)

    def setLanguage(self):
        if self.language == "en":
            # tab
            self.notebook.tab(0, text='Search')
            self.notebook.tab(1, text='Config')
            self.notebook.tab(2, text='Help')

            # search_tab
            self.label_thread['text'] = "Thread"
            self.label_mode['text'] = "Mode"
            self.label_page['text'] = "Page"
            self.label_saveMode['text'] = "SaveMode"
            self.label_searchEngine['text'] = "SearchEngine"
            self.label_searchQuery['text'] = "Query"
            self.START.configure(text='Search')
            self.mode_dict = {
                'Fofa': ['Data', 'Account'],
                'Shodan': ['Data'],
                'Hunter': ['Data'],
                'Zoomeye': ['HostSearch', 'Domain/IP', 'WebApp', 'Account'],
                'Quake': ['HostSearch', 'Service', 'Account']
            }
            self.update_mode_menu()
            self.save_mode_choice.set('NotSave')
            self.SAVE_MODE = tk.OptionMenu(self.search_frame, self.save_mode_choice, 'NotSave', 'File', 'mysql',
                                           'sqlite')
            self.SAVE_MODE.grid(row=0, column=7)

            # config_tab
            self.label_zoomeyeUser['text'] = "Account"
            self.label_zoomeyePass['text'] = "Password"
            self.label_fofaEmail['text'] = "E-mail"
            self.label_fileConfig['text'] = "Save File Config"
            self.label_filePath['text'] = "FilePath"
            self.label_dbConfig['text'] = "DB Config(MySQL)"
            self.label_dbHost['text'] = "Host"
            self.label_dbPort['text'] = "Port"
            self.label_dbName['text'] = "dbName"
            self.label_dbUser['text'] = "User"
            self.label_dbPass['text'] = "Pass"
            self.label_sqliteConfig['text'] = "SqliteConfig"
            self.label_sqlite['text'] = "SqlitePath"
            self.label_otherConfig['text'] = "OtherConfig"
            self.SAVE.configure(text='SaveConfig')
            self.LOAD.configure(text='LoadConfig')
            self.CLEAR.configure(text='ClearConfig')
            self.TESTDB.configure(text='TestDB')
            self.CLEARTOKEN.configure(text='ClearToken')
            self.language_choice.set('en')

            self.help_text.delete("1.0", "end")
            text_en = """Guidance:
1. First fill in the options in the configuration tab (fill in optional)
2. After filling in the configuration, please click Save first.
3. Please fill in the absolute path for the file path, such as /Users/xxx/fofa.csv
4. The number of query pages multiplied by 10 under Fofa and Quake queries is the number of query data items.
5.Shodan single page search is 100 items
6.Hunter single page search is 20 items
=============

Fofa syntax
title="beijing" Search "Beijing" from the title
header="elastic" Search for "elastic" from the http header
body="Cyberspace Surveying and Mapping" Search for "Cyberspace Surveying and Mapping" from the HTML text
domain="qq.com" searches for websites with the root domain name qq.com.
icon_hash="-247388890" Search for assets using this icon. Only available to FOFA premium members
host=".gov.cn" Search for ".gov.cn" from the url. Use host as the name for the search.
port="6379" Find assets corresponding to the "6379" port
icp="Beijing ICP Certificate No. 030173" Find the website with the registration number "Beijing ICP Certificate No. 030173" Search website type assets
ip="1.1.1.1" Search for websites containing "1.1.1.1" from ip. Use ip as the name when searching.
ip="220.181.111.1/24" Query the C network segment assets whose IP is "220.181.111.1"
status_code="402" Query the assets with server status "402"
protocol="quic" Query quic protocol assets and search for the specified protocol type (valid when port scanning is enabled)
country="CN" searches for assets in the specified country (code).
region="HeNan" searches for assets in the specified administrative region.
city="HanDan" searches for assets in the specified city.
cert="baidu" searches for assets with baidu in the certificate (https or imaps, etc.).
cert.subject="Oracle Corporation" Searches for certificate holders that are assets of Oracle Corporation
cert.issuer="DigiCert" searches for assets whose certificate issuer is DigiCert Inc.
cert.is_valid=true Verifies whether the certificate is valid, true is valid, false is invalid, only available to FOFA senior members
banner=users && protocol=ftp searches for assets with users text in the FTP protocol.
type=service searches all protocol assets, supporting both subdomain and service.
os="centos" searches operating systems for CentOS assets.
server=="Microsoft-IIS/10" searches for IIS 10 servers.
app="Microsoft-Exchange" Search for Microsoft-Exchange devices
after="2017" && before="2017-10-01" time range search
asn="19551" searches for assets with the specified asn.
org="Amazon.com, Inc." searches for assets of the specified org (organization).
base_protocol="udp" searches for assets with the specified udp protocol.
is_fraud=false excludes counterfeit/fraudulent data
is_honeypot=false excludes honeypot data, only available to FOFA premium members
is_ipv6=true searches for ipv6 assets and only accepts true and false.
is_domain=true searches domain name assets, only accepts true and false.
port_size="6" Query the assets with the number of open ports equal to "6", only available to FOFA members
port_size_gt="6" Query assets with open ports greater than "6", only available to FOFA members
port_size_lt="12" Query assets with open ports less than "12", only available to FOFA members
ip_ports="80,161" searches for ip assets that open ports 80 and 161 at the same time (asset data in ip units)
ip_country="CN" searches for China's IP assets (asset data in IP units).
ip_region="Zhejiang" searches for ip assets in the specified administrative region (asset data in ip units).
ip_city="Hangzhou" searches for ip assets in the specified city (asset data in ip units).
ip_after="2021-03-18" searches for ip assets after 2021-03-18 (asset data in ip units).
ip_before="2019-09-09" searches for ip assets before 2019-09-09 (asset data in ip units).
============

Zoomeye syntax
app:nginx　Component name
ver:1.0　Version
os:windows Operating system
country:"China" Country
city:"hangzhou" City
port:80　Port
hostname:google　 Hostname
site:thief.one　 Website domain name
desc:nmask　 Description
keywords:nmask'blog　 Keywords
service:ftp　 Service type
ip:8.8.8.8　 ip address
cidr:8.8.8.8/24　 IP address segment
city:"beijing" port:80 satisfies two conditions at the same time
============

Quake syntax
https://quake.360.cn/quake/#/help?id=5eb238f110d2e850d5c6aec8&title=%E6%A3%80%E7%B4%A2%E5%85%B3%E9%94%AE%E8%AF%8D
============

Shodan syntax
For example: product: "nginx" city: "Beijing" port: "8088"
https://www.shodan.io/search/filters
https://www.shodan.io/search/examples
============


Hunter Grammar
For example: domain.suffix="'qianxin.com" && title="Beijing"
https://hunter.qianxin.com/"""
            self.help_text.insert(tk.END, text_en)

        elif self.language == "ch":
            self.language_choice.set('ch')

    def update_mode_menu(self, *args):
        modes = self.mode_dict[self.search_engine_choice.get()]
        self.query_mode_choice.set(modes[0])
        menu = self.MODE['menu']
        menu.delete(0, 'end')
        for mode in modes:
            menu.add_command(label=mode, command=lambda mode=mode: self.query_mode_choice.set(mode))

    def _delete_config(self):  # 清空显示
        self.ZOOMEYE_USERNAME.delete(0, tk.END)
        self.ZOOMEYE_PASSWORD.delete(0, tk.END)
        self.ZOOMEYE_API.delete(0, tk.END)
        self.FOFA_USERNAME.delete(0, tk.END)
        self.FOFA_API.delete(0, tk.END)
        self.QUAKE_API.delete(0, tk.END)
        self.SHODAN_API.delete(0, tk.END)
        self.HUNTER_API.delete(0, tk.END)
        self.FILE.delete(0, tk.END)
        self.DATABASE_HOST.delete(0, tk.END)
        self.DATABASE_PORT.delete(0, tk.END)
        self.DATABASE_DATABASE.delete(0, tk.END)
        self.DATABASE_USERNAME.delete(0, tk.END)
        self.DATABASE_PASSWORD.delete(0, tk.END)
        self.SQLITE_FILENAME.delete(0, tk.END)

    def _insert_config(self):  # 插入数据
        self.ZOOMEYE_USERNAME.insert(tk.END, self.dic['zoomeye_username'])
        self.ZOOMEYE_PASSWORD.insert(tk.END, self.dic['zoomeye_password'])
        self.ZOOMEYE_API.insert(tk.END, self.dic['zoomeye_api'])
        self.FOFA_USERNAME.insert(tk.END, self.dic['fofa_username'])
        self.FOFA_API.insert(tk.END, self.dic['fofa_api'])
        self.QUAKE_API.insert(tk.END, self.dic['quake_api'])
        self.SHODAN_API.insert(tk.END, self.dic['shodan_api'])
        self.HUNTER_API.insert(tk.END, self.dic['hunter_api'])
        self.FILE.insert(tk.END, self.dic['file'])
        self.DATABASE_HOST.insert(tk.END, self.dic['host'])
        self.DATABASE_PORT.insert(tk.END, self.dic['port'])
        self.DATABASE_DATABASE.insert(tk.END, self.dic['database'])
        self.DATABASE_USERNAME.insert(tk.END, self.dic['username'])
        self.DATABASE_PASSWORD.insert(tk.END, self.dic['password'])
        self.SQLITE_FILENAME.insert(tk.END, self.dic['sqlitepath'])

    def _save_config(self):  # 保存数据
        self.dic = {
            'language': "en" if not os.path.exists('config.json') else self.language_choice.get(),
            'zoomeye_username': self.ZOOMEYE_USERNAME.get(),
            'zoomeye_password': self.ZOOMEYE_PASSWORD.get(),
            'zoomeye_api': self.ZOOMEYE_API.get(),
            'fofa_username': self.FOFA_USERNAME.get(),
            'fofa_api': self.FOFA_API.get(),
            'quake_api': self.QUAKE_API.get(),
            'shodan_api': self.SHODAN_API.get(),
            'hunter_api': self.HUNTER_API.get(),
            'file': self.FILE.get(),
            'host': self.DATABASE_HOST.get(),
            'port': self.DATABASE_PORT.get(),
            'database': self.DATABASE_DATABASE.get(),
            'username': self.DATABASE_USERNAME.get(),
            'password': self.DATABASE_PASSWORD.get(),
            'sqlitepath': self.SQLITE_FILENAME.get()
        }
        with open("config.json", "w", encoding='utf8') as f:
            json.dump(self.dic, f)

    def load_config(self):  # 读取配置
        with open("config.json", "r", encoding='utf8') as f:
            self.dic = json.load(f)
        self._delete_config()
        self._insert_config()

    def save_config(self):  # 保存配置
        try:
            self._save_config()
        except Exception as e:
            messagebox.showerror('Error', f'Fail to save。Info:{traceback.format_exc()}')
        else:
            messagebox.showinfo('Success', 'Success to save.\nIf you change Language, please restart the program.')

    def clear_config(self):
        self._delete_config()
        try:
            self._save_config()
        except Exception as e:
            messagebox.showerror("Error", traceback.format_exc())
        else:
            messagebox.showinfo("Success", "Success to clear.")

    def db_test(self):
        # mysql
        try:
            pymysql.connect(database=self.dic['database'], host=self.dic['host'], port=int(self.dic['port']),
                            user=self.dic['username'], password=self.dic['password'])
        except Exception as e:
            messagebox.showerror(title='Error', message=f'mysql数据库连接失败。 {e}')
        else:
            messagebox.showinfo(title='Success', message='mysql数据库连接成功')

        # sqlite
        try:
            if self.dic['sqlitepath'] == "":
                raise ValueError("Empty path for sqlite!")
            sqlite3.connect(self.dic['sqlitepath'])
        except Exception as e:
            messagebox.showerror(title='Error', message=f'sqlite数据库连接失败。 {e}')
        else:

            messagebox.showinfo(title='Success', message='sqlite数据库连接成功')

    def delete_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def delete_access_token(self):
        try:
            system(f"rm zoomeye_access_token.txt")
        except Exception as e:
            messagebox.showerror('Error', e)
            return None

    def log_insert(self, str):  # update log
        self.LOG.insert(tk.END, chars=str)
        self.LOG.see(tk.END)

    def login(self):
        if self.search_engine_choice.get() == "Zoomeye":
            # 1.查看是否存在zoomeye_access_token.txt
            if os.path.exists('zoomeye_access_token.txt'):
                with open("zoomeye_access_token.txt", "r", encoding="utf-8") as f:
                    access_token = f.read().strip('\n')
                self.zoomeye_headers = {
                    'Authorization': 'JWT ' + access_token
                }
                self.log_insert("[+] Load file 'access_token.txt' successfully.\n")
                self.log_insert(
                    f"[+] Access_Token: {self.zoomeye_headers['Authorization'][:7] + '*' * 10 + self.zoomeye_headers['Authorization'][-3:]}\n")
            # 2.通过api-key/username-password登录
            else:
                if self.dic['zoomeye_api'] != "":
                    self.zoomeye_api_key_login(self.dic['zoomeye_api'])
                elif self.dic['zoomeye_username'] != "" and self.dic['zoomeye_password'] != "":
                    self.zoomeye_user_pass_login(self.dic['zoomeye_username'], self.dic['zoomeye_password'])
                else:
                    messagebox.showerror(title='Error', message='请填写Zoomeye配置信息' if self.language == 'ch' else 'Please fill in Zoomeye config.')

    def zoomeye_api_key_login(self, api_key):
        self.zoomeye_headers = {
            "API-KEY": api_key
        }

    def zoomeye_user_pass_login(self, username, password):
        url = 'https://api.zoomeye.org/user/login'
        data = {
            'username': username,
            'password': password
        }
        encoded_data = json.dumps(data)
        resp_json = requests.post(url=url, data=encoded_data).json()
        # print(resp_json)
        try:
            access_token = resp_json['access_token']
        except:
            self.log_insert(f'[-] Login fail. {resp_json["message"]}. {resp_json["error"]}.\n')
        else:
            self.log_insert('[+] Login success!\n')
            with open("zoomeye_access_token.txt", "w", encoding="utf-8") as f:
                f.write(access_token)
            self.zoomeye_headers = {
                'Authorization': 'JWT ' + access_token
            }
            self.log_insert(
                f"[+] Access_Token: {self.zoomeye_headers['Authorization'][:7] + '*' * 10 + self.zoomeye_headers['Authorization'][-3:]}\n")

    def thread(self):
        if self.query_mode_choice.get() in ["个人信息", "Account"] or self.QUERY.get() != "":
            if self.save_mode_choice.get() == "mysql":
                try:
                    self.conn = pymysql.connect(database=self.dic['database'], host=self.dic['host'],
                                                port=int(self.dic['port']), user=self.dic['username'],
                                                password=self.dic['password'])
                except Exception as e:
                    messagebox.showerror(title='Error', message=f'[!] mysql数据库连接失败! {e}' if self.language == 'ch' else f'[!] Fail to connect to MySQL. {e}')
                    return
                else:
                    self.log_insert('[+] 数据库连接成功\n' if self.language == 'ch' else '[+] Connect to MySQL successfully.\n')
                    self.cursor = self.conn.cursor()
            elif self.save_mode_choice.get() in ["存文件", "File"] and self.FILE.get() == "":
                messagebox.showerror(title='Error', message='[!] 文件名为空!' if self.language == 'ch' else '[!] File name empty.')
                return
            t = Thread(target=self.run, daemon=True)
            t.start()
        else:
            messagebox.showerror(title='Error', message='[!] 查询语句为空!' if self.language == 'ch' else '[!] Query empty.')

    def run(self):
        if self.save_mode_choice.get() == "sqlite":
            try:
                self.sqlite_conn = sqlite3.connect(self.dic['sqlitepath'])
            except Exception as e:
                messagebox.showerror(title='Error', message=f'[!] Fail to connect to sqlite! {e}')
                return
            else:
                self.log_insert('[+] Success to connect to sqlite\n')
                self.sqlite_cursor = self.sqlite_conn.cursor()
        # zoomeye
        if self.search_engine_choice.get() == "Zoomeye":
            self.log_insert('[Zoomeye] Start searching...\n')
            if self.query_mode_choice.get() not in ['个人信息', 'Account']:
                self.delete_tree(self.TREEVIEW)
            self.login()
            query = self.QUERY.get().replace(" ", '%20')

            if self.query_mode_choice.get() in ['主机搜索', 'HostSearch']:
                zoomeye_hostsearch.headers = self.zoomeye_headers
                error_info = zoomeye_hostsearch.host_search(query=query, page=self.page_choice.get(),
                                                            thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_host_search(
                    ip text,port text,os text,app text,version text,title text,city text,country text,continents text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                        self.cursor.execute(
                            f'''INSERT INTO zoomeye_host_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists zoomeye_host_search(
                                        ip text,port text,os text,app text,version text,title text,city text,country text,continents text);''')
                    self.sqlite_conn.commit()
                    for each_dic in zoomeye_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO zoomeye_host_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}")''')
                        self.sqlite_conn.commit()
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write("ip,port,os,app,version,title,city,country,continents\n")
                        for each_dic in zoomeye_hostsearch.info_list:
                            self.TREEVIEW.insert("", tk.END, values=(
                                j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                            f.write(
                                f'''{each_dic["ip"]},{each_dic["port"]},{each_dic["os"]},{each_dic["app"]},{each_dic["version"]},{each_dic["title"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continents"]}\n''')
                            j += 1
                elif self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in zoomeye_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                        j += 1

            if self.query_mode_choice.get() in ['域名/IP', 'Domain/IP']:
                zoomeye_domain_ip.headers = self.zoomeye_headers
                error_info = zoomeye_domain_ip.domain_ip(query=query, page=self.page_choice.get(),
                                                         thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_domain_ip(
                    ip text,name text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_domain_ip.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['name'], None))
                        self.cursor.execute(
                            f'''INSERT INTO zoomeye_domain_ip VALUES("{each_dic['ip']}","{each_dic['name']}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists zoomeye_domain_ip(
                                        ip text,name text);''')
                    self.sqlite_conn.commit()
                    for each_dic in zoomeye_domain_ip.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['name'], None))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO zoomeye_domain_ip VALUES("{each_dic['ip']}","{each_dic['name']}")''')
                        self.sqlite_conn.commit()
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write("ip ,name\n")
                        for each_dic in zoomeye_domain_ip.info_list:
                            self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['name'], None))
                            f.write(f'''{str(each_dic["ip"])},{each_dic["name"]}\n''')
                            j += 1
                elif self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in zoomeye_domain_ip.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['name'], None))
                        j += 1

            if self.query_mode_choice.get() in ['web应用', 'WebApp']:
                zoomeye_websearch.headers = self.zoomeye_headers
                error_info = zoomeye_websearch.web_search(query=query, page=self.page_choice.get(),
                                                          thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_web_search(
                    ip text,site text,title text,city text,country text,continent text,isp text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_websearch.info_list:
                        self.TREEVIEW.insert("", tk.END,
                                             values=(j, each_dic['ip'], each_dic['site'], '', each_dic['title']))
                        self.cursor.execute(
                            f'''INSERT INTO zoomeye_web_search VALUES("{each_dic["ip"]}","{each_dic["site"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continent"]}","{each_dic['isp']}");''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists zoomeye_web_search(
                    ip text,site text,title text,city text,country text,continent text,isp text);''')
                    self.sqlite_conn.commit()
                    for each_dic in zoomeye_websearch.info_list:
                        self.TREEVIEW.insert("", tk.END,
                                             values=(j, each_dic['ip'], each_dic['site'], '', each_dic['title']))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO zoomeye_web_search VALUES("{each_dic["ip"]}","{each_dic["site"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continent"]}","{each_dic['isp']}");''')
                        self.sqlite_conn.commit()
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write("ip ,site ,title ,city ,country ,continents, isp\n")
                        for each_dic in zoomeye_websearch.info_list:
                            self.TREEVIEW.insert("", tk.END,
                                                 values=(j, each_dic['ip'], each_dic['site'], '', each_dic['title']))
                            f.write(
                                f'''{each_dic["ip"]},{each_dic["site"]},{each_dic["title"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continent"]},{each_dic['isp']}\n''')
                            j += 1
                elif self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in zoomeye_websearch.info_list:
                        self.TREEVIEW.insert("", tk.END,
                                             values=(j, each_dic['ip'], each_dic['site'], '', each_dic['title']))
                        j += 1

            zoomeye_resource.headers = self.zoomeye_headers
            if self.query_mode_choice.get() in ['个人信息', 'Account']:
                self.log_insert(zoomeye_resource.resource(mode="complete"))
            else:
                self.log_insert(
                    f'[Zoomeye] End of search. Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
                self.log_insert(zoomeye_resource.resource(mode="easy"))

        # fofa
        elif self.search_engine_choice.get() == "Fofa":
            self.log_insert('[Fofa] Start searching...\n')
            if self.query_mode_choice.get() in ["个人信息", "Account"]:
                text = fofa_resource.fofa_search_resource(email=self.dic['fofa_username'], key=self.dic['fofa_api'])
                self.log_insert(text)
            else:
                self.delete_tree(self.TREEVIEW)
                error_info = fofa_search_all.fofa_search(email=self.dic['fofa_username'], key=self.dic['fofa_api'],
                                                         query=str(self.QUERY.get()),
                                                         size=int(self.page_choice.get()) * 10)
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                for each_dic in fofa_search_all.info_list:
                    self.TREEVIEW.insert("", tk.END, values=(
                        j, each_dic['ip'], each_dic['port'] + "/" + each_dic['domain'], each_dic['os'],
                        each_dic['title']))
                    j += 1
                if self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists fofa_search_all(
                    ip text,port text,host text,domain text,os text,server text,title text,protocol text,country_name text,region text,city text,as_organization text,icp text,jarm text);''')
                    self.conn.commit()
                    for each in fofa_search_all.info_list:
                        self.cursor.execute(f'''insert into fofa_search_all values(
                            "{each['ip']}","{each['port']}","{each['host']}","{each['domain']}","{each['os']}","{each['server']}","{each['title']}","{each['protocol']}","{each['country_name']}","{each['region']}","{each['city']}","{each['as_organization']}","{each['icp']}","{each['jarm']}"
                        )''')
                        self.conn.commit()
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists fofa_search_all(
                                   ip text,port text,host text,domain text,os text,server text,title text,protocol text,country_name text,region text,city text,as_organization text,icp text,jarm text);''')
                    self.sqlite_conn.commit()
                    for each in fofa_search_all.info_list:
                        self.sqlite_cursor.execute(f'''insert into fofa_search_all values(
                                           "{each['ip']}","{each['port']}","{each['host']}","{each['domain']}","{each['os']}","{each['server']}","{each['title']}","{each['protocol']}","{each['country_name']}","{each['region']}","{each['city']}","{each['as_organization']}","{each['icp']}","{each['jarm']}"
                                       )''')
                        self.sqlite_conn.commit()
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write(
                            "ip,port,host,domain,os,server,title,protocol,country_name,region,city,as_organization,icp,jarm\n")
                        for each_dic in fofa_search_all.info_list:
                            f.write(
                                f"{each_dic['ip']},{each_dic['port']},{each_dic['host']},{each_dic['domain']},{each_dic['os']},{each_dic['server']},{each_dic['title']},{each_dic['protocol']},{each_dic['country_name']},{each_dic['region']},{each_dic['city']},{each_dic['as_organization']},{each_dic['icp']},{each_dic['jarm']}\n")
                elif self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    pass
                self.log_insert(
                    f'[Fofa] End of Search. Obtain totally {fofa_search_all.total_num}\nComplete information has been stored by mode "{self.save_mode_choice.get()}".\n')

        # quake
        elif self.search_engine_choice.get() == "Quake":
            self.log_insert('[Quake] Start searching...\n')
            query = self.QUERY.get()
            if self.query_mode_choice.get() not in ['个人信息', 'Account']:
                self.delete_tree(self.TREEVIEW)
            if self.query_mode_choice.get() in ["主机搜索", "HostSearch"]:
                error_info = quake_hostsearch.quake_host_search(query=query, page=self.page_choice.get(),
                                                                key=self.dic['quake_api'])
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in quake_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write(
                            "ip,service_port,service_name,service_version,service_id,domains,hostname,os_name,os_version,country_en,city_en\n")
                        for each_dic in quake_hostsearch.info_list:
                            f.write(
                                f'''{each_dic['ip']},{each_dic['service_port']},{each_dic['service_name']},{each_dic['service_version']},{each_dic['service_id']},{each_dic['domains']},{each_dic['hostname']},{each_dic['os_name']},{each_dic['os_version']},{each_dic['country_en']},{each_dic['city_en']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(
                                j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                            j += 1
                elif self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists quake_host_search(
                    ip text,service_port text,service_name text,service_version text,service_id text,domains text,hostname text,os_name text,os_version text,country_en text,city_en text);''')
                    self.conn.commit()
                    for each_dic in quake_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                        self.cursor.execute(
                            f'''INSERT INTO quake_host_search VALUES("{each_dic["ip"]}","{each_dic["service_port"]}","{each_dic["service_name"]}","{each_dic["service_version"]}","{each_dic["service_id"]}","{each_dic["domains"]}","{each_dic["hostname"]}","{each_dic["os_name"]}","{each_dic["os_version"]}","{each_dic["country_en"]}","{each_dic["city_en"]}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists quake_host_search(
                    ip text,service_port text,service_name text,service_version text,service_id text,domains text,hostname text,os_name text,os_version text,country_en text,city_en text);''')
                    self.sqlite_conn.commit()
                    for each_dic in quake_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO quake_host_search VALUES("{each_dic["ip"]}","{each_dic["service_port"]}","{each_dic["service_name"]}","{each_dic["service_version"]}","{each_dic["service_id"]}","{each_dic["domains"]}","{each_dic["hostname"]}","{each_dic["os_name"]}","{each_dic["os_version"]}","{each_dic["country_en"]}","{each_dic["city_en"]}")''')
                        self.sqlite_conn.commit()
                        j += 1
            if self.query_mode_choice.get() in ["服务搜索", "Service"]:
                error_info = quake_servicesearch.quake_service_search(query=query, page=self.page_choice.get(),
                                                                      key=self.dic['quake_api'])
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in quake_servicesearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write(
                            "ip,port,org,hostname,service_title,service_server,transport,os_name,os_version,service_name,country_en,city_en\n")
                        for each_dic in quake_servicesearch.info_list:
                            f.write(
                                f'''{each_dic['ip']},{each_dic['port']},{each_dic['org']},{each_dic['hostname']},{each_dic['service_title']},{each_dic['service_server']},{each_dic['transport']},{each_dic['os_name']},{each_dic['os_version']},{each_dic['service_name']},{each_dic['country_en']},{each_dic['city_en']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(
                                j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                            j += 1
                elif self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists quake_service_search(
                    ip text,port text,org text,hostname text,service_title text,service_server text,transport text,os_name text,service_name text,country_en text,city_en text,os_version text);''')
                    self.conn.commit()
                    for each_dic in quake_servicesearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                        self.cursor.execute(
                            f'''INSERT INTO quake_service_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["org"]}","{each_dic["hostname"]}","{each_dic["service_title"]}","{each_dic["service_server"]}","{each_dic["transport"]}","{each_dic["os_name"]}","{each_dic["service_name"]}","{each_dic["country_en"]}","{each_dic["city_en"]}","{each_dic["os_version"]}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists quake_service_search(
                    ip text,port text,org text,hostname text,service_title text,service_server text,transport text,os_name text,service_name text,country_en text,city_en text,os_version text);''')
                    self.sqlite_conn.commit()
                    for each_dic in quake_servicesearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO quake_service_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["org"]}","{each_dic["hostname"]}","{each_dic["service_title"]}","{each_dic["service_server"]}","{each_dic["transport"]}","{each_dic["os_name"]}","{each_dic["service_name"]}","{each_dic["country_en"]}","{each_dic["city_en"]}","{each_dic["os_version"]}")''')
                        self.sqlite_conn.commit()
                        j += 1
            if self.query_mode_choice.get() in ['个人信息', 'Account']:
                text = quake_resource.quake_resource_search(key=self.dic['quake_api'], mode="complete")
                self.log_insert(text)
            else:
                self.log_insert(
                    f'[Quake] End of search. Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
                self.log_insert(quake_resource.quake_resource_search(key=self.dic['quake_api'], mode="easy"))

        # Shodan
        elif self.search_engine_choice.get() == "Shodan":
            self.delete_tree(self.TREEVIEW)
            self.log_insert('[Shodan] Start searching...\n')
            query = self.QUERY.get()
            if self.query_mode_choice.get() in ["数据搜索", "Data"]:
                error_info = shodan_search.search(key=self.dic['shodan_api'], query=str(query),
                                                  page=self.page_choice.get())
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in shodan_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domains']), each_dic['os'],
                            each_dic['title']))
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write(
                            "ip,port,domains,title,product,os,info,isp,country,city,timestamp\n")
                        for each_dic in shodan_search.info_list:
                            f.write(
                                f'''{each_dic['ip']},{each_dic['port']},{each_dic['domains']},{each_dic['title']},{each_dic['product']},{each_dic['os']},{each_dic['info']},{each_dic['isp']},{each_dic['country']},{each_dic['city']},{each_dic['timestamp']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(
                                j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domains']),
                                each_dic['os'],
                                each_dic['title']))
                            j += 1
                elif self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists shodan_search(
                    ip text,port text,domains text,title text,product text,os text,info text,isp text,country text,city text,timestamp text);''')
                    self.conn.commit()
                    for each_dic in shodan_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domains']), each_dic['os'],
                            each_dic['title']))
                        self.cursor.execute(
                            f'''INSERT INTO shodan_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["domains"]}","{each_dic["title"]}","{each_dic["product"]}","{each_dic["os"]}","{each_dic["info"]}","{each_dic["isp"]}","{each_dic["country"]}","{each_dic["city"]}","{each_dic["timestamp"]}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists shodan_search(
                    ip text,port text,domains text,title text,product text,os text,info text,isp text,country text,city text,timestamp text);''')
                    self.sqlite_conn.commit()
                    for each_dic in shodan_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domains']), each_dic['os'],
                            each_dic['title']))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO shodan_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["domains"]}","{each_dic["title"]}","{each_dic["product"]}","{each_dic["os"]}","{each_dic["info"]}","{each_dic["isp"]}","{each_dic["country"]}","{each_dic["city"]}","{each_dic["timestamp"]}")''')
                        self.sqlite_conn.commit()
                        j += 1

                self.log_insert(
                    f'[Shodan] End of search. Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')

        # Hunter
        elif self.search_engine_choice.get() == "Hunter":
            self.delete_tree(self.TREEVIEW)
            self.log_insert('[Hunter] Start searching...\n')
            query = self.QUERY.get()
            if self.query_mode_choice.get() in ["数据搜索", "Data"]:
                error_info = hunter_search.search(key=self.dic['hunter_api'], query=str(query),
                                                  page=self.page_choice.get())
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() in ["不保存", "NotSave"]:
                    for each_dic in hunter_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domain']), each_dic['os'],
                            each_dic['web_title']))
                        j += 1
                elif self.save_mode_choice.get() in ["存文件", "File"]:
                    with open(self.FILE.get(), "w", encoding="utf-8") as f:
                        f.write(
                            "url,ip,port,web_title,domain,is_risk_protocol,protocol,base_protocol,status_code,component,os,company,number,country,province,city,updated_at,is_web,as_org,isp,vul_list,is_risk\n")
                        for each_dic in hunter_search.info_list:
                            f.write(
                                f'''{each_dic['url']},{each_dic['ip']},{each_dic['port']},{each_dic['web_title']},{each_dic['domain']},{each_dic['is_risk_protocol']},{each_dic['protocol']},{each_dic['base_protocol']},{each_dic['status_code']},{each_dic['component']},{each_dic['os']},{each_dic['company']},{each_dic['number']},{each_dic['country']},{each_dic['province']},{each_dic['city']},{each_dic['updated_at']},{each_dic['is_web']},{each_dic['as_org']},{each_dic['isp']},{each_dic['vul_list']},{each_dic['is_risk']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(
                                j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domain']),
                                each_dic['os'],
                                each_dic['web_title']))
                            j += 1
                elif self.save_mode_choice.get() == "mysql":
                    self.cursor.execute('''CREATE TABLE if not exists hunter_search(
                    url text, ip text, port text, web_title text, domain text, is_risk_protocol text, protocol text, base_protocol text, status_code text, component text, os text, company text, number text, country text, province text, city text, updated_at text, is_web text, as_org text, isp text, vul_list text, is_risk text);''')
                    self.conn.commit()
                    for each_dic in hunter_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domain']), each_dic['os'],
                            each_dic['web_title']))
                        self.cursor.execute(
                            f'''INSERT INTO hunter_search VALUES("{each_dic['url']}","{each_dic['ip']}","{each_dic['port']}","{each_dic['web_title']}","{each_dic['domain']}","{each_dic['is_risk_protocol']}","{each_dic['protocol']}","{each_dic['base_protocol']}","{each_dic['status_code']}","{each_dic['component']}","{each_dic['os']}","{each_dic['company']}","{each_dic['number']}","{each_dic['country']}","{each_dic['province']}","{each_dic['city']}","{each_dic['updated_at']}","{each_dic['is_web']}","{each_dic['as_org']}","{each_dic['isp']}","{each_dic['vul_list']}","{each_dic['is_risk']}")''')
                        self.conn.commit()
                        j += 1
                elif self.save_mode_choice.get() == "sqlite":
                    self.sqlite_cursor.execute('''CREATE TABLE if not exists hunter_search(
                    url text, ip text, port text, web_title text, domain text, is_risk_protocol text, protocol text, base_protocol text, status_code text, component text, os text, company text, number text, country text, province text, city text, updated_at text, is_web text, as_org text, isp text, vul_list text, is_risk);''')
                    self.sqlite_conn.commit()
                    for each_dic in hunter_search.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(
                            j, each_dic['ip'], str(each_dic['port']) + "/" + str(each_dic['domain']), each_dic['os'],
                            each_dic['web_title']))
                        self.sqlite_cursor.execute(
                            f'''INSERT INTO hunter_search VALUES("{each_dic['url']}","{each_dic['ip']}","{each_dic['port']}","{each_dic['web_title']}","{each_dic['domain']}","{each_dic['is_risk_protocol']}","{each_dic['protocol']}","{each_dic['base_protocol']}","{each_dic['status_code']}","{each_dic['component']}","{each_dic['os']}","{each_dic['company']}","{each_dic['number']}","{each_dic['country']}","{each_dic['province']}","{each_dic['city']}","{each_dic['updated_at']}","{each_dic['is_web']}","{each_dic['as_org']}","{each_dic['isp']}","{each_dic['vul_list']}","{each_dic['is_risk']}")''')
                        self.sqlite_conn.commit()
                        j += 1
            self.log_insert(
                f'[Hunter] End of search. Totally {hunter_search.other_info["total"]} results on Hunter. Complete information has been stored by mode "{self.save_mode_choice.get()}". Consume {hunter_search.other_info["consume_quota"]} points, {hunter_search.other_info["rest_quota"]} points remaining today.\n')


if __name__ == '__main__':
    root = tk.Tk()
    if "darwin" in sys.platform:
        root.geometry('793x526+320+100')
    else:
        # HiDPI
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        root.tk.call('tk', 'scaling', ScaleFactor / 75)
    root.resizable(True, False)
    root.title(f'ThunderSearch {VERSION}  --xzajyjs')
    Application(master=root)
    root.mainloop()
