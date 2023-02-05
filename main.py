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
        self.idToInstance[id] = instance
        self.insert(parent, index, **kw, open=True)

    def getInstanceFromId(self, id): return self.idToInstance[id] if id else ''

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
        columns = ("group", 'number', 'name', 'prewait', 'time', "autoplay")
        self.visual_drag = CustomTreeView(
            scene, columns=columns, height=1, show="")
        self.visual_drag.column("#1", minwidth=30, width=30, stretch="NO")
        self.visual_drag.column("#2", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#4", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#5", minwidth=100, width=100, stretch="NO")
        self.visual_drag.column("#6", minwidth=20, width=20, stretch="NO")
        tree.bind("<Motion>", self.bMotion)
        tree.bind("<Button-1>", self.bDown)
        tree.bind("<ButtonRelease-1>", self.bUp)

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
        if self.bdownCount > 10:
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
            self.visual_drag.delete(*self.visual_drag.get_children())
            self.visual_drag.insert(
                '', tk.END, values=row["values"], iid=self.iid, tag=self.tree.item(self.iid)["tags"])
            for item in tv.get_children(tv.selection()):
                self.isParent = True
                self.visual_drag.insert(self.iid, tk.END, values=tv.item(item)["values"], iid=item, tag=self.tree.item(item)["tags"])
            self.visual_drag.place(in_=tv, y=0, x=0, relwidth=1)
            parent = self.tree.parent(self.iid)
            self.tree.delete(tv.selection())
            if parent:
                if self.tree.get_children(parent) == ():
                    self.tree.getInstanceFromId(parent).setChildParent("Parent", False)

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
        tv.insert(parent, rowNum, values=item, iid=self.iid, tag=(self.visual_drag.item(self.visual_drag.get_children()[0])["tags"],))
        for item in self.visual_drag.get_children(self.iid):
            tv.insert(self.iid, tk.END, values=self.visual_drag.item(item)["values"], iid=item, tag=(self.visual_drag.item(item)["tags"],))
        if self.indentation == 0: tv.getInstanceFromId(self.iid[0]).setChildParent("Child", False)
        elif self.indentation == 1:
            # if rows[0].index("dropArea")!=0:
            #     parent=rows[0][rows[0].index("dropArea")-1]
            tv.getInstanceFromId(parent).setChildParent("Parent", True)
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

    def bMotion(self, event):
        tv = event.widget
        if self.visual_drag.winfo_ismapped():
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

    def __init__(self, cueNumber=0, name="Unnamed Cue", prewait=0.0, time=0.0, autoplay="None", open=True, isParent=False, isChild=False, tk=None) -> None:
        self.values = {"cueNumber": cueNumber, "cueName": f"Cue test number {name}", "prewait": prewait, "time": time, "Autoplay": autoplay}
        self.open = open
        self.tk = tk
        self.prewait = prewait
        self.isParent = isParent
        self.isChild = isChild
        self.path = None

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
        return (self.openSymbol(), str(self.values["cueNumber"]), self.nameIndent(), self.sToTime(self.values["prewait"]), self.sToTime(self.values["time"]), ({"None": "", "Follow": "▼", "Follow When Done": "▽"}[self.values["Autoplay"]]))

    def getInstance(self):
        return self

    def changeValue(self, name, newValue):
        self.values[name] = newValue
        if name == "prewait":
            self.prewait = newValue
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

        self.tk.bind('<Escape>', self.stopAllAudio)

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
            if self.selectedCellClass and self.prewaitInput.get() != "":
                try:
                    v = float(self.prewaitInput.get())
                except ValueError:
                    v = 0
                self.selectedCellClass.changeValue("prewait", v)

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
        self.prewaitInput.insert(0, q.values["prewait"])

    def stopAllAudio(self):
        pygame.mixer.music.stop()

    def playAudio(self, q, callback):
        if (p:=q.path):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(p)
            pygame.mixer.music.play()
        if (t:=q.values['time']) == 0: t+=1
        self.tk.after(int(math.ceil(t*1000)), callback)

    def play(self, q, parent):
        print("Started playing", q.values["cueName"])
        self.tree.item(q.iid, tag=("green",))
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
        print(f"Now playing {q.values['cueName']}")

        self.selectNext()
        self.startCue(q)

    def selectNext(self):
        rows = [self.tree.get_children()][0]
        try:
            item=rows[min(rows.index(self.tree.focus())+1, len(rows))]
            iOpen=self.tree.getInstanceFromId(item).open
            self.tree.focus(item)
            self.tree.item(item,open=(not iOpen))
            self.openParent()
        except ValueError:
            try:
                rows = [self.tree.get_children(self.tree.parent(self.tree.focus()))][0]
                self.tree.focus(rows[min(rows.index(self.tree.focus())+1, len(rows))])
            except ValueError: pass
            except IndexError: pass
        self.selectCue(None)

    def newCueFromButton(self):
        nums = []
        for x in self.tree.get_children():
            x = self.tree.getInstanceFromId(x)
            nums.append(x.values['cueNumber'])
        # print(math.ceil(max(nums)+1))
        self.createNewCue(cueNumber=float(math.ceil(max(nums)+1)))

    def createNewCue(self, cueNumber=0, name="New Cue", prewait=0.0, time=0.0, autoplay="None") -> None:
        "Creates a new cue in treeview"
        q = Cue(cueNumber=cueNumber, name=name, prewait=prewait, time=time, autoplay=autoplay, tk=self.tk)
        iid = self.addToTree(q.contense(), q.getInstance())
        q.setRow(self.tree, iid)
        q.updateVisuals()

    def addToTree(self, contense, instance):
        "Adds item to tree view, returns iid"
        self.oddrow = not self.oddrow
        # self.tree.insert('', tk.END, values=contense,tag=(("odd" if self.oddrow else "even"),),iid=f'line{self.iid}')
        self.iid += 1
        self.tree.add('', tk.END, values=contense, tag=(("odd" if self.oddrow else "even"),), iid=f'line{self.iid}', instance=instance)
        return f'line{self.iid}'

    def drawTopbar(self):
        self.topbar = tk.Frame(self.scene, bg="#3d3d3d",highlightcolor="white")
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="nesw")
        self.topbar.grid_rowconfigure(0, weight=10)
        self.topbar.grid_rowconfigure(1, weight=1)
        self.topbar.grid_columnconfigure(0, weight=1)
        self.topbar.grid_columnconfigure(1, weight=8)
        button_border = tk.Frame(self.topbar, highlightbackground="lime", highlightthickness=4)
        button_border.grid(row=0, column=0, sticky="nesw", pady=10)
        goButton = tk.Button(button_border, text="GO", background="#4d4d4d",bd=0, foreground='white', font=("Bold", 50), command=self.startPlay)
        button_border.grid_rowconfigure(0, weight=1)
        button_border.grid_columnconfigure(0, weight=1)
        goButton.grid(row=0, column=0, sticky="nesw")
        topInfoFrame = tk.Frame(self.topbar, bg="#3d3d3d", highlightcolor="green")
        topInfoFrame.grid(row=0, column=1, sticky="nesw")
        topInfoFrame.grid_rowconfigure(0, weight=1)
        topInfoFrame.grid_columnconfigure(0, weight=1)
        var = tk.StringVar()
        var.trace("w", lambda name, index, mode,var=var: self.cueValueChange("title"))
        self.qtitle = tk.Entry(topInfoFrame, textvariable=var, font=(30), bg="#3d3d3d", fg="white")
        self.qtitle.grid(row=0, column=0, sticky="new", padx=10, pady=40)
        topTools = tk.Frame(self.topbar, bg="#3d3d3d", highlightcolor="white")
        topTools.grid(row=1, column=0, sticky="nesw", pady=10, columnspan=2)
        topTools.grid_rowconfigure(0, weight=1)
        for _ in range(50): topTools.grid_columnconfigure(_, weight=1)
        toolBarIcons = [['Audio',"self.newCueFromButton"],['Fade',"lambda:print('Fade')"],*([[' ',"lambda:print('Coming soon!')"]]*20)]
        print(toolBarIcons)
        for i,x in enumerate(toolBarIcons):
            tmpTool = tk.Button(topTools, text=x[0], bg="#4d4d4d", bd=0, fg="white",command=eval(x[1]))
            tmpTool.grid(row=0, column=int(2*i+1.5), sticky="NSEW")

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
        durationInput = tk.Entry(self.bottomBarBasicTab, disabledbackground="#313131", fg="white", state="disabled")
        durationInput.grid(row=1, column=1, sticky="we")
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
        self.scene.grid_rowconfigure(0, weight=1)
        self.scene.grid_rowconfigure(1, weight=3)
        self.scene.grid_rowconfigure(2, weight=5)
        self.scene.grid_columnconfigure(0, weight=10)
        columns = ("group", 'number', 'name', 'prewait', 'time', "autoplay")
        self.tree = CustomTreeView(self.scene, columns=columns, show='headings', selectmode="browse")
        self.tree.heading('number', text='Number')
        self.tree.heading('name', text='Name')
        self.tree.heading('prewait', text='Prewait')
        self.tree.heading('time', text='Time')
        self.tree.heading('autoplay', text='⫯')
        self.tree.column("#1", minwidth=20, width=20, stretch="NO") # Group
        self.tree.column("#2", minwidth=60, width=60, stretch="NO") # Number
        self.tree.column("#3", minwidth=50, width=50, stretch="YES") # Name
        self.tree.column("#4", minwidth=90, width=90, stretch="NO") # Prewait
        self.tree.column("#5", minwidth=90, width=90, stretch="NO") # Time
        self.tree.column("#6", minwidth=30, width=30, stretch="NO") # Autoplay
        self.oddrow = False
        self.iid = 0
        for a in range(100): self.createNewCue(cueNumber=float(a), name=f"{a}")
        self.setTreeColour()
        self.tree.tag_configure("green", background="green", font=("Bold", 11))
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

        self.tree.bind("<Control-R>", self.renumberCues)

    def renumberCues(self, e):
        if not (start := simpledialog.askfloat('Cue renumber', 'Start')): return
        if not (increment := simpledialog.askfloat('Cue renumber', 'Increment')): return
        v = start
        for x in self.tree.get_children():
            x = self.tree.getInstanceFromId(x)
            x.changeValue('cueNumber', f'{float(v):.1f}')
            v += increment

    def selectPath(self):
        q = self.tree.getInstanceFromId(self.tree.focus())
        if (path := filedialog.askopenfilename(title='Select file to add', filetypes=(('Sound', '*.ogg *.wav *.mp3'), ('All files', '*.*')))):
            q.path = path
            print(path)
            if q.values['cueName'].split(' ')[1] == 'test' or q.values['cueName'] == '':
                q.values['cueName'] = f"Play {path.split('/')[-1]}"
            # x = pa.get_duration(*pa.load(path))
            # print(x)
            # print(mediainfo(path)['duration'])
            print(q.values['time'])
            q.values['time'] = sf.info(path).duration
            self.fileInput.config(text=path)
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
