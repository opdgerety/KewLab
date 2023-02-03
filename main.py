import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import os

class CustomTreeView(ttk.Treeview):
    def __init__(self, master,**kw) -> None:
        super().__init__(master, **kw)
        self.idToInstance={}
    def add(self,parent,index,**kw):
        id=kw["iid"]
        instance=kw.pop("instance")
        self.idToInstance[id]=instance
        self.insert(parent,index,**kw)
    def getInstanceFromId(self,id):
        return self.idToInstance[id]
        

class TreeViewDragHandler():
    def __init__(self,tree,scene,tk) -> None:
        self.tree=tree
        self.tk=tk
        self.y=0
        self.iid=""
        self.bdown=False
        self.holding=False
        columns = ("group",'number', 'name', 'prewait', 'time',"autoplay")
        self.visual_drag= CustomTreeView(scene, columns=columns,height=1,show="")
        self.visual_drag.column("#1", minwidth=30, width=30, stretch="NO")
        self.visual_drag.column("#2", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#4", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#5", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#6", minwidth=20, width=20, stretch="NO")
        tree.bind("<Motion>",self.bMotion)
        tree.bind("<Button-1>", self.bDown) 
        tree.bind("<ButtonRelease-1>",self.bUp)
    def bDown(self,event):
        self.bdown=True
        self.tk.after(250,lambda:self.pickUp(event))
    def pickUp(self,event):
        if not self.bdown:
            return
        self.holding=True
        tv = event.widget
        if tv.identify_region(event.x, event.y) != 'separator':
            row = tv.item(tv.selection())
            self.iid = (tv.selection())
            if not row["values"]:
                self.holding=False
                return
            self.visual_drag.delete(*self.visual_drag.get_children())
            self.visual_drag.insert('', tk.END, values=row["values"])
            self.visual_drag.place(in_=tv,y=0, x=0,relwidth=1)
            self.tree.delete(tv.selection())
    def bUp(self,event):
        self.bdown=False
        if not self.holding:
            return
        self.holding=False
        tv = event.widget
        y=self.y
        rows=[self.tree.get_children()]
        # row=self.tree.identify_row(y=y)
        try:
            rowNum=rows[0].index("dropArea")
        except ValueError:
            rowNum=0
        item=self.visual_drag.item(self.visual_drag.get_children()[0])["values"]
        tv.insert('', rowNum,values=item,iid=self.iid)
        self.visual_drag.place_forget()
        for item in self.tree.get_children():
            if self.tree.item(item)['tags'] and self.tree.item(item)['tags'][0][:8]=="dropArea":
                self.tree.delete(item)
        self.resetOddEven()
    def bMotion(self,event):
        tv = event.widget
        if self.visual_drag.winfo_ismapped():
            y = event.y
            self.visual_drag.place_configure(y=y)
            self.y=y
            rows=[self.tree.get_children()]
            row=self.tree.identify_row(y=y)
            try:
                rowNum=rows[0].index(row)
            except ValueError:
                rowNum=0
            for item in self.tree.get_children():
                if self.tree.item(item)['tags'][0][:8]=="dropArea":
                    self.tree.delete(item)
                    break
            if row=="":
                row="1"
            tv.add('', rowNum,tag=("dropArea",),iid=f"dropArea",values="",instance=None)
    def resetOddEven(self):
        odd=False
        for item in self.tree.get_children():
            odd=not odd
            self.tree.item(item,tag=(("odd" if odd else "even"),))
        
class Cue():
    "Stores the data for a cue"
    def __init__(self,cueNumber=0,name="Unnamed Cue",prewait=0.0,time=0.0,autoplay="None") -> None:
        self.values={"cueNumber":cueNumber,"cueName":f"Cue test number {name}","prewait":prewait,"time":time,"Autoplay":autoplay}
    def setRow(self,row,iid) -> None:
        "Provides an instance of row"
        self.rowInstance=row
        self.iid=iid
    def sToTime(self,s):
        return f"{int(s/60):02d}.{int(s%60):02d}.{f'{(s-int(s)):.3f}'[2:]}"
    def contense(self):
        return (">",str(self.values["cueNumber"]),self.values["cueName"],self.sToTime(self.values["prewait"]),self.sToTime(self.values["time"]),({"None":"","Follow":"o"}[self.values["Autoplay"]]))
    def getInstance(self):
        return self
    def changeValue(self,name,newValue):
        self.values[name]=newValue
        self.updateVisuals()
    def updateVisuals(self):
        self.rowInstance.item(self.iid,values=self.contense())


class Main():
    def __init__(self) -> None:
        self.dirPath = os.path.dirname(os.path.abspath(__file__))
        self.selectedCellClass=None
    def setTreeColour(self) -> None:
        "Sets treeview colour"
        style = ttk.Style(self.tk)
        style.theme_use("alt")
        style.configure("Treeview.Heading", background="#4d4d4d", foreground="white", fieldbackground="black")
        style.configure("Treeview", background="#4d4d4d", foreground="white", fieldbackground="#3d3d3d")
        style.configure("Vertical.TScrollbar", troughcolor="#4d4d4d",bordercolor="white", arrowcolor="#4d4d4d")
        def fix(option): 
            return [elm for elm in style.map("Treeview", cuery_opt=option)
                    if elm[:2] != ("!disabled", "!selected")]
        style = ttk.Style()
        style.map("Treeview", 
                foreground=fix("foreground"),
                background=fix("background"))
    def initTk(self) -> None:
        "Prepeares the tkinter window"
        self.tk=tk.Tk()
        self.tk.title("KewLab")
        self.scene=tk.Frame(self.tk)
        self.scene.pack(fill="both", expand=True)         
        self.tk.geometry(f"{self.relativeSize('w')}x{self.relativeSize('h')}+-10+0")
        self.tk.iconbitmap(f'{self.dirPath}/Assets/icon.ico')
        ttk.Style().configure("Treeview", background="black", 
        foreground="white", fieldbackground="black")
        self.loadScene(0)
        self.tk.mainloop()
    def relativeSize(self,dir,amount=1) -> float:
        "Returns number of pixels to size something based off screen size"
        if dir=="w":
            return int(self.tk.winfo_screenwidth()*amount)
        return int(self.tk.winfo_screenheight()*amount)
    def cueValueChange(self,valueName):
        if valueName=="title":
            if self.selectedCellClass and self.qtitle.get()!="":
                self.selectedCellClass.changeValue("cueName",self.qtitle.get())
        if valueName=="autoplay":
            if self.selectedCellClass and self.autoplayInputVar.get()!="":
                self.selectedCellClass.changeValue("Autoplay",self.autoplayInputVar.get())
        if valueName=="number":
            if self.selectedCellClass and self.numberInput.get()!="":
                try:
                    v=float(self.numberInput.get())
                except ValueError:
                    v=0
                self.selectedCellClass.changeValue("cueNumber",v)
        if valueName=="prewait":
            if self.selectedCellClass and self.prewaitInput.get()!="":
                try:
                    v=float(self.prewaitInput.get())
                except ValueError:
                    v=0
                self.selectedCellClass.changeValue("prewait",v)
    def resetOddEven(self):
        odd=False
        for item in self.tree.get_children():
            odd=not odd
            self.tree.item(item,tag=(("odd" if odd else "even"),))
    def selectCue(self,event):
        self.resetOddEven()
        self.tree.item(self.tree.focus(),tag="selected")
        q =self.tree.getInstanceFromId(self.tree.focus())
        self.selectedCellClass=q
        self.qtitle.delete(0,"end")
        self.qtitle.insert(0,q.values["cueName"])
        self.autoplayInputVar.set(q.values["Autoplay"])
        self.numberInput.delete(0,"end")
        self.numberInput.insert(0,q.values["cueNumber"])
    def play(self):
        if self.tree.focus()=="":
            return
        q =self.tree.getInstanceFromId(self.tree.focus())
        print(f"Now playing {q.values['cueName']}")
        self.selectNext()
    def selectNext(self):
        rows=[self.tree.get_children()][0]
        try:
            self.tree.focus(rows[min(rows.index(self.tree.focus())+1,len(rows))])
        except ValueError:
            pass
        self.selectCue(None)
    def createNewCue(self,cueNumber=0,name="New Cue",prewait=0.0,time=0.0,autoplay="None") -> None:
        "Creates a new cue in treeview"
        q=Cue(cueNumber=cueNumber,name=name,prewait=prewait,time=time,autoplay=autoplay)
        iid=self.addToTree(q.contense(),q.getInstance())
        q.setRow(self.tree,iid)

    def addToTree(self,contense,instance):
        "Adds item to tree view, returns iid"
        self.oddrow=not self.oddrow
        # self.tree.insert('', tk.END, values=contense,tag=(("odd" if self.oddrow else "even"),),iid=f'line{self.iid}')
        self.iid+=1
        self.tree.add('', tk.END, values=contense,tag=(("odd" if self.oddrow else "even"),),iid=f'line{self.iid}',instance=instance)
        return f'line{self.iid}'

    def drawTopbar(self):
        self.topbar=tk.Frame(self.scene, bg="#3d3d3d",highlightcolor="white")
        self.topbar.grid(row=0,column=0,columnspan=2,sticky="nesw")
        self.topbar.grid_rowconfigure(0,weight=10)
        self.topbar.grid_rowconfigure(1,weight=1)
        self.topbar.grid_columnconfigure(0,weight=1)
        self.topbar.grid_columnconfigure(1,weight=8)
        button_border = tk.Frame(self.topbar, highlightbackground = "lime", highlightthickness = 4)
        button_border.grid(row=0,column=0,sticky="nesw",pady=10)
        goButton=tk.Button(button_border,text="GO",bg="gray",bd=0,font=("Bold",30),command=self.play)
        button_border.grid_rowconfigure(0,weight=1)
        button_border.grid_columnconfigure(0,weight=1)
        goButton.grid(row=0,column=0,sticky="nesw")
        topInfoFrame=tk.Frame(self.topbar, bg="#3d3d3d",highlightcolor="white")
        topInfoFrame.grid(row=0,column=1,sticky="nesw")
        topInfoFrame.grid_rowconfigure(0,weight=1)
        topInfoFrame.grid_columnconfigure(0,weight=1)
        var = tk.StringVar()
        var.trace("w", lambda name, index,mode, var=var: self.cueValueChange("title"))
        self.qtitle=tk.Entry(topInfoFrame,textvariable=var,font=(30),bg="gray")
        self.qtitle.grid(row=0,column=0,sticky="new",padx=10,pady=40)
        topTools=tk.Frame(self.topbar, bg="#3d3d3d",highlightcolor="white")
        topTools.grid(row=1,column=0,sticky="nesw",pady=10,columnspan=2)
        topTools.grid_rowconfigure(0,weight=1)
        for _ in range(50):
            topTools.grid_columnconfigure(_,weight=1)
        for _ in range(1,49,2):
            tmpTool=tk.Button(topTools,text="T",bg="#4d4d4d",bd=0)
            tmpTool.grid(row=0,column=_,sticky="NSEW")
        tmpTool=tk.Button(topTools,text="T",bg="#4d4d4d",bd=0)
        tmpTool.grid(row=0,column=6,sticky="NSEW")
    def updateBottomTabs(self,tabName):
        self.bottomBarBasicTab.grid_forget()
        self.bottomBarTimeTab.grid_forget()
        self.bottomBarLevelsTab.grid_forget()
        self.bottomBarTrimTab.grid_forget()
        self.bottomBarEffectsTab.grid_forget()
        if tabName=="basic":
            self.bottomBarBasicTab.grid(row=1,column=0,sticky="nesw")
        if tabName=="time":
            self.bottomBarTimeTab.grid(row=1,column=0,sticky="nesw")
        if tabName=="level":
            self.bottomBarLevelsTab.grid(row=1,column=0,sticky="nesw")
        if tabName=="trim":
            self.bottomBarTrimTab.grid(row=1,column=0,sticky="nesw")
        if tabName=="effects":
            self.bottomBarEffectsTab.grid(row=1,column=0,sticky="nesw")

    def drawBottomBar(self):
        self.bottombar=tk.Frame(self.scene, bg="#3d3d3d",highlightcolor="white")
        self.bottombar.grid(row=2,column=0,columnspan=2,sticky="nesw")
        self.bottombar.grid_columnconfigure(0,weight=1)
        self.bottombar.grid_rowconfigure(0,weight=1, uniform='row')
        self.bottombar.grid_rowconfigure(1,weight=7, uniform='row')
        accordionTitles=tk.Frame(self.bottombar, bg="#313131",highlightcolor="white",bd=1)
        accordionTitles.grid(row=0,column=0,sticky="nesw")
        accordionTitles.grid_rowconfigure(0,weight=1)
        for _ in range(10):
            accordionTitles.grid_columnconfigure(_,weight=1)
        basicTabButton=tk.Button(accordionTitles,text="Basic",bg="#3d3d3d",fg="White",font=("Bold",10),command=lambda:self.updateBottomTabs("basic"))
        basicTabButton.grid(row=0,column=0,sticky="nesw")
        timeTabButton=tk.Button(accordionTitles,text="Time And Loop",bg="#3d3d3d",fg="White",font=("Bold",10),command=lambda:self.updateBottomTabs("time"))
        timeTabButton.grid(row=0,column=1,sticky="nesw")
        levelsTabButton=tk.Button(accordionTitles,text="Audio Levels",bg="#3d3d3d",fg="White",font=("Bold",10),command=lambda:self.updateBottomTabs("levels"))
        levelsTabButton.grid(row=0,column=2,sticky="nesw")
        trimTabButton=tk.Button(accordionTitles,text="Audio Trim",bg="#3d3d3d",fg="White",font=("Bold",10),command=lambda:self.updateBottomTabs("trim"))
        trimTabButton.grid(row=0,column=3,sticky="nesw")
        effectsTabButton=tk.Button(accordionTitles,text="Audio Effects",bg="#3d3d3d",fg="White",font=("Bold",10),command=lambda:self.updateBottomTabs("effects"))
        effectsTabButton.grid(row=0,column=4,sticky="nesw")
        self.bottomBarBasicTab=tk.Frame(self.bottombar, bg="#3d3d3d",highlightcolor="white")
        self.bottomBarBasicTab.grid_columnconfigure(0,weight=1)
        self.bottomBarBasicTab.grid_columnconfigure(1,weight=1)
        self.bottomBarBasicTab.grid_columnconfigure(2,weight=10)
        self.bottomBarBasicTab.grid_rowconfigure(0,weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(1,weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(2,weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(3,weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(4,weight=1, uniform='row')
        self.bottomBarBasicTab.grid(row=1,column=0,sticky="nesw")
        numberLabel=tk.Label(self.bottomBarBasicTab,text="Number:",background="#3d3d3d",fg="white")
        numberLabel.grid(row=0,column=0,sticky="nswe")
        durationLabel=tk.Label(self.bottomBarBasicTab,text="Duration:",background="#3d3d3d",fg="white")
        durationLabel.grid(row=1,column=0,sticky="nswe")
        prewaitLabel=tk.Label(self.bottomBarBasicTab,text="Prewait:",background="#3d3d3d",fg="white")
        prewaitLabel.grid(row=2,column=0,sticky="nswe")
        autoplayLabel=tk.Label(self.bottomBarBasicTab,text="Continue:",background="#3d3d3d",fg="white")
        autoplayLabel.grid(row=3,column=0,sticky="nswe")
        var = tk.StringVar()
        self.numberInput=tk.Entry(self.bottomBarBasicTab,textvariable=var,bg="#313131",fg="white")
        var.trace("w", lambda name, index,mode, var=var: self.cueValueChange("number"))
        self.numberInput.grid(row=0,column=1,sticky="we")
        durationInput=tk.Entry(self.bottomBarBasicTab,disabledbackground="#313131",fg="white",state="disabled")
        durationInput.grid(row=1,column=1,sticky="we")
        var = tk.StringVar()
        self.prewaitInput=tk.Entry(self.bottomBarBasicTab,textvariable=var,bg="#313131",fg="white")
        var.trace("w", lambda name, index,mode, var=var: self.cueValueChange("prewait"))
        self.prewaitInput.grid(row=2,column=1,sticky="we")
        self.autoplayInputVar = tk.StringVar()
        self.autoplayInputVar.set("None")
        autoplayInput=tk.OptionMenu( self.bottomBarBasicTab , self.autoplayInputVar , *["None","Follow"])
        self.autoplayInputVar.trace("w", lambda name, index,mode, var=self.autoplayInputVar: self.cueValueChange("autoplay"))
        autoplayInput.configure(indicatoron=0, compound=tk.RIGHT, image="")
        autoplayInput.config(borderwidth=0,bg="#313131",activebackground="#313131",activeforeground="white",bd=0,fg="white",highlightthickness=0)
        autoplayInput["menu"].config(bg="#313131",activebackground="#313131",activeforeground="white",fg="white")
        autoplayInput.grid(row=3,column=1,sticky="we")
        self.bottomBarTimeTab=tk.Frame(self.bottombar, bg="#3d3d3d",highlightcolor="white")
        self.bottomBarTimeTab.grid_columnconfigure(0,weight=1)
        self.bottomBarTimeTab.grid_columnconfigure(1,weight=1)
        self.bottomBarTimeTab.grid_columnconfigure(2,weight=10)
        self.bottomBarTimeTab.grid_rowconfigure(0,weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(1,weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(2,weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(3,weight=1)
        self.bottomBarLevelsTab=tk.Frame(self.bottombar, bg="#3d3d3d",highlightcolor="white")
        self.bottomBarTrimTab=tk.Frame(self.bottombar, bg="#3d3d3d",highlightcolor="white")
        self.bottomBarEffectsTab=tk.Frame(self.bottombar, bg="#3d3d3d",highlightcolor="white")

    def mainScene(self) -> None:
        "Loads the main scene"
        self.drawTopbar()
        self.scene.grid_rowconfigure(0,weight=1)
        self.scene.grid_rowconfigure(1,weight=3)
        self.scene.grid_rowconfigure(2,weight=5)
        self.scene.grid_columnconfigure(0,weight=10)
        columns = ("group",'number', 'name', 'prewait', 'time',"autoplay")
        self.tree = CustomTreeView(self.scene,columns=columns, show='headings',selectmode="browse")
        self.tree.heading('number', text='Number')
        self.tree.heading('name', text='Name')
        self.tree.heading('prewait', text='Prewait')
        self.tree.heading('time', text='Time')
        self.tree.heading('autoplay', text='⫯')
        self.tree.column("#1", minwidth=30, width=30, stretch="NO")
        self.tree.column("#2", minwidth=100, width=100, stretch="NO")
        self.tree.column("#4", minwidth=100, width=100, stretch="NO")
        self.tree.column("#5", minwidth=100, width=100, stretch="NO")
        self.tree.column("#6", minwidth=20, width=20, stretch="NO")
        self.oddrow=False
        self.iid=0
        for a in range(100):
            self.createNewCue(cueNumber=float(a),name=f"{a}")
        self.setTreeColour()
        self.tree.tag_configure("odd",background="#4d4d4d",foreground="white",font=("Bold",11))
        self.tree.tag_configure("even",background="#3d3d3d",foreground="white",font=("Bold",11))
        self.tree.tag_configure("selected",background="#4a6984",foreground="white",font=("Bold",11))
        self.tree.tag_configure("dropArea",background="#4a6984",foreground="white")
        self.tree.grid(row=1,column=0,sticky="nsew")
        scrollbar = ttk.Scrollbar(self.scene, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.treedrag=TreeViewDragHandler(self.tree,self.scene,self.tk)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.drawBottomBar()
        self.tree.bind("<<TreeviewSelect>>",self.selectCue)
        self.tree.bind("<space>",lambda e:self.play())
        
    def loadScene(self,scene) -> None:
        "Loads a scene based of scene number"
        self.scene.destroy()
        self.scene=tk.Frame(self.tk)
        self.scene.pack(fill="both", expand=True)
        self.scene.configure(bg="#3d3d3d")
        if scene==0:
            self.mainScene()
        
def run():
    ui=Main()
    ui.initTk()
    
if __name__=="__main__":
    run()
