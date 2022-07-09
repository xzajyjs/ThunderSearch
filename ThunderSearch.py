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

VERSION = "v2.0"

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
        # help_frame = Frame()
        notebook.add(search_frame, text='查询')
        notebook.add(config_frame, text='配置')
        # notebook.add(help_frame, text='帮助')
        notebook.grid(row=0,column=0,columnspan=20)

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
        Label(config_frame,text='Fofa',width=10).grid(row=4,column=0,columnspan=2)
        Label(config_frame, text='账号:').grid(row=5,column=0)
        Label(config_frame, text='密码:').grid(row=6,column=0)
        Label(config_frame,text='API-KEY:').grid(row=7,column=0)
        self.FOFA_USERNAME = Entry(config_frame,width=24,borderwidth=1,state='readonly')
        self.FOFA_USERNAME.grid(row=5,column=1)
        self.FOFA_PASSWORD = Entry(config_frame,width=24,show="*",borderwidth=1,state='readonly')
        self.FOFA_PASSWORD.grid(row=6,column=1)
        self.FOFA_API = Entry(config_frame,width=24,borderwidth=1,show='*',state='readonly')
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
        self.search_engine_choice.set('Zoomeye')
        self.SEARCH_ENGINE = OptionMenu(search_frame, self.search_engine_choice, 'Zoomeye')
        self.SEARCH_ENGINE.grid(row=0, column=9)

        # self.query_label = Label(search_frame, text='搜索语句').grid(row=1, column=2)
        Label(search_frame, text='查询语句:').grid(row=1, column=0)
        self.QUERY = Entry(search_frame, width=60, borderwidth=1)
        self.QUERY.grid(row=1, column=1, columnspan=8)
        self.START = Button(search_frame, text=' 查询 ', command=self.thread)
        self.START.grid(row=1, column=9)


        self.TREEVIEW = Treeview(search_frame,show='headings')
        self.TREEVIEW.grid(row=3,column=0,columnspan=10)
        self.TREEVIEW['columns'] = ("ID","IP","PORT/DOMAIN","OS")
        self.TREEVIEW.column("ID",width=50)
        self.TREEVIEW.column("IP",width=220)
        self.TREEVIEW.column("PORT/DOMAIN",width=200)
        self.TREEVIEW.column("OS",width=220)
        self.TREEVIEW.heading("ID",text="ID")
        self.TREEVIEW.heading("IP",text="IP")
        self.TREEVIEW.heading("PORT/DOMAIN",text="PORT/DOMAIN")
        self.TREEVIEW.heading("OS",text="OS")
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
        self.FOFA_PASSWORD.delete(0,END)
        self.FOFA_PASSWORD.insert(END,self.dic['fofa_password'])
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
            'fofa_password':self.FOFA_PASSWORD.get(),
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
            system(f"rm zoomeye_access_token.txt fofa_access_token.txt")
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

        elif self.search_engine_choice.get() == "Fofa":
            pass

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
                    self.conn = pymysql.connect(database=self.dic['database'],host=self.dic['host'],port=self.dic['port'],user=self.dic['username'],password=self.dic['password'])
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
        if self.query_mode_choice.get() != '个人信息':
            self.delete_tree(self.TREEVIEW)
        self.login()
        self.log_insert('Start searching...\n')
        query = self.QUERY.get().replace(" ",'%20')

        if self.query_mode_choice.get() == '主机搜索':
            hs.headers = self.zoomeye_headers
            hs.host_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))

            j=1
            if self.save_mode_choice.get() == "数据库":
                self.cursor.execute('''CREATE TABLE if not exists host_search(
                ip text,port text,os text,app text,version text,title text,city text,country text,continents text);''')
                self.conn.commit()
                for each_dic in hs.info_list:
                    self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os']))
                    self.cursor.execute(f'''INSERT INTO host_search VALUES("{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}")''')
                    self.conn.commit()
                    j+=1
            elif self.save_mode_choice.get() == "存文件":
                with open(self.FILE.get(),"w",encoding="utf-8") as f:
                    f.write("ip ,port ,os ,app ,version ,title ,city ,country ,continents\n")
                    for each_dic in hs.info_list:
                        self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os']))
                        f.write(f'''{each_dic["ip"]}","{each_dic["port"]}","{each_dic["os"]}","{each_dic["app"]}","{each_dic["version"]}","{each_dic["title"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continents"]}\n''')
                        j+=1
            elif self.save_mode_choice.get() == "不保存":
                for each_dic in hs.info_list:
                    self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['port'], each_dic['os']))
                    j+=1
                    
        if self.query_mode_choice.get() == '域名/IP':
            di.headers = self.zoomeye_headers
            di.domain_ip(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
            j=1
            if self.save_mode_choice.get() == "数据库":
                self.cursor.execute('''CREATE TABLE if not exists domain_ip(
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
                self.cursor.execute('''CREATE TABLE if not exists web_search(
                ip text,site text,city text,country text,continent text,isp text);''')
                self.conn.commit()
                for each_dic in ws.info_list:
                    self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['site']))
                    self.cursor.execute(f'''INSERT INTO web_search VALUES("{each_dic["ip"]}","{each_dic["site"]}","{each_dic["city"]}","{each_dic["country"]}","{each_dic["continent"]}","{each_dic['isp']}");''')
                    self.conn.commit()
                    j+=1
            elif self.save_mode_choice.get() == "存文件":
                with open(self.FILE.get(),"w",encoding="utf-8") as f:
                    f.write("ip ,site ,city ,country ,continents, isp\n")
                    for each_dic in ws.info_list:
                        self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['site']))
                        f.write(f'''{each_dic["ip"]},{each_dic["site"]},{each_dic["city"]},{each_dic["country"]},{each_dic["continent"]},{each_dic['isp']}\n''')
                        j+=1
            elif self.save_mode_choice.get() == "不保存":
                for each_dic in ws.info_list:
                    self.TREEVIEW.insert("", END, values=(j, each_dic['ip'], each_dic['site']))
                    j+=1

        res.headers = self.zoomeye_headers
        if self.query_mode_choice.get() == '个人信息':
            self.log_insert(res.resource(mode="complete"))
        else:
            self.log_insert(f'Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
            self.log_insert(res.resource(mode="easy"))


if __name__=='__main__':
    root = Tk()
    root.geometry('760x516+320+100')
    # root.maxsize(width=718,height=497)
    root.minsize(width=760, height=516)
    root.maxsize(width=760, height=516)
    root.title(f'ThunderSearch {VERSION}  --xzajyjs')
    Application(master=root)
    root.mainloop()
