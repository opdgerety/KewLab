import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, font
from PIL import ImageTk, Image
import soundfile as sf
import os, math, pygame
# import librosa as pa
# from pydub.utils import mediainfo

#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class CustomTreeView(ttk.Treeview):
    def __init__(self, master, **kw) -> None:
        super().__init__(master, **kw)
        self.idToInstance = {}

    def add(self, parent, index, **kw):
        id = kw["iid"]
        instance = kw.pop("instance")
        open=True
        if "open" in kw.keys():
            open=kw.pop("open")
        if instance and instance.isParent:
            open=False
        self.idToInstance[id] = instance
        self.insert(parent, index, **kw, open=open)

    def getInstanceFromId(self, id): return self.idToInstance[id] if id else ''

    def deleteRow(self,item):
        for child in self.get_children(item):
            self.idToInstance.pop(child)
            super().delete(child)
        self.idToInstance.pop(item)
        super().delete(item)

class ImageButton(tk.Button):
    def __init__(self, master,file="",**kwargs) -> None:
        if file:
            self.image=Image.open(file)
        self.master=master
        super().__init__(master,**kwargs)
        self.bind("<Configure>",lambda e:self.updateImage())
        # self.updateImage()
    def updateImage(self):
        width,height=self.winfo_width(),self.winfo_height()
        if width<=0 or height<=0:
            return
        self.newImage=self.image.resize((width,height))
        self.newImage=ImageTk.PhotoImage(self.newImage)
        self.config(image=self.newImage)
        
class ImageEntry(tk.Entry):
    def __init__(self, master,file="",parentBackground="black",percentOfset=0.98,text="",**kwargs) -> None:
        if file:
            self.image=Image.open(file)
        self.percentOfset=percentOfset
        self.frame=tk.Frame(master, bd=0, bg=parentBackground,relief="sunken")
        self.master=master
        self.parentBackground=parentBackground
        self.imageLabel = tk.Label(self.frame)
        self.imageLabel.grid()
        self.textvar=tk.StringVar()
        super().__init__(self.frame,**kwargs,textvariable=self.textvar)
        self.bind("<Configure>",lambda e:self.updateImage())
    def grid(self,**kwargs):
        self.frame.grid(**kwargs)
        self.frame.columnconfigure(0,weight=1)
        self.frame.rowconfigure(0,weight=1)
        super().grid(row=0,column=0,sticky="nesw")
    def updateImage(self):
        self.grid_configure(padx=self.frame.winfo_width()-self.frame.winfo_width()*self.percentOfset)
        width,height=self.frame.winfo_width(),self.frame.winfo_height()
        if width<=0 or height<=0:
            return
        self.newImage=self.image.resize((width,height))
        self.newImage=ImageTk.PhotoImage(self.newImage)
        self.imageLabel.config(image=self.newImage,background=self.parentBackground)

class OptionsDropdown(tk.Frame):
    def __init__(self, master,openButton,parentBackground="black",buttons=[],**kwargs) -> None:
        self.master=master
        self.openButton=openButton
        self.parentBackground=parentBackground
        self.buttons=buttons
        self.imageLabel=False
        self.hidden=True
        super().__init__(master,**kwargs)
        self.openButton.bind("<Enter>",self.enterButton)
        self.openButton.bind("<Leave>",self.exitButton)
        self.bind("<Enter>",self.enterSelf)
        self.bind("<Leave>",self.exitSelf)
    def show(self):
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1,uniform=True)
        self.rowconfigure(1,weight=1,uniform=True)
        self.rowconfigure(2,weight=1,uniform=True)
        self.rowconfigure(3,weight=1,uniform=True)
        self.rowconfigure(4,weight=1,uniform=True)
        self.rowconfigure(5,weight=1,uniform=True)
        p=0
        width,height=self.openButton.winfo_width(),self.openButton.winfo_height()*len(self.buttons)
        for button in self.buttons:
            b=ImageButton(self,file=button[0],bd=0,bg="#474646",activebackground="#474646",width=width,height=height,command=button[1])
            b.grid(row=p,column=0)
            p+=1
        self.place(x=self.openButton.winfo_x(),y=self.openButton.winfo_y()+self.openButton.winfo_height(),width=width,height=height)
    def hide(self):
        if self.hidden:
            self.place_forget()
    def enterButton(self,event):
        self.show()
        self.hidden=False
    def exitButton(self,event):
        self.hidden=True
        self.after(100,self.hide)
    def enterSelf(self,event):
        self.hidden=False
    def exitSelf(self,event):
        self.hidden=True
        self.hide()


