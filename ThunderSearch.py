import json
import requests
import pymysql
from os import system
from tkinter import *
from threading import Thread
from tkinter import messagebox
from tkinter.ttk import Treeview

import module.host_search as hs
import module.domain_ip as di
import module.resource as res
import module.web_search as ws

class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.delete_access_token()
        self.createWidget()
        self.pack()
        
    def createWidget(self):
        self.login_mode_label = Label(self,text='登陆方式',width=10).grid(row=0,column=0)
        self.login_mode_choice = StringVar(self)
        self.login_mode_choice.set('配置文件')
        self.LOGIN_MODE = OptionMenu(self,self.login_mode_choice,'账号密码','API-KEY','配置文件')
        self.LOGIN_MODE.grid(row=1,column=0)
        self.api_label = Label(self,text='API-KEY:').grid(row=2,column=0)
        self.API = Entry(self,width=21,borderwidth=1,show='*')
        self.API.grid(row=2,column=1,columnspan=2)
        self.u_label = Label(self, text='账号:').grid(row=0,column=1)
        self.p_label = Label(self, text='密码:').grid(row=1,column=1)
        self.USERNAME = Entry(self,width=16,borderwidth=1)
        self.USERNAME.grid(row=0,column=2)
        self.PASSWORD = Entry(self,width=16,show="*",borderwidth=1)
        self.PASSWORD.grid(row=1,column=2)
        self.thread_label = Label(self, text='线程数:',width=6).grid(row=0,column=3)
        self.query_label = Label(self, text='查询语句:').grid(row=1,column=3)
        self.thread_choice = StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = OptionMenu(self,self.thread_choice,'1','5','10','20','30')
        self.THREAD.grid(row=0,column=4)
        self.page_label = Label(self,text='查询页数:').grid(row=0,column=5)
        self.page_choice = StringVar(self)
        self.page_choice.set('1')
        self.PAGE = OptionMenu(self,self.page_choice,'1','2','3','4','5','10','15','20','30','50','80','100','200','300','500','1000')
        self.PAGE.grid(row=0,column=6)
        self.mode_label = Label(self,text='模式:').grid(row=0,column=7)
        self.query_mode_choice = StringVar(self)
        self.query_mode_choice.set('web应用')
        self.MODE = OptionMenu(self,self.query_mode_choice,'主机搜索','域名/IP','web应用','个人信息')
        self.MODE.grid(row=0,column=8)
        self.START = Button(self,text='查询',command=self.thread)
        self.START.grid(row=0,column=9)
        self.QUERY = Entry(self, width=36,borderwidth=1)
        self.QUERY.grid(row=1,column=4,columnspan=8)
        
        self.save_mode_label = Label(self,text='存储模式:').grid(row=2,column=3)
        self.save_mode_choice = StringVar(self)
        self.save_mode_choice.set('不保存')
        self.SAVE_MODE = OptionMenu(self,self.save_mode_choice,'存文件','数据库','不保存')
        self.SAVE_MODE.grid(row=2,column=4)

        self.file_label = Label(self,text='文件名:').grid(row=2,column=5)
        self.FILE = Entry(self,width=21,borderwidth=1)
        self.FILE.grid(row=2,column=6,columnspan=10)
        
        self.TREEVIEW = Treeview(self,show='headings')
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
        self.LOG = Text(self,relief=SOLID,borderwidth=1,height=15,width=98,fg='gray')
        self.LOG.grid(row=4,column=0,columnspan=10)

        self.log_insert("@Version: 1.7.5\n@Author: xzajyjs\n@E-mail: xuziang16@gmail.com\n@Repo: https://github.com/xzajyjs/ThunderSearch\n")

    def delete_tree(self,tree):
        for item in tree.get_children():
            tree.delete(item)
    
    def delete_access_token(self):
        try:
            system("rm access_token.txt")
        except:
            return None

    def log_insert(self,str):       # update log
        self.LOG.insert(END,chars=str)
        self.LOG.see(END)

    def login(self):
        try:    # access_token exists.
            with open("access_token.txt","r",encoding="utf-8") as f:
                access_token = f.read().strip('\n')
            self.headers = {
                'Authorization':'JWT ' + access_token
            }
            self.log_insert("[+] Load file 'access_token.txt' successfully.\n")
            self.log_insert(f"[+] Access_Token: {self.headers['Authorization'][:7]+'*'*10+self.headers['Authorization'][-3:]}\n")
        except FileNotFoundError:   # access_token not exists.
            if self.login_mode_choice.get() == "账号密码":
                self.log_insert("[!] Fail to find access_token.txt. Need to Login now.\n")
                username = self.USERNAME.get().strip()
                password = self.PASSWORD.get().strip()
                self.user_pass_login(username=username,password=password)

            elif self.login_mode_choice.get() == "API-KEY":
                key = self.API.get().strip()
                self.api_key_login(key)

            elif self.login_mode_choice.get() == "配置文件":
                with open("config.json","r",encoding="utf-8") as f:
                    user_data = json.load(f)
                if user_data['API-KEY'] != "":
                    self.log_insert('[+] Try to login with API-KEY in config.json.\n')
                    self.api_key_login(user_data['API-KEY'])
                elif user_data['username'] != "" and user_data['password'] != "":
                    self.log_insert('[+] Try to login with username/password in config.json.\n')
                    self.user_pass_login(username=user_data['username'],password=user_data['password'])
                else:
                    self.log_insert('[!] config.json empty!\n')
                    messagebox.showerror(title='Error',message='配置文件为空')
                    return None

    def api_key_login(self,api_key):
        self.headers = {
            "API-KEY":api_key
        }
        self.log_insert(f"[+] API-KEY: {api_key[:5]+'*'*10+api_key[-5:]}\n")

    def user_pass_login(self,username,password):
        url = 'https://api.zoomeye.org/user/login'
        data = {
            'username':username,
            'password':password
        }
        encoded_data = json.dumps(data)
        resp_json = requests.post(url=url, data=encoded_data).json()
        try:
            access_token = resp_json['access_token']
        except:
            self.log_insert(f'[-] Login fail. {resp_json["message"]}\n')
        else:
            self.log_insert('[+] Login success!\n')
            with open("access_token.txt","w",encoding="utf-8") as f:
                f.write(access_token)
        self.headers = {
            'Authorization':'JWT ' + access_token
        }
        print(self.headers['Authorization'])
        self.log_insert(f"[+] Access_Token: {self.headers['Authorization'][:7]+'*'*10+self.headers['Authorization'][-3:]}\n")

    def thread(self):
        if self.query_mode_choice.get() == "个人信息" or self.QUERY.get() != "":
            if self.save_mode_choice.get() == "数据库":
                with open("config.json","r",encoding="utf-8") as f:
                    user_data = json.load(f)
                self.db_name = user_data['db_name']
                self.db_host = user_data['db_host']
                # self.db_port = user_data['db_port']
                self.db_username = user_data['db_username']
                self.db_password = user_data['db_password']
                try:
                    self.conn = pymysql.connect(database=self.db_name,host=self.db_host,user=self.db_username,password=self.db_password)
                except:
                    messagebox.showerror(title='Error',message='[!] 数据库连接失败!')
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
            hs.headers = self.headers
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
            di.headers = self.headers
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
            ws.headers = self.headers
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

        res.headers = self.headers
        if self.query_mode_choice.get() == '个人信息':
            self.log_insert(res.resource(mode="complete"))
        else:
            self.log_insert(f'Complete information has been stored by mode "{self.save_mode_choice.get()}".\n')
            self.log_insert(res.resource(mode="easy"))


if __name__=='__main__':
    root = Tk()
    root.geometry('718x497+350+100')
    root.maxsize(width=718,height=497)
    root.minsize(width=718,height=497)
    root.title('ThunderSearch v1.7.6  --xzajyjs')
    Application(master=root)
    root.mainloop()
