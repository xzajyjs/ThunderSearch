import os
import json
import pymysql
import requests
import tkinter as tk
from os import system
from threading import Thread
from tkinter import messagebox
from tkinter.ttk import Notebook, Treeview

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

VERSION = "v2.3.1"

class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.delete_access_token()
        self.createWidget()
        self.pack()
        

    def createWidget(self):
        notebook = Notebook(self)
        self.search_frame = tk.Frame()
        config_frame = tk.Frame()
        help_frame = tk.Frame()
        notebook.add(self.search_frame, text='查询')
        notebook.add(config_frame, text='配置')
        notebook.add(help_frame, text='帮助')
        notebook.grid(row=0,column=0,columnspan=20)

        # help_frame
        help_text = tk.Text(help_frame,relief=tk.SOLID,borderwidth=1,height=35,width=100,fg='gray')
        help_text.grid(row=0,column=0)
        text = """使用指南:
1.先填写配置选项卡中的选项(可有选择性填写)
2.填写完配置请先点击保存
3.文件路径请填写绝对路径,如/Users/xxx/fofa.csv
4.查询页数在fofa和quake查询下乘以10即为查询数据条数
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
https://quake.360.cn/quake/#/help?id=5eb238f110d2e850d5c6aec8&title=%E6%A3%80%E7%B4%A2%E5%85%B3%E9%94%AE%E8%AF%8D"""
        help_text.insert(tk.END,text)


        # config_frame

        # zoomeye
        tk.Label(config_frame,text='Zoomeye',width=10).grid(row=0,column=0,columnspan=2)
        tk.Label(config_frame, text='账号:').grid(row=1,column=0)
        tk.Label(config_frame, text='密码:').grid(row=2,column=0)
        tk.Label(config_frame,text='API-KEY:').grid(row=3,column=0)
        self.ZOOMEYE_USERNAME = tk.Entry(config_frame,width=24,borderwidth=1)
        self.ZOOMEYE_USERNAME.grid(row=1,column=1)
        self.ZOOMEYE_PASSWORD = tk.Entry(config_frame,width=24,show="*",borderwidth=1)
        self.ZOOMEYE_PASSWORD.grid(row=2,column=1)
        self.ZOOMEYE_API = tk.Entry(config_frame,width=24,borderwidth=1,show='*')
        self.ZOOMEYE_API.grid(row=3,column=1)

        # fofa
        tk.Label(config_frame,text='Fofa',width=10).grid(row=5,column=0,columnspan=2)
        tk.Label(config_frame, text='邮箱:').grid(row=6,column=0)
        tk.Label(config_frame,text='API-KEY:').grid(row=7,column=0)
        self.FOFA_USERNAME = tk.Entry(config_frame,width=24,borderwidth=1)
        self.FOFA_USERNAME.grid(row=6,column=1)
        self.FOFA_API = tk.Entry(config_frame,width=24,borderwidth=1,show='*')
        self.FOFA_API.grid(row=7,column=1)

        # blank
        tk.Label(config_frame,text="").grid(row=8,column=0,columnspan=2)

        #quake
        tk.Label(config_frame,text="360Quake").grid(row=9,column=0,columnspan=2)
        tk.Label(config_frame,text="API-KEY").grid(row=10,column=0)
        self.QUAKE_API = tk.Entry(config_frame,width=24,show="*",borderwidth=1)
        self.QUAKE_API.grid(row=10,column=1)

        # 右侧配置
        tk.Label(config_frame, text='其他配置').grid(row=0,column=2,columnspan=2)
        tk.Label(config_frame,text='文件路径').grid(row=1,column=2)
        tk.Label(config_frame, text='数据库配置(MySQL)').grid(row=2,column=2,columnspan=2)
        tk.Label(config_frame,text='主机').grid(row=3,column=2)
        tk.Label(config_frame,text='端口').grid(row=4,column=2)
        tk.Label(config_frame,text='数据库名').grid(row=5,column=2)
        tk.Label(config_frame,text='用户名').grid(row=6,column=2)
        tk.Label(config_frame,text='密码').grid(row=7,column=2)
        self.FILE = tk.Entry(config_frame, width=30,borderwidth=1)
        self.FILE.grid(row=1,column=3)
        self.DATABASE_HOST = tk.Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_HOST.grid(row=3,column=3)
        self.DATABASE_PORT = tk.Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_PORT.grid(row=4,column=3)
        self.DATABASE_DATABASE = tk.Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_DATABASE.grid(row=5,column=3)
        self.DATABASE_USERNAME = tk.Entry(config_frame, width=30,borderwidth=1)
        self.DATABASE_USERNAME.grid(row=6,column=3)
        self.DATABASE_PASSWORD = tk.Entry(config_frame, width=30,borderwidth=1,show="*")
        self.DATABASE_PASSWORD.grid(row=7,column=3)


        self.SAVE = tk.Button(config_frame, text='保存配置', command=self.save_config)
        self.SAVE.grid(row=3,column=4)
        self.LOAD = tk.Button(config_frame, text='读取配置', command=self.load_config)
        self.LOAD.grid(row=4,column=4)
        self.LOAD = tk.Button(config_frame, text='清空配置', command=self.clear_config)
        self.LOAD.grid(row=5,column=4)
        self.LOAD = tk.Button(config_frame, text='数据库测试', command=self.db_test)
        self.LOAD.grid(row=6,column=4)
        self.SAVE = tk.Button(config_frame, text='清除token', command=self.delete_access_token)
        self.SAVE.grid(row=7,column=4)


        # self.search_frame
        tk.Label(self.search_frame, text='线程数:',width=6).grid(row=0,column=0)
        self.thread_choice = tk.StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = tk.OptionMenu(self.search_frame,self.thread_choice,'1','5','10','20','30')
        self.THREAD.grid(row=0,column=1)
        tk.Label(self.search_frame,text='查询页数:').grid(row=0,column=2)
        self.page_choice = tk.StringVar(self)
        self.page_choice.set('1')
        self.PAGE = tk.OptionMenu(self.search_frame,self.page_choice,'1','2','3','4','5','10','15','20','30','50','80','100','200','300','500','1000')
        self.PAGE.grid(row=0,column=3)
        tk.Label(self.search_frame,text='模式:').grid(row=0,column=4)

        self.mode_dict = {
            'Zoomeye':['主机搜索','域名/IP','web应用','个人信息'],
            'Fofa':['数据查询','个人信息'],
            'Quake':['主机搜索','服务搜索','个人信息']
        }
        
        self.query_mode_choice = tk.StringVar(self)
        self.MODE = tk.OptionMenu(self.search_frame,self.query_mode_choice,'')
        self.MODE.grid(row=0,column=5)

        self.search_engine_choice = tk.StringVar(self)
        self.search_engine_choice.trace('w', self.update_mode_menu)
        self.search_engine_choice.set('Zoomeye')

        tk.Label(self.search_frame,text='存储模式:').grid(row=0,column=6)
        self.save_mode_choice = tk.StringVar(self)
        self.save_mode_choice.set('不保存')
        self.SAVE_MODE = tk.OptionMenu(self.search_frame,self.save_mode_choice,'不保存','存文件','数据库')
        self.SAVE_MODE.grid(row=0,column=7)

        tk.Label(self.search_frame, text='搜索引擎:').grid(row=0, column=8)
        self.SEARCH_ENGINE = tk.OptionMenu(self.search_frame, self.search_engine_choice, *self.mode_dict.keys())
        self.SEARCH_ENGINE.grid(row=0, column=9)

        tk.Label(self.search_frame, text='查询语句:').grid(row=1, column=0)
        self.QUERY = tk.Entry(self.search_frame, width=60, borderwidth=1)
        self.QUERY.grid(row=1, column=1, columnspan=8)
        self.START = tk.Button(self.search_frame, text='查询', command=self.thread)
        self.START.grid(row=1, column=9)

        self.TREEVIEW = Treeview(self.search_frame,show='headings')
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
        self.LOG = tk.Text(self.search_frame,relief=tk.SOLID,borderwidth=1,height=15,width=98,fg='gray')
        self.LOG.grid(row=4,column=0,columnspan=10)

        # 信息处理
        self.log_insert(f"@Version: {VERSION}\n@Author: xzajyjs\n@E-mail: xuziang16@gmail.com\n@Repo: https://github.com/xzajyjs/ThunderSearch\n")
        if not os.path.exists('config.json'):
            self.save_config()
        try:
            self.load_config()
        except Exception as e:
            messagebox.showerror(title='Error',message=f'配置文件读取错误, {e}')


    def update_mode_menu(self,*args):
        modes = self.mode_dict[self.search_engine_choice.get()]
        self.query_mode_choice.set(modes[0])
        menu = self.MODE['menu']
        menu.delete(0, 'end')
        for mode in modes:
            menu.add_command(label=mode, command=lambda mode=mode: self.query_mode_choice.set(mode))


    def _delete_config(self):    # 清空显示
        self.ZOOMEYE_USERNAME.delete(0,tk.END)
        self.ZOOMEYE_PASSWORD.delete(0,tk.END)
        self.ZOOMEYE_API.delete(0,tk.END)
        self.FOFA_USERNAME.delete(0,tk.END)
        self.FOFA_API.delete(0,tk.END)
        self.QUAKE_API.delete(0,tk.END)
        self.FILE.delete(0,tk.END)
        self.DATABASE_HOST.delete(0,tk.END)
        self.DATABASE_PORT.delete(0,tk.END)
        self.DATABASE_DATABASE.delete(0,tk.END)
        self.DATABASE_USERNAME.delete(0,tk.END)
        self.DATABASE_PASSWORD.delete(0,tk.END)


    def _insert_config(self):    # 插入数据
        self.ZOOMEYE_USERNAME.insert(tk.END,self.dic['zoomeye_username'])
        self.ZOOMEYE_PASSWORD.insert(tk.END,self.dic['zoomeye_password'])
        self.ZOOMEYE_API.insert(tk.END,self.dic['zoomeye_api'])
        self.FOFA_USERNAME.insert(tk.END,self.dic['fofa_username'])
        self.FOFA_API.insert(tk.END,self.dic['fofa_api'])
        self.QUAKE_API.insert(tk.END,self.dic['quake_api'])
        self.FILE.insert(tk.END,self.dic['file'])
        self.DATABASE_HOST.insert(tk.END,self.dic['host'])
        self.DATABASE_PORT.insert(tk.END,self.dic['port'])
        self.DATABASE_DATABASE.insert(tk.END,self.dic['database'])
        self.DATABASE_USERNAME.insert(tk.END,self.dic['username'])
        self.DATABASE_PASSWORD.insert(tk.END,self.dic['password'])


    def _save_config(self):     # 保存数据
        self.dic = {
            'zoomeye_username':self.ZOOMEYE_USERNAME.get(),
            'zoomeye_password':self.ZOOMEYE_PASSWORD.get(),
            'zoomeye_api':self.ZOOMEYE_API.get(),
            'fofa_username':self.FOFA_USERNAME.get(),
            'fofa_api':self.FOFA_API.get(),
            'quake_api':self.QUAKE_API.get(),
            'file':self.FILE.get(),
            'host':self.DATABASE_HOST.get(),
            'port':self.DATABASE_PORT.get(),
            'database':self.DATABASE_DATABASE.get(),
            'username':self.DATABASE_USERNAME.get(),
            'password':self.DATABASE_PASSWORD.get()
        }
        with open("config.json", "w", encoding='utf8') as f:
            json.dump(self.dic, f)


    def load_config(self):      # 读取配置
        with open("config.json", "r", encoding='utf8') as f:
            self.dic = json.load(f)
        self._delete_config()
        self._insert_config()
        

    def save_config(self):      # 保存配置
        try:
            self._save_config()
        except Exception as e:
            messagebox.showerror('Error',f'保存失败。错误信息:{e}')
        else:
            messagebox.showinfo('Success','保存成功')


    def clear_config(self):
        self._delete_config()
        try:
            self._save_config()
        except Exception as e:
            messagebox.showerror("Error",e)
        else:
            messagebox.showinfo("Success","清空成功")
        

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
        self.LOG.insert(tk.END,chars=str)
        self.LOG.see(tk.END)


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
            self.log_insert('[Zoomeye] Start searching...\n')
            if self.query_mode_choice.get() != '个人信息':
                self.delete_tree(self.TREEVIEW)
            self.login()
            query = self.QUERY.get().replace(" ",'%20')

            if self.query_mode_choice.get() == '主机搜索':
                zoomeye_hostsearch.headers = self.zoomeye_headers
                error_info = zoomeye_hostsearch.host_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_host_search(
                    ip text,port text,os text,app text,version text,title text,city text,country text,continents text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_hostsearch.info_list:
                        self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os'],each_dic['title']))
                        self.cursor.execute(f'''INSERT INTO zoomeye_host_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}")''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip,port,os,app,version,title,city,country,continents\n")
                        for each_dic in zoomeye_hostsearch.info_list:
                            self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os'],each_dic['title']))
                            f.write(f'''{each_dic["ip"]},{each_dic["port"]},{each_dic["os"]},{each_dic["app"]},{each_dic["version"]},{each_dic["title"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continents"]}\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in zoomeye_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os'], each_dic['title']))
                        j+=1

            if self.query_mode_choice.get() == '域名/IP':
                zoomeye_domain_ip.headers = self.zoomeye_headers
                error_info = zoomeye_domain_ip.domain_ip(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_domain_ip(
                    ip text,name text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_domain_ip.info_list:
                        self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['name'],None))
                        self.cursor.execute(f'''INSERT INTO zoomeye_domain_ip VALUES("{each_dic['ip']}","{each_dic['name']}")''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip ,name\n")
                        for each_dic in zoomeye_domain_ip.info_list:
                            self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['name'],None))
                            f.write(f'''{str(each_dic["ip"])},{each_dic["name"]}\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in zoomeye_domain_ip.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['name'], None))
                        j+=1

            if self.query_mode_choice.get() == 'web应用':
                zoomeye_websearch.headers = self.zoomeye_headers
                error_info = zoomeye_websearch.web_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists zoomeye_web_search(
                    ip text,site text,title text,city text,country text,continent text,isp text);''')
                    self.conn.commit()
                    for each_dic in zoomeye_websearch.info_list:
                        self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['site'],'',each_dic['title']))
                        self.cursor.execute(f'''INSERT INTO zoomeye_web_search VALUES("{each_dic["ip"]}","{each_dic["site"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continent"]}","{each_dic['isp']}");''')
                        self.conn.commit()
                        j+=1
                elif self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip ,site ,title ,city ,country ,continents, isp\n")
                        for each_dic in zoomeye_websearch.info_list:
                            self.TREEVIEW.insert("",tk.END,values=(j,each_dic['ip'],each_dic['site'],'',each_dic['title']))
                            f.write(f'''{each_dic["ip"]},{each_dic["site"]},{each_dic["title"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continent"]},{each_dic['isp']}\n''')
                            j+=1
                elif self.save_mode_choice.get() == "不保存":
                    for each_dic in zoomeye_websearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['site'],'',each_dic['title']))
                        j+=1

            zoomeye_resource.headers = self.zoomeye_headers
            if self.query_mode_choice.get() == '个人信息':
                self.log_insert(zoomeye_resource.resource(mode="complete"))
            else:
                self.log_insert(f'[Zoomeye] End of search. Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
                self.log_insert(zoomeye_resource.resource(mode="easy"))
        
        # fofa
        elif self.search_engine_choice.get() == "Fofa":
            self.log_insert('[Fofa] Start searching...\n')
            if self.query_mode_choice.get() == "个人信息":
                text = fofa_resource.fofa_search_resource(email=self.dic['fofa_username'],key=self.dic['fofa_api'])
                self.log_insert(text)
            else:
                self.delete_tree(self.TREEVIEW)
                error_info = fofa_search_all.fofa_search(email=self.dic['fofa_username'],key=self.dic['fofa_api'],query=str(self.QUERY.get()),size=int(self.page_choice.get())*10)
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j=1
                for each_dic in fofa_search_all.info_list:
                    self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['port']+"/"+each_dic['domain'], each_dic['os'], each_dic['title']))
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

        # quake
        elif self.search_engine_choice.get() == "Quake":
            self.log_insert('[Quake] Start searching...\n')
            query = self.QUERY.get()
            if self.query_mode_choice.get() != '个人信息':
                self.delete_tree(self.TREEVIEW)
            if self.query_mode_choice.get() == "主机搜索":
                error_info = quake_hostsearch.quake_host_search(query=query,page=self.page_choice.get(),key=self.dic['quake_api'])
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "不保存":
                    for each_dic in quake_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                        j+=1
                if self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip,service_port,service_name,service_version,service_id,domains,hostname,os_name,os_version,country_en,city_en\n")
                        for each_dic in quake_hostsearch.info_list:
                            f.write(f'''{each_dic['ip']},{each_dic['service_port']},{each_dic['service_name']},{each_dic['service_version']},{each_dic['service_id']},{each_dic['domains']},{each_dic['hostname']},{each_dic['os_name']},{each_dic['os_version']},{each_dic['country_en']},{each_dic['city_en']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                            j+=1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists quake_host_search(
                    ip text,service_port text,service_name text,service_version text,service_id text,domains text,hostname text,os_name text,os_version text,country_en text,city_en text);''')
                    self.conn.commit()
                    for each_dic in quake_hostsearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['service_port'], each_dic['os_name'], ''))
                        self.cursor.execute(f'''INSERT INTO quake_host_search VALUES("{each_dic["ip"]}","{each_dic["service_port"]}","{each_dic["service_name"]}","{each_dic["service_version"]}","{each_dic["service_id"]}","{each_dic["domains"]}","{each_dic["hostname"]}","{each_dic["os_name"]}","{each_dic["os_version"]}","{each_dic["country_en"]}","{each_dic["city_en"]}")''')
                        self.conn.commit()
                        j+=1
            if self.query_mode_choice.get() == "服务搜索":
                error_info = quake_servicesearch.quake_service_search(query=query,page=self.page_choice.get(),key=self.dic['quake_api'])
                if error_info is not None:
                    self.log_insert(f'[!] Error: {error_info}\n')

                j = 1
                if self.save_mode_choice.get() == "不保存":
                    for each_dic in quake_servicesearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                        j += 1
                if self.save_mode_choice.get() == "存文件":
                    with open(self.FILE.get(),"w",encoding="utf-8") as f:
                        f.write("ip,port,org,hostname,service_title,service_server,transport,os_name,os_version,service_name,country_en,city_en\n")
                        for each_dic in quake_servicesearch.info_list:
                            f.write(f'''{each_dic['ip']},{each_dic['port']},{each_dic['org']},{each_dic['hostname']},{each_dic['service_title']},{each_dic['service_server']},{each_dic['transport']},{each_dic['os_name']},{each_dic['os_version']},{each_dic['service_name']},{each_dic['country_en']},{each_dic['city_en']}\n''')
                            self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                            j += 1
                if self.save_mode_choice.get() == "数据库":
                    self.cursor.execute('''CREATE TABLE if not exists quake_service_search(
                    ip text,port text,org text,hostname text,service_title text,service_server text,transport text,os_name text,service_name text,country_en text,city_en text,os_version text);''')
                    self.conn.commit()
                    for each_dic in quake_servicesearch.info_list:
                        self.TREEVIEW.insert("", tk.END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os_name'], each_dic['service_title']))
                        self.cursor.execute(f'''INSERT INTO quake_service_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["org"]}","{each_dic["hostname"]}","{each_dic["service_title"]}","{each_dic["service_server"]}","{each_dic["transport"]}","{each_dic["os_name"]}","{each_dic["service_name"]}","{each_dic["country_en"]}","{each_dic["city_en"]}","{each_dic["os_version"]}")''')
                        self.conn.commit()
                        j+=1
            if self.query_mode_choice.get() == "个人信息":
                text = quake_resource.quake_resource_search(key=self.dic['quake_api'],mode="complete")
                self.log_insert(text)
            else:
                self.log_insert(f'[Quake] End of search. Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
                self.log_insert(quake_resource.quake_resource_search(key=self.dic['quake_api'],mode="easy"))
            

if __name__=='__main__':
    root = tk.Tk()
    root.geometry('760x516+320+100')
    root.minsize(width=760, height=516)
    root.maxsize(width=760, height=516)
    root.title(f'ThunderSearch {VERSION}  --xzajyjs')
    Application(master=root)
    root.mainloop()
