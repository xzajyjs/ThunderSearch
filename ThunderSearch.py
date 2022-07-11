import json
import requests
import pymysql
import os
from os import system
from tkinter import *
from threading import Thread
from tkinter import messagebox
from tkinter.ttk import Notebook, Treeview

import module.zoomeye.host_search as hs
import module.zoomeye.domain_ip as di
import module.zoomeye.resource as res
import module.zoomeye.web_search as ws

import module.fofa.search_all as fofa_search_all
import module.fofa.resource as fofa_resource

VERSION = "v2.2"

class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.delete_access_token()
        self.createWidget()
        self.pack()
        
    def createWidget(self):
        notebook = Notebook(self)
        search_frame = Frame()
        config_frame = Frame()
        help_frame = Frame()
        notebook.add(search_frame, text='查询')
        notebook.add(config_frame, text='配置')
        notebook.add(help_frame, text='帮助')
        notebook.grid(row=0,column=0,columnspan=20)

        # help_frame
        help_text = Text(help_frame,relief=SOLID,borderwidth=1,height=35,width=100,fg='gray')
        help_text.grid(row=0,column=0)
        text = """使用指南:
1.先填写配置选项卡中的选项(可有选择性填写)
2.填写完配置请先点击保存
3.文件路径请填写绝对路径,如/Users/xxx/fofa.csv
4.线程数仅对zoomeye查询有效
5.查询页数在fofa查询下乘以10即为查询数据条数
6.查询模式除个人信息选项外,其余仅适用于zoomeye。当选中非个人信息时才可正常使用fofa进行查询
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
city:"beijing" port:80 同时满足两个条件"""
        help_text.insert(END,text)


        # config_frame

        # zoomeye
        Label(config_frame,text='Zoomeye',width=10).grid(row=0,column=0,columnspan=2)
        Label(config_frame, text='账号:').grid(row=1,column=0)
        Label(config_frame, text='密码:').grid(row=2,column=0)
        Label(config_frame,text='API-KEY:').grid(row=3,column=0)
        self.ZOOMEYE_USERNAME = Entry(config_frame,width=24,borderwidth=1)
        self.ZOOMEYE_USERNAME.grid(row=1,column=1)
        self.ZOOMEYE_PASSWORD = Entry(config_frame,width=24,show="*",borderwidth=1)
        self.ZOOMEYE_PASSWORD.grid(row=2,column=1)
        self.ZOOMEYE_API = Entry(config_frame,width=24,borderwidth=1,show='*')
        self.ZOOMEYE_API.grid(row=3,column=1)

        # fofa
        Label(config_frame,text='Fofa',width=10).grid(row=5,column=0,columnspan=2)
        Label(config_frame, text='邮箱:').grid(row=6,column=0)
        Label(config_frame,text='API-KEY:').grid(row=7,column=0)
        self.FOFA_USERNAME = Entry(config_frame,width=24,borderwidth=1)
        self.FOFA_USERNAME.grid(row=6,column=1)
        self.FOFA_API = Entry(config_frame,width=24,borderwidth=1,show='*')
        self.FOFA_API.grid(row=7,column=1)

        # 右侧配置
        Label(config_frame, text='其他配置').grid(row=0,column=2,columnspan=2)
        Label(config_frame,text='文件路径').grid(row=1,column=2)
        Label(config_frame, text='数据库配置').grid(row=2,column=2,columnspan=2)
        Label(config_frame,text='主机').grid(row=3,column=2)
        Label(config_frame,text='端口').grid(row=4,column=2)
        Label(config_frame,text='数据库名').grid(row=5,column=2)
        Label(config_frame,text='用户名').grid(row=6,column=2)
        Label(config_frame,text='密码').grid(row=7,column=2)
        self.FILE = Entry(config_frame, width=30,borderwidth=1)
        self.FILE.grid(row=1,column=3)
        self.DATABASE_HOST = Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_HOST.grid(row=3,column=3)
        self.DATABASE_PORT = Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_PORT.grid(row=4,column=3)
        self.DATABASE_DATABASE = Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_DATABASE.grid(row=5,column=3)
        self.DATABASE_USERNAME = Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_USERNAME.grid(row=6,column=3)
        self.DATABASE_PASSWORD = Entry(config_frame, width=30,borderwidth=1,show="*")
        self.DATABASE_PASSWORD.grid(row=7,column=3)


        self.SAVE = Button(config_frame, text='保存配置', command=self.save_config)
        self.SAVE.grid(row=3,column=4)
        self.LOAD = Button(config_frame, text='读取配置', command=self.load_config)
        self.LOAD.grid(row=4,column=4)
        self.LOAD = Button(config_frame, text='数据库测试', command=self.db_test)
        self.LOAD.grid(row=5,column=4)
        self.SAVE = Button(config_frame, text='清除token', command=self.delete_access_token)
        self.SAVE.grid(row=6,column=4)


        # search_frame
        Label(search_frame, text='线程数:',width=6).grid(row=0,column=0)
        self.thread_choice = StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = OptionMenu(search_frame,self.thread_choice,'1','5','10','20','30')
        self.THREAD.grid(row=0,column=1)
        Label(search_frame,text='查询页数:').grid(row=0,column=2)
        self.page_choice = StringVar(self)
        self.page_choice.set('1')
        self.PAGE = OptionMenu(search_frame,self.page_choice,'1','2','3','4','5','10','15','20','30','50','80','100','200','300','500','1000')
        self.PAGE.grid(row=0,column=3)
        Label(search_frame,text='模式:').grid(row=0,column=4)
        self.query_mode_choice = StringVar(self)
        self.query_mode_choice.set('web应用')
        self.MODE = OptionMenu(search_frame,self.query_mode_choice,'主机搜索','域名/IP','web应用','个人信息')
        self.MODE.grid(row=0,column=5)
        
        Label(search_frame,text='存储模式:').grid(row=0,column=6)
        self.save_mode_choice = StringVar(self)
        self.save_mode_choice.set('不保存')
        self.SAVE_MODE = OptionMenu(search_frame,self.save_mode_choice,'不保存','存文件','数据库')
        self.SAVE_MODE.grid(row=0,column=7)

        Label(search_frame, text='搜索引擎:').grid(row=0, column=8)
        self.search_engine_choice = StringVar(self)
        self.search_engine_choice.set('Fofa')
        self.SEARCH_ENGINE = OptionMenu(search_frame, self.search_engine_choice, 'Zoomeye','Fofa')
        self.SEARCH_ENGINE.grid(row=0, column=9)

        Label(search_frame, text='查询语句:').grid(row=1, column=0)
        self.QUERY = Entry(search_frame, width=60, borderwidth=1)
        self.QUERY.grid(row=1, column=1, columnspan=8)
        self.START = Button(search_frame, text=' 查询 ', command=self.thread)
        self.START.grid(row=1, column=9)


        self.TREEVIEW = Treeview(search_frame,show='headings')
        self.TREEVIEW.grid(row=3,column=0,columnspan=10)
        self.TREEVIEW['columns'] = ("ID","IP","PORT/DOMAIN","OS","TITLE")
        self.TREEVIEW.column("ID",width=50)
        self.TREEVIEW.column("IP",width=160)
        self.TREEVIEW.column("PORT/DOMAIN",width=190)
        self.TREEVIEW.column("OS",width=90)
        self.TREEVIEW.column("TITLE",width=200)
        self.TREEVIEW.heading("ID",text="ID")
        self.TREEVIEW.heading("IP",text="IP")
        self.TREEVIEW.heading("PORT/DOMAIN",text="PORT/DOMAIN")
        self.TREEVIEW.heading("OS",text="OS")
        self.TREEVIEW.heading("TITLE",text="TITLE")
        self.LOG = Text(search_frame,relief=SOLID,borderwidth=1,height=15,width=98,fg='gray')
        self.LOG.grid(row=4,column=0,columnspan=10)

        # 信息处理
        self.log_insert(f"@Version: {VERSION}\n@Author: xzajyjs\n@E-mail: xuziang16@gmail.com\n@Repo: https://github.com/xzajyjs/ThunderSearch\n")
        if not os.path.exists('config.json'):
            self.save_config()
        try:
            self.load_config()
        except Exception as e:
            messagebox.showerror(title='Error',message=f'配置文件读取错误, {e}')

    def load_config(self):
        with open("config.json", "r", encoding='utf8') as f:
            self.dic = json.load(f)
        self.ZOOMEYE_USERNAME.delete(0,END)
        self.ZOOMEYE_USERNAME.insert(END,self.dic['zoomeye_username'])
        self.ZOOMEYE_PASSWORD.delete(0,END)
        self.ZOOMEYE_PASSWORD.insert(END,self.dic['zoomeye_password'])
        self.ZOOMEYE_API.delete(0,END)
        self.ZOOMEYE_API.insert(END,self.dic['zoomeye_api'])
        self.FOFA_USERNAME.delete(0,END)
        self.FOFA_USERNAME.insert(END,self.dic['fofa_username'])
        self.FOFA_API.delete(0,END)
        self.FOFA_API.insert(END,self.dic['fofa_api'])
        self.FILE.delete(0,END)
        self.FILE.insert(END,self.dic['file'])
        self.DATABASE_HOST.delete(0,END)
        self.DATABASE_HOST.insert(END,self.dic['host'])
        self.DATABASE_PORT.delete(0,END)
        self.DATABASE_PORT.insert(END,self.dic['port'])
        self.DATABASE_DATABASE.delete(0,END)
        self.DATABASE_DATABASE.insert(END,self.dic['database'])
        self.DATABASE_USERNAME.delete(0,END)
        self.DATABASE_USERNAME.insert(END,self.dic['username'])
        self.DATABASE_PASSWORD.delete(0,END)
        self.DATABASE_PASSWORD.insert(END,self.dic['password'])

    def save_config(self):
        self.dic = {
            'zoomeye_username':self.ZOOMEYE_USERNAME.get(),
            'zoomeye_password':self.ZOOMEYE_PASSWORD.get(),
            'zoomeye_api':self.ZOOMEYE_API.get(),
            'fofa_username':self.FOFA_USERNAME.get(),
            'fofa_api':self.FOFA_API.get(),
            'file':self.FILE.get(),
            'host':self.DATABASE_HOST.get(),
            'port':self.DATABASE_PORT.get(),
            'database':self.DATABASE_DATABASE.get(),
            'username':self.DATABASE_USERNAME.get(),
            'password':self.DATABASE_PASSWORD.get()
        }
        try:
            with open("config.json", "w", encoding='utf8') as f:
                json.dump(self.dic, f)
        except Exception as e:
            messagebox.showerror('Error',f'保存失败。错误信息:{e}')
        else:
            messagebox.showinfo('Success','保存成功')

    def db_test(self):
        try:
            self.conn = pymysql.connect(database=self.dic['database'],host=self.dic['host'],port=int(self.dic['port']),user=self.dic['username'],password=self.dic['password'])
        except Exception as e:
            messagebox.showerror(title='Error',message=f'数据库连接失败。 {e}')
        else:
            messagebox.showinfo(title='Success',message='数据库连接成功')

    def delete_tree(self,tree):
        for item in tree.get_children():
            tree.delete(item)
    
    def delete_access_token(self):
        try:
            system(f"rm zoomeye_access_token.txt")
        except Exception as e:
            messagebox.showerror('Error',e)
            return None

    def log_insert(self,str):       # update log
        self.LOG.insert(END,chars=str)
        self.LOG.see(END)

    def login(self):
        if self.search_engine_choice.get() == "Zoomeye":
            # 1.查看是否存在zoomeye_access_token.txt
            if os.path.exists('zoomeye_access_token.txt'):
                with open("zoomeye_access_token.txt","r",encoding="utf-8") as f:
                    access_token = f.read().strip('\n')
                self.zoomeye_headers = {
                    'Authorization':'JWT ' + access_token
                }
                self.log_insert("[+] Load file 'access_token.txt' successfully.\n")
                self.log_insert(f"[+] Access_Token: {self.zoomeye_headers['Authorization'][:7]+'*'*10+self.zoomeye_headers['Authorization'][-3:]}\n")
            # 2.通过api-key/username-password登录
            else:
                if self.dic['zoomeye_api'] != "":
                    self.zoomeye_api_key_login(self.dic['zoomeye_api'])
                elif self.dic['zoomeye_username'] != "" and self.dic['zoomeye_password'] != "":
                    self.zoomeye_user_pass_login(self.dic['zoomeye_username'],self.dic['zoomeye_password'])
                else:
                    messagebox.showerror(title='Error',message='请填写Zoomeye配置信息')

    def zoomeye_api_key_login(self,api_key):
        self.zoomeye_headers = {
            "API-KEY":api_key
        }
        self.log_insert(f"[+] API-KEY: {api_key[:5]+'*'*10+api_key[-5:]}\n")

    def zoomeye_user_pass_login(self,username,password):
        url = 'https://api.zoomeye.org/user/login'
        data = {
            'username':username,
            'password':password
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
            with open("zoomeye_access_token.txt","w",encoding="utf-8") as f:
                f.write(access_token)
            self.zoomeye_headers = {
                'Authorization':'JWT ' + access_token
            }
            # print(self.zoomeye_headers['Authorization'])
            self.log_insert(f"[+] Access_Token: {self.zoomeye_headers['Authorization'][:7]+'*'*10+self.zoomeye_headers['Authorization'][-3:]}\n")

    def thread(self):
        if self.query_mode_choice.get() == "个人信息" or self.QUERY.get() != "":
            if self.save_mode_choice.get() == "数据库":
                try:
                    self.conn = pymysql.connect(database=self.dic['database'],host=self.dic['host'],port=int(self.dic['port']),user=self.dic['username'],password=self.dic['password'])
                except Exception as e:
                    messagebox.showerror(title='Error',message=f'[!] 数据库连接失败! {e}')
                    return 
                else:
                    self.log_insert('[+] 数据库连接成功\n')
                    self.cursor = self.conn.cursor()
            elif self.save_mode_choice.get() == "存文件" and self.FILE.get() == "":
                messagebox.showerror(title='Error',message='[!] 文件名为空!')
                return
            t = Thread(target=self.run,daemon=True)
            t.start()
        else:
            messagebox.showerror(title='Error',message='[!] 查询语句为空!')

    def run(self):
        # zoomeye
        if self.search_engine_choice.get() == "Zoomeye":
            if self.query_mode_choice.get() != '个人信息':
                self.delete_tree(self.TREEVIEW)
            self.login()
            self.log_insert('[Zoomeye] Start searching...\n')
            query = self.QUERY.get().replace(" ",'%20')

            if self.query_mode_choice.get() == '主机搜索':
                hs.headers = self.zoomeye_headers
                self.log_insert("")
                hs.host_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))

                j=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_host_search(
                    ip text,port text,os text,app text,version text,title text,city text,country text,continents text);''')
                    self.conn.commit()
                    for each_dic in hs.info_list:
                        self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os'],each_dic['title']))
                        self.cursor.execute(f'''INSERT INTO host_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}")''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip ,port ,os ,app ,version ,title ,city ,country ,continents\n")
                        for each_dic in hs.info_list:
                            self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os'],each_dic['title']))
                            f.write(f'''{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in hs.info_list:
                        self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                        j+=1

            if self.query_mode_choice.get() == '域名/IP':
                di.headers = self.zoomeye_headers
                di.domain_ip(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
                j=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_domain_ip(
                    ip text,name text);''')
                    self.conn.commit()
                    for each_dic in di.info_list:
                        self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['name'],None))
                        self.cursor.execute(f'''INSERT INTO domain_ip VALUES("{each_dic['ip']}","{each_dic['name']}")''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip ,name\n")
                        for each_dic in di.info_list:
                            self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['name'],None))
                            f.write(f'''{each_dic["ip"]}","{each_dic["name"]}"\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in di.info_list:
                        self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['name'], None))
                        j+=1

            if self.query_mode_choice.get() == 'web应用':
                ws.headers = self.zoomeye_headers
                ws.web_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
                j = 1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_web_search(
                    ip text,site text,title text,city text,country text,continent text,isp text);''')
                    self.conn.commit()
                    for each_dic in ws.info_list:
                        self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['site'],'',each_dic['title']))
                        self.cursor.execute(f'''INSERT INTO web_search VALUES("{each_dic["ip"]}","{each_dic["site"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continent"]}","{each_dic['isp']}");''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip ,site ,title ,city ,country ,continents, isp\n")
                        for each_dic in ws.info_list:
                            self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['site'],'',each_dic['title']))
                            f.write(f'''{each_dic["ip"]},{each_dic["site"]},{each_dic["title"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continent"]},{each_dic['isp']}\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in ws.info_list:
                        self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['site'],'',each_dic['title']))
                        j+=1

            res.headers = self.zoomeye_headers
            if self.query_mode_choice.get() == '个人信息':
                self.log_insert(res.resource(mode="complete"))
            else:
                self.log_insert(f'Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
                self.log_insert(res.resource(mode="easy"))
        # fofa
        elif self.search_engine_choice.get() == "Fofa":
            if self.query_mode_choice.get() == "个人信息":
                text = fofa_resource.fofa_search_resource(email=self.dic['fofa_username'],key=self.dic['fofa_api'])
                self.log_insert(text)
            else:
                self.delete_tree(self.TREEVIEW)
                self.log_insert('[Fofa] Start searching...\n')

                error_info = fofa_search_all.fofa_search(email=self.dic['fofa_username'],key=self.dic['fofa_api'],query=str(self.QUERY.get()),size=int(self.page_choice.get())*10)
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}')
                j=1
                for each_dic in fofa_search_all.info_list:
                    self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['port']+"/"+each_dic['domain'], each_dic['os'], each_dic['title']))
                    j+=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists fofa_search_all(
                    ip text,port text,host text,domain text,os text,server text,title text,protocol text,country_name text,region text,city text,as_organization text,icp text,jarm text);''')
                    self.conn.commit()
                    for each in fofa_search_all.info_list:
                        self.cursor.execute(f'''insert into fofa_search_all values(
                            "{each['ip']}","{each['port']}","{each['host']}","{each['domain']}","{each['os']}","{each['server']}","{each['title']}","{each['protocol']}","{each['country_name']}","{each['region']}","{each['city']}","{each['as_organization']}","{each['icp']}","{each['jarm']}"
                        )''')
                        self.conn.commit()
                    pass
                if self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip,port,host,domain,os,server,title,protocol,country_name,region,city,as_organization,icp,jarm\n")
                        for each_dic in fofa_search_all.info_list:
                            f.write(f"{each_dic['ip']},{each_dic['port']},{each_dic['host']},{each_dic['domain']},{each_dic['os']},{each_dic['server']},{each_dic['title']},{each_dic['protocol']},{each_dic['country_name']},{each_dic['region']},{each_dic['city']},{each_dic['as_organization']},{each_dic['icp']},{each_dic['jarm']}\n")
                    
                if self.save_mode_choice.get() == "不保存":
                    pass
                self.log_insert(f'[Fofa] End of Search. Obtain totally {fofa_search_all.total_num}\nComplete information has been stored by mode "{self.save_mode_choice.get()}".\n')


if __name__=='__main__':
    root = Tk()
    root.geometry('760x516+320+100')
    root.minsize(width=760, height=516)
    root.maxsize(width=760, height=516)
    root.title(f'ThunderSearch {VERSION}  --xzajyjs')
    Application(master=root)
    root.mainloop()
