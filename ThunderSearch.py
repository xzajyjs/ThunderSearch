import json
from statistics import mode
import requests
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.createWidget()
        self.pack()
        
    def createWidget(self):
        self.u_label = Label(self, text='账号').grid(row=0,column=0)
        self.p_label = Label(self, text='密码').grid(row=1,column=0)
        self.USERNAME = Entry(self,width=16,borderwidth=1)
        self.USERNAME.grid(row=0,column=1)
        self.PASSWORD = Entry(self,width=16,show="*",borderwidth=1)
        self.PASSWORD.grid(row=1,column=1)
        self.thread_label = Label(self, text='线程数').grid(row=0,column=2)
        self.query_label = Label(self, text='查询语句').grid(row=1,column=2)
        self.thread_choice = StringVar(self)
        self.thread_choice.set('5')
        self.THREAD = OptionMenu(self,self.thread_choice,'1','5','10','20','30')
        self.THREAD.grid(row=0,column=3)
        self.page_label = Label(self,text='查询页数').grid(row=0,column=4)
        self.page_choice = StringVar(self)
        self.page_choice.set('1')
        self.PAGE = OptionMenu(self,self.page_choice,'1','2','3','4','5','10','15','20','30','50','80','100','200','300','500','1000')
        self.PAGE.grid(row=0,column=5)
        self.mode_label = Label(self,text='模式').grid(row=0,column=6)
        self.mode_choice = StringVar(self)
        self.mode_choice.set('主机搜索')
        self.MODE = OptionMenu(self,self.mode_choice,'主机搜索','域名/IP','个人信息')
        self.MODE.grid(row=0,column=7)
        self.START = Button(self,text='一键查询',command=self.thread)
        self.START.grid(row=0,column=8)
        self.QUERY = Entry(self, width=18,borderwidth=1)
        self.QUERY.grid(row=1,column=3,columnspan=4)
        self.file_label = Label(self,text='存储文件名').grid(row=1,column=7)
        self.FILE = Entry(self,width=8,borderwidth=1)
        self.FILE.grid(row=1,column=8)
        self.TREEVIEW = Treeview(self,show='headings')
        self.TREEVIEW.grid(row=2,column=0,columnspan=9)
        self.TREEVIEW['columns'] = ("ID","IP","PORT/DOMAIN","OS")
        self.TREEVIEW.column("ID",width=50)
        self.TREEVIEW.column("IP",width=200)
        self.TREEVIEW.column("PORT/DOMAIN",width=150)
        self.TREEVIEW.column("OS",width=200)
        self.TREEVIEW.heading("ID",text="ID")
        self.TREEVIEW.heading("IP",text="IP")
        self.TREEVIEW.heading("PORT/DOMAIN",text="PORT/DOMAIN")
        self.TREEVIEW.heading("OS",text="OS")
        self.LOG = Text(self,relief=SOLID,borderwidth=1,height=10,width=86)
        self.LOG.grid(row=3,column=0,columnspan=9)

    def delete_tree(self,tree):
        x = tree.get_children()
        for item in x:
            tree.delete(item)

    def log_insert(self,str):       # update log
        self.LOG.insert(END,chars=str)
        self.LOG.see(END)

    def login(self):
        try:
            with open("access_token.txt", "r") as f:
                access_token = f.read().strip('\n')
            self.log_insert("Load file 'access_token.txt' successfully.\n")
        except FileNotFoundError:
            self.log_insert("Fail to find access_token.txt. Need to Login now.\n")
            url = 'https://api.zoomeye.org/user/login'
            data = {
                'username':self.USERNAME.get().strip(),
                'password':self.PASSWORD.get().strip()
            }
            encoded_data = json.dumps(data)
            resp_json = requests.post(url, encoded_data).json()
            try:
                access_token = resp_json['access_token']
            except:
                self.log_insert(f'[-] Login fail. {resp_json["message"]}\n')
            else:
                self.log_insert('[+] Login success!\n')
                with open("access_token.txt", "w") as f:
                    f.write(access_token)

        self.headers = {
            'Authorization':'JWT ' + access_token
        }
        print(self.headers)
        self.log_insert(f"Access_Token: {self.headers['Authorization']}\n")
    
    def thread(self):
        if self.QUERY.get() != "" and self.FILE.get() != "" or self.mode_choice.get() == "个人信息":
            t1 = Thread(target=self.run,daemon=True)
            t1.start()
        else:
            messagebox.showerror(title='Error',message='Query or FilePath empty!')

    def run(self):
        if self.mode_choice.get() != '个人信息':
            self.delete_tree(self.TREEVIEW)
        self.info_list = []
        self.login()
        self.log_insert('Start searching...\n')
        query = self.QUERY.get().replace(" ",'%20')

        if self.mode_choice.get() == '主机搜索':
            self.host_search(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
            j = 1
            with open(self.FILE.get(),"w") as f:
                f.write("ip:port\tcountry\tos\thostname\n")
                for each_dic in self.info_list:
                    self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['port'],each_dic['os']))
                    f.write(f"{each_dic['ip']}:{each_dic['port']},{each_dic['country']},{each_dic['os']},{each_dic['hostname']}\n")
                    j += 1
                    
        if self.mode_choice.get() == '域名/IP':
            self.domain_ip(query=query,page=self.page_choice.get(),thread=int(self.thread_choice.get()))
            j = 1
            with open(self.FILE.get(),"w") as f:
                f.write("ip\tdomain\n")
                for each_dic in self.info_list:
                    self.TREEVIEW.insert("",END,values=(j,each_dic['ip'],each_dic['name'],None))
                    f.write(f"{each_dic['ip']} {each_dic['name']}\n")
                    j += 1

        if self.mode_choice.get() == '个人信息':
            self.resource(mode="complete")

        if self.mode_choice.get() != "个人信息":
            self.log_insert(f'Complete information has been stored into {self.FILE.get()}.\n')
            self.resource(mode="easy")

    def host_search(self, query, page, thread):
        with ThreadPoolExecutor(thread) as t:
            for i in range(1,int(page)+1):
                t.submit(self.host_search_threadpool, query=query, page=i)
        self.log_insert("End of search.\n")

    def host_search_threadpool(self, query, page):
        url = f'https://api.zoomeye.org/host/search?query={query}&page={page}&sub_type=v4&facets=app,os'
        print(url)
        try:
            matches = requests.get(url, headers=self.headers).json()
            for each in matches['matches']:
                each_dic = {}
                each_dic['ip'] = each['ip']
                each_dic['port'] = each['portinfo']['port']
                each_dic['country'] = each['geoinfo']['country']['names']['en']
                each_dic['os'] = each['portinfo']['os']
                each_dic['hostname'] = each['portinfo']['hostname']
                
                self.info_list.append(each_dic)
        except Exception as e:
            if str(e.message) == 'matches':
                print ()
                self.log_insert('[-] info : account was break, excceeding the max limitations\n')
            else:
                print  ()
                self.log_insert(f'[-] info : {str(e.message)}\n')

    def domain_ip(self, query, page, thread):
        with ThreadPoolExecutor(thread) as t:
            for i in range(1,int(page)+1):
                t.submit(self.domain_ip_threadpool, query=query, page=i)
        self.log_insert("End of search.\n")

    def domain_ip_threadpool(self, query, page):
        resp = requests.get(f'https://api.zoomeye.org/domain/search?q={query}&type=0&page={page}', headers=self.headers)
        try:
            for each in resp.json()['list']:
                each_dic = {}
                try:
                    each_dic['ip'] = each['ip']
                except:
                    each_dic['ip'] = None
                each_dic['name'] = each['name']
                self.info_list.append(each_dic)
        except Exception as e:
            if str(e.message) == 'resp':
                print ()
                self.log_insert('[-] info : account was break, excceeding the max limitations\n')
            else:
                print  ()
                self.log_insert(f'[-] info : {str(e.message)}\n')
        
    def resource(self,mode):     # user_info
        resp = requests.get('https://api.zoomeye.org/resources-info', headers=self.headers)
        last = resp.json()['resources']['search']
        if mode == "easy":
            self.log_insert(f"[!] Your account's Remaining query quota: {last} (this month).\n")
        elif mode == "complete":
            inteval = resp.json()['resources']['interval']
            uname = resp.json()['user_info']['name']
            role = resp.json()['user_info']['role']
            expired_at = resp.json()['user_info']['expired_at']
            remain_free_quota = resp.json()['quota_info']['remain_free_quota']
            remain_pay_quota = resp.json()['quota_info']['remain_pay_quota']
            remain_total_quota = resp.json()['quota_info']['remain_total_quota']
            self.log_insert(f'[+] Name: {uname}\n[+] Role: {role}\n[+] Intevel: {inteval}\n[+] Expired_at: {expired_at}\n[+] Remain_free_quota: {remain_free_quota}\n[+] Remain_pay_quota: {remain_pay_quota}\n[+] Remain_total_quota: {remain_total_quota}\n')

if __name__=='__main__':
    root = Tk()
    root.geometry('640x404+450+100')
    root.maxsize(width=640,height=404)
    root.minsize(width=640,height=404)
    root.title('ThunderSearch v1.3')
    Application(master=root)
    root.mainloop()