#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class TreeViewDragHandler():
    def __init__(self, tree, scene, tk) -> None:
        self.tree = tree
        self.tk = tk
        self.y = 0
        self.startx = 0
        self.indentation = 0
        self.iid = ""
        self.bdown = False
        self.bdownCount = 0
        self.holding = False
        self.isParent = False
        columns = ("group", 'number', 'name',"type", 'prewait', 'time', "autoplay")
        self.visual_drag = CustomTreeView(
            scene, columns=columns, height=1, show="")
        self.visual_drag.column("#1", minwidth=30, width=30, stretch="NO")
        self.visual_drag.column("#2", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#4", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#5", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#6", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#7", minwidth=20, width=20, stretch="NO")
        tree.bind("<Motion>", self.bMotion)
        tree.bind("<Button-1>", self.bDown)
        tree.bind("<ButtonRelease-1>", self.bUp)

    def rebind(self):
        self.tree.bind("<Button-1>", self.bDown)
        self.tree.bind("<ButtonRelease-1>", self.bUp)


    def failsafe(self,event):
        if self.bDown:
            self.tk.after(1000,lambda:self.failsafe(event))
        elif self.holding:
            self.bUp(event)

    def bDown(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        self.bdown = True
        self.tk.after(20, lambda: self.bDownHeld(event))

    def bDownHeld(self, event):
        self.bdownCount += 1
        if not self.bdown:
            self.bdownCount = 0
            return
        if self.bdownCount > 20:
            self.bdownCount = 0
            self.pickUp(event)
        else:
            self.tk.after(20, lambda: self.bDownHeld(event))

    def pickUp(self, event):
        if not self.bdown: return
        tv = event.widget
        if tv.identify_region(event.x, event.y) != 'separator':
            self.holding = True
            self.startx = event.x
            row = tv.item(tv.selection())
            self.iid = (tv.selection())
            if not row["values"]:
                self.holding = False
                return
            self.isParent = False
            self.isOpen=self.tree.getInstanceFromId(self.iid[0]).open
            self.visual_drag.delete(*self.visual_drag.get_children())
            self.visual_drag.insert(
                '', tk.END, values=row["values"], iid=self.iid, tag=self.tree.item(self.iid)["tags"])
            for item in tv.get_children(tv.selection()):
                self.isParent = True
                self.visual_drag.insert(self.iid, tk.END, values=tv.item(item)["values"], iid=item, tag=self.tree.item(item)["tags"])
            self.visual_drag.place(in_=tv, y=self.y, x=0, relwidth=1)
            parent = self.tree.parent(self.iid)
            self.tree.delete(tv.selection())
            if parent:
                if self.tree.get_children(parent) == ():
                    self.tree.getInstanceFromId(parent).setChildParent("Parent", False)
            self.failsafe(event)
            self.bMotion(event,True)

    def bUp(self, event):
        self.bdown = False
        self.bdownCount = 0
        if not self.holding:
            return
        self.holding = False
        tv = event.widget
        y = self.y
        rows = [self.tree.get_children()]
        rowNum = 0
        parent = ""
        for item in self.tree.get_children():
            if item == "dropArea":
                rowNum = self.tree.get_children().index(item)
                break
            for item2 in self.tree.get_children(item):
                if item2 == "dropArea":
                    parent = item
                    rowNum = self.tree.get_children(item).index(item2)
                    break
            if rowNum:
                break
        # try:
        #     rowNum=rows[0].index("dropArea")
        # except ValueError:
        #     rowNum=0
        item = self.visual_drag.item(
            self.visual_drag.get_children()[0])["values"]
        tv.insert(parent, rowNum, values=item, iid=self.iid, tag=(self.visual_drag.item(self.visual_drag.get_children()[0])["tags"],),open=self.isOpen)
        for item in self.visual_drag.get_children(self.iid):
            tv.insert(self.iid, tk.END, values=self.visual_drag.item(item)["values"], iid=item, tag=(self.visual_drag.item(item)["tags"],))
        if self.indentation == 0 or not parent: tv.getInstanceFromId(self.iid[0]).setChildParent("Child", False)
        elif self.indentation == 1:
            # if rows[0].index("dropArea")!=0:
            #     parent=rows[0][rows[0].index("dropArea")-1]
            if parent:
                tv.getInstanceFromId(parent).setChildParent("Parent", True)
            if tv.getInstanceFromId(self.iid[0]):
                tv.getInstanceFromId(self.iid[0]).setChildParent("Child", True)
        self.visual_drag.place_forget()
        for item in self.tree.get_children():
            if self.tree.item(item)['tags'] and self.tree.item(item)['tags'][0][:8] == "dropArea":
                self.tree.delete(item)
                break
            for item in self.tree.get_children(item):
                if self.tree.item(item)['tags'] and self.tree.item(item)['tags'][0][:8] == "dropArea":
                    self.tree.delete(item)
                    break
        self.resetOddEven()

    def bMotion(self, event, specialCase=False):
        tv = event.widget
        if specialCase:
            self.visual_drag.place(x=0,y=self.y)
        if self.visual_drag.winfo_ismapped() or specialCase:
            y = event.y
            if event.x-self.startx < 25 or self.isParent:
                self.visual_drag.place_configure(y=y, x=0)
                self.indentation = 0
            elif event.x-self.startx > 25:
                self.visual_drag.place_configure(y=y, x=50)
                self.indentation = 1
            self.y = y
            rows = [self.tree.get_children()]
            row = self.tree.identify_row(y=y)
            try: rowNum = rows[0].index(row)
            except ValueError: rowNum = 0
            for item in self.tree.get_children():
                if item == "dropArea":
                    self.tree.delete(item)
                    break
                for item in self.tree.get_children(item):
                    if item == "dropArea":
                        self.tree.delete(item)
                        break
                    for item in self.tree.get_children(item):
                        if item == "dropArea": self.tree.delete(item)
            row2 = self.tree.identify_row(y=y)
            parent = ""
            if self.indentation == 1:
                if self.tree.parent(row2):
                    parent = self.tree.parent(row2)
                    rowNum = self.tree.get_children(parent).index(row2)+1
                else:
                    parent = row2
                    rowNum = 0
            # print(parent,rowNum)
            tv.add(parent, rowNum, tag=("dropArea",), iid=f"dropArea", values="", instance=None)
        else:
            self.y = event.y

    def resetOddEven(self):
        odd = False
        for item in self.tree.get_children():
            odd = not odd
            if self.tree.item(item)["tags"][0] not in ['green', 'orange', 'selected']:
                self.tree.item(item, tag=(("odd" if odd else "even"),))
            for item in self.tree.get_children(item):
                odd = not odd
                if self.tree.item(item)["tags"][0] not in ['green', 'orange', 'selected']:
                    self.tree.item(item, tag=(("odd" if odd else "even"),))

#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class Cue():
    "Stores the data for a cue"

    def __init__(self, cueNumber=0, name="Unnamed Cue", prewait=0.0, time=0.0, autoplay="None", open=True, isParent=False, isChild=False, tk=None, path=None,effect=None,target=None,iid=None) -> None:
        self.values = {"cueNumber": cueNumber, "cueName": f"{name}", "prewait": prewait, "time": time, "Autoplay": autoplay}
        self.open = open
        self.tk = tk
        self.prewait = prewait
        self.duration=time
        self.isParent = isParent
        self.isChild = isChild
        self.path = path
        self.channel = None
        self.effect=effect
        self.target=target
        self.iid=iid
        if path and path[-4:]!="None":
            self.duration=sf.info(path).duration
            self.values["time"]=self.duration
        else:
            path=None
        self.isPlaying = False

    def setRow(self, row, iid) -> None:
        "Provides an instance of row"
        self.rowInstance = row
        self.iid = iid

    def setChildParent(self, parentOrChild, val):
        if parentOrChild == "Parent":
            self.isParent = val
        if parentOrChild == "Child":
            self.isChild = val
        self.updateVisuals()

    def nameIndent(self):
        if self.isChild:
            return "        "+self.values["cueName"]
        return self.values["cueName"]

    def openSymbol(self):
        if self.isParent:
            if self.open:
                if self.isChild:
                    return "  v"
                return "v"
            if self.isChild:
                return "  >"
            return ">"
        return ""

    def sToTime(self, s):
        return f"{int(s/60):02d}:{int(s%60):02d}.{f'{(s-int(s)):.3f}'[2:]}"

    def contense(self):
        return (self.openSymbol(), str(self.values["cueNumber"]), self.nameIndent(),("Audio" if not self.effect else self.effect), self.sToTime(self.values["prewait"]), self.sToTime(self.values["time"]), ({"None": "", "Follow": "▼", "Follow When Done": "▽"}[self.values["Autoplay"]]))

    def getInstance(self):
        return self

    def changeValue(self, name, newValue):
        self.values[name] = newValue
        if name == "prewait":
            self.prewait = newValue
        if name == "time":
            self.duration = float(newValue)
        self.updateVisuals()

    def updateVisuals(self):
        self.rowInstance.item(self.iid, values=self.contense())

#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------

class Main():
    def __init__(self) -> None:
        pygame.mixer.init()
        self.dirPath = os.path.dirname(os.path.abspath(__file__))
        self.selectedCellClass = None
        self.globFont = 'aerial'
        pygame.mixer.set_num_channels(100)
        self.activeChannels=list(range(100))
        self.stopping=False

    def setTreeColour(self) -> None:
        "Sets treeview colour"
        style = ttk.Style(self.tk)
        style.theme_use("clam")
        style.configure("Treeview.Heading", background="#4d4d4d", foreground="white", fieldbackground="black")
        style.configure("Treeview", background="#4d4d4d", foreground="white", fieldbackground="#3d3d3d")
        style.configure("Vertical.TScrollbar", troughcolor="#4d4d4d", bordercolor="white", arrowcolor="#4d4d4d")

        def fix(option):
            return [elm for elm in style.map("Treeview", cuery_opt=option) if elm[:2] != ("!disabled", "!selected")]
        style = ttk.Style()
        style.map("Treeview", foreground=fix("foreground"), background=fix("background"))

    def deleteAll(self):
        for q in self.tree.get_children():
            self.tree.deleteRow(q)
        self.cleanLocalFiles()
    
    def delete(self):
        self.tree.deleteRow(self.tree.focus())
        self.cleanLocalFiles()

    def selectFile(self):
        if (path := filedialog.askopenfilename(title='Select file to open', filetypes=(('KewLab v1', '*.klab1'),))):
            self.openFile(path)
        else: return
    def selectSave(self):
        if (path := filedialog.asksaveasfilename(title='Select file to save as', filetypes=(('KewLab v1', '*.klab1'),))):
            self.saveFile(path.replace(".klab1",""))
        else: return
    
    def cleanLocalFiles(self):
        files=[]
        for q in self.tree.idToInstance.keys():
            q=self.tree.getInstanceFromId(q)
            if q and q.path:
                files.append(q.path.replace("\\","/").split('/')[-1])
        for fileName in os.listdir(f"{self.dirPath}\LocalFiles"):
            if fileName not in files:
                os.remove(f"{self.dirPath}\LocalFiles\{fileName}")

    def saveFile(self,path):
        self.cleanLocalFiles()
        with open(f"{path}.klab1","w") as outputFile:
            files=[]
            for fileName in os.listdir(f"{self.dirPath}\LocalFiles"):
                with open(f"{self.dirPath}\LocalFiles\{fileName}","rb") as f:
                    files.append(f"{fileName}<DataSeperator>{f.read()}")
            outputFile.write(f"{'<<FileSeperator>>'.join(files)}")
            outputFile.write("<<<SectionSeperator>>>")
            cues=[]
            for cue in self.tree.get_children():
                q=self.tree.getInstanceFromId(cue)
                if q.path:
                    qpath=q.path.replace('\\','/').split('/')[-1]
                else:
                    qpath=None
                cues.append(f"iid::{q.iid},,,parent::,,,cueNumber::{q.values['cueNumber']},,,name::{q.values['cueName']},,,prewait::float({q.prewait}),,,time::float({q.duration}),,,autoplay::{q.values['Autoplay']},,,isParent::{q.isParent},,,isChild::{q.isChild},,,path::{qpath},,,effect::{q.effect},,,effect::{q.effect},,,target::{q.target}")
                for child in self.tree.get_children(cue):
                    q=self.tree.getInstanceFromId(child)
                    if q.path:
                        qpath=q.path.replace('\\','/').split('/')[-1]
                    else:
                        qpath=None
                    cues.append(f"iid::{q.iid},,,parent::{cue},,,cueNumber::{q.values['cueNumber']},,,name::{q.values['cueName']},,,prewait::float({q.prewait}),,,time::float({q.duration}),,,autoplay::{q.values['Autoplay']},,,isParent::{q.isParent},,,isChild::{q.isChild},,,path::{qpath},,,effect::{q.effect},,,effect::{q.effect},,,target::{q.target}")
            outputFile.write("<<CueSepperator>>".join(cues))
    def openFile(self,path):
        self.deleteAll()
        self.cleanLocalFiles()
        for fileName in os.listdir(f"{self.dirPath}\LocalFiles"):
            os.remove(f"{self.dirPath}\LocalFiles\{fileName}")
        with open(f"{path}","r") as inputFile:
            data=inputFile.read()
            f=data.split("<<<SectionSeperator>>>")
            if len(f)<2:
                return
            files,cues=f
            for row in files.split("<<FileSeperator>>"):
                if row:
                    fileName,fileData=row.split("<DataSeperator>")
                    with open(f"{self.dirPath}\LocalFiles\{fileName}","wb") as f:
                        f.write(eval(fileData))
            for cue in cues.split("<<CueSepperator>>"):
                if cues:
                    cueData = {}
                    for arg in cue.split(",,,"):
                        n,a=arg.split("::")
                        if "float(" in a:
                            a=float(a.replace("float(","")[:-1])
                        elif a == "True":
                            a=True
                        elif a == "False":
                            a=False
                        elif a=="None" and n!="autoplay":
                            a=None
                        cueData[n]=a
                    p=cueData.pop("parent")
                    if cueData:
                        cueData["path"]=f"{self.dirPath}\LocalFiles\{cueData['path']}"
                    self.createNewCueFromKLabFile(p,cueData)

    def initTk(self) -> None:
        "Prepeares the tkinter window"
        self.tk = tk.Tk()
        self.tk.title("KewLab")
        self.scene = tk.Frame(self.tk)
        self.scene.pack(fill="both", expand=True)
        self.tk.option_add("*Font", "aerial 12")
        self.tk.geometry(f"{self.relativeSize('w')}x{self.relativeSize('h')}+-10+0")
        self.tk.iconbitmap(f'{self.dirPath}/Assets/icon.ico')
        ttk.Style().configure("Treeview", background="black", foreground="white", fieldbackground="black")
        self.loadScene(0)
        self.tk.mainloop()

    def relativeSize(self, dir, amount=1) -> float:
        "Returns number of pixels to size something based off screen size"
        return int(self.tk.winfo_screenwidth()*amount) if dir == "w" else int(self.tk.winfo_screenheight()*amount)

    def cueValueChange(self, valueName):
        if valueName == "title":
            if self.selectedCellClass and self.qtitle.get() != "":
                self.selectedCellClass.changeValue("cueName", self.qtitle.get())
                self.qtitle2.delete(0, "end")
                self.qtitle2.insert(0, self.qtitle.get())
        if valueName == "title2":
            if self.selectedCellClass and self.qtitle2.get() != "":
                self.selectedCellClass.changeValue("cueName", self.qtitle2.get())
                self.qtitle.delete(0, "end")
                self.qtitle.insert(0, self.qtitle2.get())
        if valueName == "autoplay":
            if self.selectedCellClass and self.autoplayInputVar.get() != "":
                self.selectedCellClass.changeValue("Autoplay", self.autoplayInputVar.get())
        if valueName == "number":
            if self.selectedCellClass and self.numberInput.get() != "":
                try:
                    v = float(self.numberInput.get())
                except ValueError:
                    v = 0
                self.selectedCellClass.changeValue("cueNumber", v)
        if valueName == "prewait":
            if not self.selectedCellClass.isPlaying:
                if self.selectedCellClass and self.prewaitInput.get() != "":
                    try:
                        v = float(self.prewaitInput.get())
                    except ValueError:
                        v = 0
                    self.selectedCellClass.changeValue("prewait", v)
        if valueName == "duration":
            if not self.selectedCellClass.isPlaying and self.selectedCellClass.effect:
                if self.selectedCellClass and self.prewaitInput.get() != "":
                    try:
                        v = float(self.durationInput.get())
                    except ValueError:
                        v = 0
                    self.selectedCellClass.changeValue("time", v)

    def openParent(self):
        q = self.tree.getInstanceFromId(self.tree.focus())
        q.open = not q.open
        q.updateVisuals()

    def resetOddEven(self, resetSelected=False):
        odd = False
        for item in self.tree.get_children():
            odd = not odd
            if self.tree.item(item)["tags"][0] not in ['green', 'orange', ("selected" if not resetSelected else "")]:
                self.tree.item(item, tag=(("odd" if odd else "even"),))
            for item in self.tree.get_children(item):
                odd = not odd
                if self.tree.item(item)["tags"][0] not in ['green', 'orange', ("selected" if not resetSelected else "")]:
                    self.tree.item(item, tag=(("odd" if odd else "even"),))

    def selectTargetStart(self):
        self.tree.unbind("<Button-1>")
        self.tk.bind("<Escape>", lambda e : self.selectTarget(e,fail=True))
        self.tree.unbind("<<TreeviewSelect>>")
        self.tree.unbind("<ButtonRelease-1>")
        self.tree.bind("<Button-1>", self.selectTarget)
        self.targetSelect.config(bg="#4a6984")
        

    def selectTarget(self,event,fail=False):
        if fail:
            target=None
        else:
            target=self.tree.identify_row(event.y)
        self.tk.after(100,lambda:self.tree.bind("<<TreeviewSelect>>", self.selectCue))
        self.tree.unbind("<Button-1>")
        self.tk.after(500,lambda:self.treedrag.rebind())
        if target!=self.selectedCellClass.iid:
            self.selectedCellClass.target=target
            targetName=self.tree.getInstanceFromId(target)
            if targetName:
                self.targetSelect.config(text=f'Target: {targetName.values["cueName"]}',state="normal",bg="#313131")
            else:
                self.targetSelect.config(text="Select Target",state="normal",bg="#313131")
        else:
            self.targetSelect.config(text="Select Target",state="normal",bg="#313131")
    def selectCue(self, event):
        self.resetOddEven(resetSelected=True)
        self.tree.item(self.tree.focus(), tag=("selected",))
        q = self.tree.getInstanceFromId(self.tree.focus())
        self.selectedCellClass = q
        self.qtitle.delete(0, "end")
        self.qtitle.insert(0, q.values["cueName"])
        self.qtitle2.delete(0, "end")
        self.qtitle2.insert(0, q.values["cueName"])
        self.autoplayInputVar.set(q.values["Autoplay"])
        self.numberInput.delete(0, "end")
        self.numberInput.insert(0, q.values["cueNumber"])
        self.prewaitInput.delete(0, "end")
        self.prewaitInput.insert(0, q.prewait)
        if q.effect:
            # self.fileInput.config(text="",state="disabled")
            self.fileInput.grid_forget()
            self.targetSelect.grid(row=3, column=2, sticky=("ew"), padx=10)
            d=f"{(q.duration):.3f}"
            self.durationInput.config(state="normal")
            self.durationInput.delete(0, "end")
            self.durationInput.insert(0, d)
            target=q.target
            if target:
                targetName=self.tree.getInstanceFromId(target)
                if targetName:
                    self.targetSelect.config(text=f'Target: {targetName.values["cueName"]}',state="normal")
            else:
                self.targetSelect.config(text="Select Target",state="normal") 
        else:
            d=f"{(q.duration):.3f}"
            self.durationInput.config(state="normal")
            self.durationInput.delete(0, "end")
            self.durationInput.insert(0, d)
            self.durationInput.config(state="readonly")
            self.fileInput.grid(row=3, column=2, sticky=("ew"), padx=10)
            self.targetSelect.grid_forget()
            self.fileInput.config(text="",state="normal")
            if q.path:
                fileName=q.path.replace("\\","/").split('/')[-1]
                self.fileInput.config(text=fileName)
            else:
                self.fileInput.config(text="Select Path")
    
    def finnishedStopping(self):
        self.stopping=False

    def stopAllAudio(self,event=None):
        self.stopping=True
        for channel in range(100):
            if channel not in self.activeChannels:
                pygame.mixer.Channel(channel).stop()
        self.tk.after(200,self.finnishedStopping)

    def checkAudioFinished(self,channel,callback,q):
        if not q.effect:
            if not pygame.mixer.Channel(channel).get_busy():
                self.activeChannels.append(channel)
                q.changeValue("time",q.duration)
                q.isPlaying=False
                q.channel=None
                callback()
            else:
                self.tk.after(100,lambda:self.checkAudioFinished(channel,callback,q))
                q.values["time"]-=0.1
                q.updateVisuals()
        else:
            if q.values["time"]<=0:
                q.changeValue("time",q.duration)
                q.isPlaying=False
                q.channel=None
                callback()
            else:
                self.tk.after(100,lambda:self.checkAudioFinished(channel,callback,q))
                q.values["time"]-=0.1
                q.updateVisuals()

    def playAudio(self, q, callback):
        if not q.effect:
            channel=self.activeChannels.pop()
            q.channel=channel
            if (p:=q.path):
                pygame.mixer.Channel(channel).play(pygame.mixer.Sound(p))
            if (t:=q.values['time']) == 0: t+=1
            self.tk.after(100,lambda:self.checkAudioFinished(channel,callback,q))
        elif q.effect=="Fade":
            target=self.tree.getInstanceFromId(q.target)
            if target.isPlaying and target.channel:
                print(f"Fading channel {target.channel} over {q.duration} secconds")
            self.tk.after(100,lambda:self.checkAudioFinished(None,callback,q))
        # self.checkAudioFinnished(channel,callback)
        # self.tk.after(int(math.ceil(t*1000)), callback)

    def play(self, q, parent):
        print("Started playing", q.values["cueName"])
        self.tree.item(q.iid, tag=("green",))
        q.isPlaying=True
        self.playAudio(q,callback=lambda: self.cueEnded(q, parent))

    def prewait(self, q, parent):
        q.values["prewait"] -= 0.1
        q.updateVisuals()
        if q.values["prewait"] <= 0:
            if self.tree.item(q.iid)["tags"][-1] == 'orange':
                self.tree.item(q.iid, tag=("",))
                self.resetOddEven()
            q.values["prewait"] = q.prewait
            q.updateVisuals()
            self.play(q, parent)
        else:
            if self.tree.item(q.iid)["tags"][-1] not in ['orange', 'selected']:
                self.tree.item(q.iid, tag=("orange",))
            self.tk.after(100, lambda: self.prewait(q, parent))

    def cueEnded(self, q, parent):
        if self.tree.item(q.iid)["tags"][-1] == 'green':
            self.tree.item(q.iid, tag=("",))
            self.resetOddEven()
        if not self.stopping:
            if q.values["Autoplay"] == "Follow When Done":
                if self.tree.get_children(q.iid):
                    self.startCue(self.tree.getInstanceFromId(self.tree.get_children(q.iid)[0]), parent=q.iid)
                else:
                    rows = self.tree.get_children()
                    if q.iid in rows:
                        self.startPlay()
                    else:
                        rows = self.tree.get_children(parent)
                        if q.iid not in rows:
                            return
                        i = rows.index(q.iid)
                        if i != len(rows)-1:
                            self.startCue(
                                self.tree.getInstanceFromId(rows[i+1]), parent)
                        elif not self.tree.focus() in rows:
                            self.startPlay()

    def startCue(self, q, parent=""):
        if q.values["prewait"] <= 0:
            self.prewait(q, parent)
        else:
            # self.tree.item(q.iid,tag=("orange",))
            self.tk.after(100, lambda: self.prewait(q, parent))
        if q.values["Autoplay"] == "Follow" or (self.tree.get_children(q.iid) and q.values["Autoplay"] == "None"):
            if self.tree.get_children(q.iid):
                self.startCue(self.tree.getInstanceFromId(self.tree.get_children(q.iid)[0]), parent=q.iid)
            else:
                rows = self.tree.get_children()
                if q.iid in rows:
                    self.startPlay()
                else:
                    rows = self.tree.get_children(parent)
                    i = rows.index(q.iid)
                    if i != len(rows)-1:
                        self.startCue(self.tree.getInstanceFromId(rows[i+1]), parent)
                    elif not self.tree.focus() in rows:
                        self.startPlay()

    def startPlay(self):
        if self.tree.focus() == "": return
        q = self.tree.getInstanceFromId(self.tree.focus())
        self.selectNext()
        self.startCue(q)

    def selectNext(self):
        rows = [self.tree.get_children()][0]
        try:
            item=rows[min(rows.index(self.tree.focus())+1, len(rows)-1)]
            iOpen=self.tree.getInstanceFromId(item).open
            self.tree.focus(item)
            if self.tree.get_children(item):
                self.tree.item(item,open=(not iOpen))
                self.openParent()
            else:
                self.tree.item(item,open=False)
                self.openParent()
        except ValueError:
            try:
                rows = [self.tree.get_children(self.tree.parent(self.tree.focus()))][0]
                self.tree.focus(rows[min(rows.index(self.tree.focus())+1, len(rows))])
            except ValueError: pass
            except IndexError: pass
        self.selectCue(None)
        self.tree.see(self.tree.focus())

    def deleteRow(self,*items) -> None:
        for iid in items:
            self.idToInstance.pop(iid)
            super().delete(iid)
            for child in self.get_children(iid):
                self.idToInstance.pop(child)
                super().delete(child)

    def newCueFromButton(self):
        nums = [0]
        for x in self.tree.get_children():
            x = self.tree.getInstanceFromId(x)
            nums.append(float(x.values['cueNumber']))
        # print(math.ceil(max(nums)+1))
        self.createNewCue(cueNumber=float(math.ceil(max(nums)+1)))
    
    def newFadeFromButton(self):
        nums = [0]
        for x in self.tree.get_children():
            x = self.tree.getInstanceFromId(x)
            nums.append(float(x.values['cueNumber']))
        # print(math.ceil(max(nums)+1))
        self.createNewCue(cueNumber=float(math.ceil(max(nums)+1)),effect="Fade")

    def createNewCue(self, cueNumber=0, name="New Cue", prewait=0.0, time=0.0, autoplay="None", path=None, effect=None) -> None:
        "Creates a new cue in treeview"
        q = Cue(cueNumber=cueNumber, name=name, prewait=prewait, time=time, autoplay=autoplay, path=path, tk=self.tk,effect=effect)
        iid = self.addToTree(q.contense(), q.getInstance())
        q.setRow(self.tree, iid)
        q.updateVisuals()
    
    def createNewCueFromKLabFile(self, parent, kwargs) -> None:
        "Creates a new cue in treeview"
        open=True
        if kwargs["isParent"]:
            open=False
        q = Cue(**kwargs, tk=self.tk,open=open)
        iid = self.addToTree(q.contense(), q.getInstance(),parent=parent,open=open,iid=kwargs["iid"])
        q.setRow(self.tree, iid)
        q.updateVisuals()

    def addToTree(self, contense, instance,parent="",open=True,iid=None):
        "Adds item to tree view, returns iid"
        self.oddrow = not self.oddrow
        # self.tree.insert('', tk.END, values=contense,tag=(("odd" if self.oddrow else "even"),),iid=f'line{self.iid}')
        if not iid:
            self.iid += 1
            iid=f'line{self.iid}'
        else:
            int(iid.replace("line",""))>=self.iid
            self.iid=int(iid.replace("line",""))+1
        self.tree.add(parent, tk.END, values=contense, tag=(("odd" if self.oddrow else "even"),), iid=iid, instance=instance)
        return iid

    def drawTopbar(self):
        self.topbar = tk.Frame(self.scene, bg="#2D2C2C",bd=0)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="nesw")
        self.topbar.grid_rowconfigure(0, weight=2,uniform=True)
        self.topbar.grid_rowconfigure(1, weight=7,uniform=True)
        self.topbar.grid_rowconfigure(2, weight=2,uniform=True)
        self.topbar.grid_columnconfigure(0, weight=1)
        toolbar = tk.Frame(self.topbar, bd=0, bg="#474646")
        toolbar.grid_rowconfigure(0, weight=1)
        toolbar.grid_columnconfigure(0, weight=1,uniform=True)
        toolbar.grid_columnconfigure(1, weight=3,uniform=True)
        toolbar.grid_columnconfigure(2, weight=3,uniform=True)
        toolbar.grid_columnconfigure(3, weight=3,uniform=True)
        toolbar.grid_columnconfigure(4, weight=1,uniform=True)
        toolbar.grid_columnconfigure(5, weight=2,uniform=True)
        toolbar.grid_columnconfigure(6, weight=1,uniform=True)
        toolbar.grid_columnconfigure(7, weight=21,uniform=True)
        toolbar.grid_columnconfigure(8, weight=1,uniform=True)
        toolbar.grid_columnconfigure(9, weight=2,uniform=True)
        toolbar.grid_columnconfigure(10, weight=1,uniform=True)
        toolbar.grid_columnconfigure(11, weight=3,uniform=True)
        toolbar.grid_columnconfigure(12, weight=6,uniform=True)
        toolbar.grid_columnconfigure(13, weight=1,uniform=True)
        toolbar.grid(row=0, column=0, sticky="nsew")
        fileButton=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\Buttonfile.png",bd=0)
        fileButton.grid(row=0,column=1,sticky="news",pady=5,padx=1)
        filedropdown=OptionsDropdown(self.scene,fileButton,buttons=[(f"{self.dirPath}\Assets\Buttons\Buttonopen.png",self.selectFile),(f"{self.dirPath}\Assets\Buttons\Buttonsave.png",self.selectSave),(f"{self.dirPath}\Assets\Buttons\Buttonimportcues.png",self.addCuesFromFolder),(f"{self.dirPath}\Assets\Buttons\Buttonimportcue.png",None),(f"{self.dirPath}\Assets\Buttons\Buttonimport.png",None),(f"{self.dirPath}\Assets\Buttons\Buttonexport.png",None)],parentBackground="#474646",bg="#5B5B5B")
        editButton=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\Buttonedit.png",bd=0)
        editButton.grid(row=0,column=2,sticky="news",pady=5,padx=1)
        filedropdown=OptionsDropdown(self.scene,editButton,buttons=[(f"{self.dirPath}\Assets\Buttons\Buttondelete.png",self.delete),(f"{self.dirPath}\Assets\Buttons\Buttondeleteall.png",self.deleteAll),(f"{self.dirPath}\Assets\Buttons\Buttonnewaudio.png",self.newCueFromButton),(f"{self.dirPath}\Assets\Buttons\Buttonnewfade.png",self.newFadeFromButton),(f"{self.dirPath}\Assets\Buttons\Buttonnewpan.png",None),(f"{self.dirPath}\Assets\Buttons\Buttonreorder.png",self.renumberCues)],parentBackground="#474646",bg="#5B5B5B")
        viewButton=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\Buttonview.png",bd=0)
        viewButton.grid(row=0,column=3,sticky="news",pady=5,padx=1)
        sep=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\horizontalSeperator.png",bd=0)
        sep.grid(row=0,column=5,sticky="news",pady=10,padx=1)
        self.projectTitle=ImageEntry(toolbar,bg="#5B5B5B",file=f"{self.dirPath}\Assets\Buttons\ProjectTitle.png",bd=0,parentBackground="#474646",text="File Title",font=("public sans",))
        self.projectTitle.grid(row=0,column=7,sticky="news",pady=5,padx=1)
        self.projectTitle.insert(0,"Project Title")
        sep=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\horizontalSeperator.png",bd=0)
        sep.grid(row=0,column=9,sticky="news",pady=10,padx=1)
        helpButton=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\Buttonhelp.png",bd=0)
        helpButton.grid(row=0,column=11,sticky="news",pady=5,padx=1)
        libraryButton=ImageButton(toolbar,bg="#474646",activebackground="#474646",file=f"{self.dirPath}\Assets\Buttons\Buttonlibrary.png",bd=0)
        libraryButton.grid(row=0,column=12,sticky="news",pady=5,padx=1)
        topbarMiddle = tk.Frame(self.topbar, bd=0, bg="#2D2C2C")
        topbarMiddle.grid_rowconfigure(0,weight=1)
        topbarMiddle.grid_columnconfigure(0, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(1, weight=9,uniform=True)
        topbarMiddle.grid_columnconfigure(2, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(3, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(4, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(5, weight=23,uniform=True)
        topbarMiddle.grid_columnconfigure(6, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(7, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(8, weight=1,uniform=True)
        topbarMiddle.grid_columnconfigure(9, weight=9,uniform=True)
        topbarMiddle.grid_columnconfigure(10, weight=1,uniform=True)
        topbarMiddle.grid(row=1, column=0, sticky="nsew")
        goButton=ImageButton(topbarMiddle,bg="#2D2C2C",activebackground="#2D2C2C",file=f"{self.dirPath}\Assets\Buttons\ButtonGo.png",bd=0,command=self.startPlay)
        goButton.grid(row=0,column=1,sticky="news",pady=5,padx=1)
        sep=ImageButton(topbarMiddle,bg="#2D2C2C",activebackground="#2D2C2C",file=f"{self.dirPath}\Assets\Buttons\\verticalSeperator.png",bd=0)
        sep.grid(row=0,column=3,sticky="news",pady=5,padx=10)
        sep=ImageButton(topbarMiddle,bg="#2D2C2C",activebackground="#2D2C2C",file=f"{self.dirPath}\Assets\Buttons\\verticalSeperator.png",bd=0)
        sep.grid(row=0,column=7,sticky="news",pady=5,padx=10)
        noButton=ImageButton(topbarMiddle,bg="#2D2C2C",activebackground="#2D2C2C",file=f"{self.dirPath}\Assets\Buttons\ButtonNo.png",bd=0,command=self.stopAllAudio)
        noButton.grid(row=0,column=9,sticky="news",pady=5,padx=1)
        topbarCenter = tk.Frame(topbarMiddle, bd=0, bg="#2D2C2C")
        topbarCenter.grid_rowconfigure(0,weight=1,uniform=True)
        topbarCenter.grid_rowconfigure(1,weight=4,uniform=True)
        topbarCenter.grid_rowconfigure(2,weight=1,uniform=True)
        topbarCenter.grid_rowconfigure(3,weight=4,uniform=True)
        topbarCenter.grid_rowconfigure(4,weight=1,uniform=True)
        topbarCenter.grid_columnconfigure(0, weight=1)
        topbarCenter.grid(row=0, column=5, sticky="nsew")
        self.qtitle=ImageEntry(topbarCenter,bg="#474646",file=f"{self.dirPath}\Assets\Buttons\CueTitle.png",bd=0,parentBackground="#2D2C2C",text="File Title",font=("public sans",),percentOfset=0.98)
        self.qtitle.grid(row=1,column=0,sticky="news",pady=5,padx=1)
        self.qtitle.insert(0,"Cue Title")
        self.qtitle.textvar.trace("w", lambda name, index, mode,var=self.qtitle.textvar: self.cueValueChange("title"))
        notes=ImageEntry(topbarCenter,bg="#474646",file=f"{self.dirPath}\Assets\Buttons\\NoteTitle.png",bd=0,parentBackground="#2D2C2C",text="File Title",font=("public sans",),percentOfset=0.98)
        notes.grid(row=3,column=0,sticky="news",pady=5,padx=1)
        notes.insert(0,"Notes Tmp")
        toolTray = tk.Frame(self.topbar, bd=0, bg="#474646")
        toolTray.grid(row=2, column=0, sticky="nsew")
        toolTray.grid_columnconfigure(0,weight=1,uniform=True)
        toolTray.grid_rowconfigure(0, weight=1)

    def updateBottomTabs(self, tabName):
        self.bottomBarBasicTab.grid_forget()
        self.bottomBarTimeTab.grid_forget()
        self.bottomBarLevelsTab.grid_forget()
        self.bottomBarTrimTab.grid_forget()
        self.bottomBarEffectsTab.grid_forget()
        if tabName == "basic": self.bottomBarBasicTab.grid(row=1, column=0, sticky="nesw")
        if tabName == "time": self.bottomBarTimeTab.grid(row=1, column=0, sticky="nesw")
        if tabName == "level": self.bottomBarLevelsTab.grid(row=1, column=0, sticky="nesw")
        if tabName == "trim": self.bottomBarTrimTab.grid(row=1, column=0, sticky="nesw")
        if tabName == "effects": self.bottomBarEffectsTab.grid(row=1, column=0, sticky="nesw")

    def drawBottomBar(self):
        self.bottombar = tk.Frame(self.scene, bg="#3d3d3d", highlightcolor="white")
        self.bottombar.grid(row=2, column=0, columnspan=2, sticky="nesw")
        self.bottombar.grid_columnconfigure(0, weight=1)
        self.bottombar.grid_rowconfigure(0, weight=1, uniform='row')
        self.bottombar.grid_rowconfigure(1, weight=7, uniform='row')
        accordionTitles = tk.Frame(self.bottombar, bg="#4d4d4d", highlightcolor="white", bd=1)
        accordionTitles.grid(row=0, column=0, sticky="nesw")
        accordionTitles.grid_rowconfigure(0, weight=1)
        for _ in range(10): accordionTitles.grid_columnconfigure(_, weight=1)
        basicTabButton = tk.Button(accordionTitles, text="Basic", bg="#3d3d3d", fg="White", font=(f"{self.globFont} Bold", 12), command=lambda: self.updateBottomTabs("basic"))
        basicTabButton.grid(row=0, column=0, sticky="nesw")
        timeTabButton = tk.Button(accordionTitles, text="Time And Loop", bg="#3d3d3d", fg="White", font=("aerial Bold", 12), command=lambda: self.updateBottomTabs("time"))
        timeTabButton.grid(row=0, column=1, sticky="nesw")
        levelsTabButton = tk.Button(accordionTitles, text="Audio Levels", bg="#3d3d3d", fg="White", font=("aerial Bold", 12), command=lambda: self.updateBottomTabs("levels"))
        levelsTabButton.grid(row=0, column=2, sticky="nesw")
        trimTabButton = tk.Button(accordionTitles, text="Audio Trim", bg="#3d3d3d", fg="White", font=("aerial Bold", 12), command=lambda: self.updateBottomTabs("trim"))
        trimTabButton.grid(row=0, column=3, sticky="nesw")
        effectsTabButton = tk.Button(accordionTitles, text="Audio Effects", bg="#3d3d3d", fg="White", font=("aerial Bold", 12), command=lambda: self.updateBottomTabs("effects"))
        effectsTabButton.grid(row=0, column=4, sticky="nesw")

        self.bottomBarBasicTab = tk.Frame(self.bottombar, bg="#3d3d3d", highlightcolor="white")

        self.bottomBarBasicTab.grid_columnconfigure(0, weight=1)
        self.bottomBarBasicTab.grid_columnconfigure(1, weight=1)
        self.bottomBarBasicTab.grid_columnconfigure(2, weight=10)

        self.bottomBarBasicTab.grid_rowconfigure(0, weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(1, weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(2, weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(3, weight=1, uniform='row')
        self.bottomBarBasicTab.grid_rowconfigure(4, weight=1, uniform='row')

        self.bottomBarBasicTab.grid(row=1, column=0, sticky="nesw")
        numberLabel = tk.Label(self.bottomBarBasicTab,text="Number:", background="#3d3d3d", fg="white")
        numberLabel.grid(row=0, column=0, sticky="nswe")
        durationLabel = tk.Label(self.bottomBarBasicTab, text="Duration:", background="#3d3d3d", fg="white")
        durationLabel.grid(row=1, column=0, sticky="nswe")
        prewaitLabel = tk.Label(self.bottomBarBasicTab, text="Prewait:", background="#3d3d3d", fg="white")
        prewaitLabel.grid(row=2, column=0, sticky="nswe")
        autoplayLabel = tk.Label(self.bottomBarBasicTab, text="Continue:", background="#3d3d3d", fg="white")
        autoplayLabel.grid(row=3, column=0, sticky="nswe")
        var = tk.StringVar()
        self.numberInput = tk.Entry(self.bottomBarBasicTab, textvariable=var, bg="#313131", fg="white")
        var.trace("w", lambda name, index, mode, var=var: self.cueValueChange("number"))
        self.numberInput.grid(row=0, column=1, sticky="we")
        var = tk.StringVar()
        self.durationInput = tk.Entry(self.bottomBarBasicTab,textvariable=var, disabledbackground="#313131",readonlybackground="#313131",background="#313131", fg="white")
        var.trace("w", lambda name, index, mode, var=var: self.cueValueChange("duration"))
        self.durationInput.grid(row=1, column=1, sticky="we")
        var = tk.StringVar()
        self.prewaitInput = tk.Entry(self.bottomBarBasicTab, textvariable=var, bg="#313131", fg="white")
        var.trace("w", lambda name, index, mode, var=var: self.cueValueChange("prewait"))
        self.prewaitInput.grid(row=2, column=1, sticky="we")
        self.autoplayInputVar = tk.StringVar()
        self.autoplayInputVar.set("None")
        autoplayInput = tk.OptionMenu(self.bottomBarBasicTab, self.autoplayInputVar, *["None", "Follow", "Follow When Done"])
        self.autoplayInputVar.trace("w", lambda name, index, mode, var=self.autoplayInputVar: self.cueValueChange("autoplay"))
        autoplayInput.configure(indicatoron=0, compound=tk.RIGHT, image="")
        autoplayInput.config(borderwidth=0, bg="#313131", activebackground="#313131", activeforeground="white", bd=0, fg="white", highlightthickness=0)
        autoplayInput["menu"].config(bg="#313131", activebackground="#313131", activeforeground="white", fg="white")
        autoplayInput.grid(row=3, column=1, sticky="we")
        var = tk.StringVar()
        var.trace("w", lambda name, index, mode, var=var: self.cueValueChange("title2"))
        self.qtitle2 = tk.Entry(self.bottomBarBasicTab, textvariable=var, font=(40), bg="#313131", fg="White")
        self.qtitle2.grid(row=0, column=2, sticky="ew", padx=10)
        notes = tk.Text(self.bottomBarBasicTab, font=(40), bg="#313131", width=1, height=1, fg="white")
        notes.grid(row=1, column=2, sticky="nesw", rowspan=2, padx=10, pady=20)
        self.fileInput = tk.Button(self.bottomBarBasicTab, font=(f'{self.globFont} 10'), bg="#313131", width=1,height=1, fg="white", text="Select Path", command=self.selectPath)
        self.fileInput.grid(row=3, column=2, sticky=("ew"), padx=10)
        self.targetSelect = tk.Button(self.bottomBarBasicTab, font=(40), bg="#313131", fg="White",text="Select Target",command=self.selectTargetStart)

        self.bottomBarTimeTab = tk.Frame(self.bottombar, bg="#3d3d3d", highlightcolor="white")

        self.bottomBarTimeTab.grid_columnconfigure(0, weight=1)
        self.bottomBarTimeTab.grid_columnconfigure(1, weight=1)
        self.bottomBarTimeTab.grid_columnconfigure(2, weight=10)
        self.bottomBarTimeTab.grid_rowconfigure(0, weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(1, weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(2, weight=1)
        self.bottomBarTimeTab.grid_rowconfigure(3, weight=1)

        self.bottomBarLevelsTab = tk.Frame(self.bottombar, bg="#3d3d3d", highlightcolor="white")
        self.bottomBarTrimTab = tk.Frame(self.bottombar, bg="#3d3d3d", highlightcolor="white")
        self.bottomBarEffectsTab = tk.Frame(self.bottombar, bg="#3d3d3d", highlightcolor="white")

    def mainScene(self) -> None:
        "Loads the main scene"
        self.drawTopbar()
        self.scene.grid_rowconfigure(0, weight=2,uniform=True)
        self.scene.grid_rowconfigure(1, weight=4 ,uniform=True)
        self.scene.grid_rowconfigure(2, weight=3,uniform=True)
        self.scene.grid_columnconfigure(0, weight=10)
        columns = ("group", 'number', 'name','type', 'prewait', 'time', "autoplay")
        self.tree = CustomTreeView(self.scene, columns=columns, show='headings', selectmode="browse")
        self.tree.heading('number', text='Number')
        self.tree.heading('name', text='Name')
        self.tree.heading('type', text='Cue Type')
        self.tree.heading('prewait', text='Prewait')
        self.tree.heading('time', text='Time')
        self.tree.heading('autoplay', text='▼')
        self.tree.column("#1", minwidth=20, width=20, stretch="NO") # Group
        self.tree.column("#2", minwidth=60, width=60, stretch="NO") # Number
        self.tree.column("#3", minwidth=50, width=100, stretch="YES") # Name
        self.tree.column("#4", minwidth=100, width=100, stretch="NO") # Type
        self.tree.column("#5", minwidth=90, width=90, stretch="NO") # Prewait
        self.tree.column("#6", minwidth=90, width=90, stretch="NO") # Time
        self.tree.column("#7", minwidth=30, width=30, stretch="NO") # Autoplay
        self.oddrow = False
        self.iid = 0
        # for a in range(100): self.createNewCue(cueNumber=float(a), name=f"Test cue {a}")
        self.setTreeColour()
        self.tree.tag_configure("green",background="green", font=("Bold", 11))
        self.tree.tag_configure("orange", background="orange", font=("Bold", 11))
        self.tree.tag_configure("odd", background="#4d4d4d", foreground="white", font=("Bold", 11))
        self.tree.tag_configure("even", background="#3d3d3d", foreground="white", font=("Bold", 11))
        self.tree.tag_configure("selected", background="#4a6984", foreground="white", font=("Bold", 11))
        self.tree.tag_configure("dropArea", background="#4a6984", foreground="white")
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.scene, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.treedrag = TreeViewDragHandler(self.tree, self.scene, self.tk)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.drawBottomBar()
        self.tree.bind("<<TreeviewSelect>>", self.selectCue)
        self.tree.bind("<<TreeviewOpen>>", lambda e: self.openParent())
        self.tree.bind("<<TreeviewClose>>", lambda e: self.openParent())
        self.tree.bind("<space>", lambda e: self.startPlay())
        self.tree.bind('<Escape>', self.stopAllAudio)
        self.tree.bind("<Control-R>", self.renumberCues)
        self.cleanLocalFiles()

    def addCuesFromFolder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            files = os.listdir(folder_selected)
            for x in files:
                if x.split('.')[-1] in ['wav','ogg','mp3']:
                    nums = [0]
                    for i in self.tree.get_children():
                        i = self.tree.getInstanceFromId(i)
                        nums.append(i.values['cueNumber'])
                    fileName=x.replace("\\","/").split('/')[-1]
                    with open(str(folder_selected+'/'+x),"rb") as inputFile:
                        with open(f"{self.dirPath}\LocalFiles\{fileName}","wb") as outputFile:
                            outputFile.write(inputFile.read())
                    self.createNewCue(cueNumber=float(math.ceil(max(nums)+1)),path=f"{self.dirPath}\LocalFiles\{fileName}",name=f"Play {str(folder_selected+'/'+x).split('/')[-1]}")

    def renumberCues(self, e=None):
        if not (start := simpledialog.askfloat('Cue renumber', 'Start')): return
        if not (increment := simpledialog.askfloat('Cue renumber', 'Increment')): return
        v = start
        for x in self.tree.get_children():
            x = self.tree.getInstanceFromId(x)
            x.changeValue('cueNumber', float(f'{float(v):.1f}'))
            v += increment

    def selectPath(self):
        q = self.tree.getInstanceFromId(self.tree.focus())
        if (path := filedialog.askopenfilename(title='Select file to add', filetypes=(('Sound', '*.ogg *.wav *.mp3'), ('All files', '*.*')))):
            fileName=path.replace("\\","/").split('/')[-1]
            with open(path,"rb") as inputFile:
                with open(f"{self.dirPath}\LocalFiles\{fileName}","wb") as outputFile:
                    outputFile.write(inputFile.read())
            q.path = f"{self.dirPath}\LocalFiles\{fileName}"
            if q.values['cueName'].split(' ')[1] == 'test' or q.values['cueName'] == '':
                q.values['cueName'] = f"Play {path.split('/')[-1]}"
            # x = pa.get_duration(*pa.load(path))
            # print(x)
            # print(mediainfo(path)['duration'])
            q.changeValue('time',sf.info(path).duration)
            self.fileInput.config(text=fileName)
            q.updateVisuals() #ABC
        else: return

    def loadScene(self, scene) -> None:
        "Loads a scene based of scene number"
        self.scene.destroy()
        self.scene = tk.Frame(self.tk)
        self.scene.pack(fill="both", expand=True)
        self.scene.configure(bg="#3d3d3d")
        if scene == 0: self.mainScene()


def run():
    ui = Main()
    ui.initTk()


if __name__ == "__main__":
    run()
