import tkinter as tk
import Manager
import FPGrowthDONE

class Window():
    
    @staticmethod
    def ConfigWindow(win, name, xFraction, yFraction, bgColour):
        #root.resizable(False, False)
        screenWidth = win.winfo_screenwidth()
        screenHeight = win.winfo_screenheight()
        windowWidth = int(screenWidth/xFraction)
        windowHeight = int(screenHeight/yFraction)
        win.title(name)
        win.configure(bg=bgColour)
        win.geometry(f"{windowWidth}x{windowHeight}+{int((screenWidth-windowWidth)/2)}+{int((screenHeight-windowHeight)/2)}")
        
        return (windowWidth, windowHeight)
    

class App(tk.Tk):
    
    def __init__(self, xFraction, yFraction, autoClose = False):
        super().__init__()
        #self.root.resizable(False, False)
        bgColour="snow2"
        Window.ConfigWindow(self, "Loading", xFraction, yFraction, bgColour)
        self.user = None
        self.popupOpen = False
        self.prefs = []
        self.__autoClose = autoClose
        self.__LoginWin(xFraction, yFraction, bgColour, autoClose)    
    
    def __LoginWin(self, xFraction, yFraction, bgColour, autoClose):
        def TryLogin():
            successful = False
            email = emailVar.get().lower()
            password = passVar.get()
            userId = Manager.Login(email, password)
            if userId:
                tryAgain["text"] = "Success"
                tryAgain["fg"] = "black"
                
                self.user = userId
                if self.__autoClose:
                    self.destroy()
                    return
                self.__MainPage()
            else:
                colours = {"black" : "red", "red":"black"}
                tryAgain["text"] = "Email or password invalid"
                tryAgain["fg"] = colours[tryAgain["fg"]]
        
        def CreateAccount():
            email = emailVar.get().lower()
            password = passVar.get()
            tryAgain["fg"] = "red"
            if Manager.Login(email, password) is not None:
                tryAgain["text"] = "Email already in use"
            elif len(email) < 3:
                tryAgain["text"] = "Please enter a vaild email"
            elif email.count("@") > 1 or email.count("@") < 1:
                tryAgain["text"] = "@ must be used once"
            elif len(password) < 4:
                tryAgain["text"] = "Password must be more than 3 characters"
            else:
                from random import randint
                code = str(randint(0,9999999))
                message = f"Use the following code to complete account creation: {code}."
                
                tryAgain["fg"] = "black"
                tryAgain["text"] = "Code sent to email"  
                if not self.popupOpen:
                    message = Manager.CreateEmailMessage("Creating Account", email, message)
                    Manager.SendMessage(email, message)
                    popUp = Popup(self, code=code, email=email, password=password)
                       
        width, height = Window.ConfigWindow(self, "Login", xFraction, yFraction, bgColour)
        emailVar = tk.StringVar()
        passVar = tk.StringVar()

        tk.Label(self, text="Login", font=("Calibri Light", 18), bg=bgColour).pack(pady=int(height/100))

        tk.Label(self, text="Email Address", font=("Calibri Light", 12), bg=bgColour).pack(anchor="w", padx=int(width/10))
        emailInput = tk.Entry(self, font=("Courier New", 15), width=width, textvariable=emailVar).pack(anchor="w", padx=int(width/10))

        tk.Label(self, text="Password", font=("Calibri Light", 12), bg=bgColour).pack(anchor="w", padx=int(width/10))
        passwordInput = tk.Entry(self, font=("Courier New", 15), show="*", width=width, textvariable=passVar).pack(anchor="w", padx=int(width/10))

        tryAgain = tk.Label(self, text="", font=("Calibri Light", 12), bg=bgColour, fg="black")
        tryAgain.pack(anchor="center", side="bottom")
        tk.Button(self, text="Log in", command=TryLogin).pack(anchor="n", side="left", padx=int(width/10), pady=int(height/50))
        tk.Button(self, text="Sign up", command=CreateAccount).pack(anchor="n", side="right", padx=int(width/10), pady=int(height/50))
        
    def __MainPage(self):
        for widget in self.winfo_children():
            widget.destroy()
        bgColour = "slategray4"
        width, height = Window.ConfigWindow(self, "App", 1.5, 1.5, "slategray4")
        padHeight = height*0.005
        padWidth = width*0.005
        self.columnconfigure(0, weight=1, uniform="c1")
        self.columnconfigure(1, weight=2, uniform="c1")
        self.rowconfigure(0, weight=1, uniform="r1")
        self.rowconfigure(1, weight=1, uniform="r1")
        
        optionsBg = "slategray1"
        optionsFrame = tk.Frame(self, bg="slategray2")
        prefLabel = tk.Label(optionsFrame, text="Preferences", font=("Calibri Light", 15), bg="slategray2").pack(pady=padHeight)
        optionsFrame.grid(row=0, rowspan=2, column=0, sticky="nesw", padx=(0, padWidth))
        configFrame = tk.Frame(optionsFrame, bg=bgColour)
        configFrame.pack(fill="both", expand=True, padx=padWidth*2, pady=(padHeight, padHeight*4))
        
        loadedPrefs = Manager.GetPrefs(self.user)
        
        heading = tk.Frame(configFrame, bg=bgColour)
        for i in range(len(loadedPrefs[0])-1):
            heading.columnconfigure(i, weight=1, uniform="g2")
        heading.pack(fill="x", anchor="center")
        
        tk.Label(heading, text=f"Event Type", fg="white", bg=bgColour).grid(column=0, row=0, sticky="w", padx=10)
        tk.Label(heading, text=f"Notif Freq (days)", fg="white", bg=bgColour).grid(column=1, row=0, sticky="w")
        tk.Label(heading, text=f"Notify", fg="white", bg=bgColour).grid(column=2, row=0, sticky="w")
        tk.Label(heading, text=f"Critical", fg="white", bg=bgColour).grid(column=3, row=0, sticky="w")
        
        for i in loadedPrefs:
            preference = Preference(configFrame, i)
            preference.pack(anchor="center", fill="x")
            self.prefs.append(preference)
        
        submitFrame = tk.Frame(configFrame, bg=bgColour)
        submitFrame.pack(padx=10, pady=10, anchor="w")
        tk.Button(submitFrame, text="Apply Changes", command=self.__UpdatePreferences).pack(anchor="w", side="left")
        tk.Button(submitFrame, text="Revert Changes", command=self.__RevertChanges).pack(anchor="w", side="left", padx=10)
        
        infoFrame = tk.Frame(self, bg="slategray2")
        infoFrame.grid(row=0, column=1, sticky="nesw", pady=(0, padHeight/2))
        infoText = tk.Text(infoFrame, bg="slategray2", font=("Calibri Light", 12))
        infoGreeting = """WELCOME!

Here you can change adjust your notification settings to match your preferences and also see all your discovered trends.
The preferences window on the left has a few settings you can adjust:
Notification frequency - the number of days between each email you recieve about a specific event.
Notify - toggles whether or not you are sent an email regardless of the notification frequency.
Critical - toggles wheter an event is critical. Whenever a critical event is detected you are immediately sent an email to notify you.

The trends window below is tells you the relationships between events and when they are detected. It is formatted in this style:

[antecedent] => [consequent] : confidence

The antecedent contains the conditions in which the consequent happens, and the confidence tells you how frequently the antecedent happens in proportion to the consequent.

Trend times should be rounded to the nearest hour, and reflect the entire timeframe rounding to that hour. (11:58 -> 12:00, which includes 11:30-12:30)"""
        infoText.insert(tk.END, infoGreeting)
        infoText.pack(fill="both", expand=True)
        
        trendsFrame = tk.Frame(self, bg="slategray2")
        trendsFrame.grid(row=1, column=1, sticky="nesw", pady=(padHeight/2, 0))
        verticalScroll = tk.Scrollbar(trendsFrame)
        verticalScroll.pack(side="right", fill="y")
        horizontalScroll = tk.Scrollbar(trendsFrame, orient="horizontal")
        horizontalScroll.pack(side="bottom", fill="x")
        trendText = tk.Text(trendsFrame, wrap="none", bg="slategray2", font=("Calibri Light", 15),
                            yscrollcommand = verticalScroll.set, xscrollcommand=horizontalScroll.set)
        verticalScroll.config(command=trendText.yview)
        horizontalScroll.config(command=trendText.xview)
        
        antecendents, consequents, confidences = FPGrowthDONE.CreateRules(self.user)
        antecendents, consequents = Manager.ConvertEventId(antecendents, consequents)
        for i in range(len(confidences)):
            antecendent = ", ".join(antecendents[i])
            consequent = ", ".join(consequents[i])
            confidence = confidences[i]
            trendText.insert(tk.END, f"{antecendent} => {consequent} : {confidence}\n")
        trendText.pack(fill="both", expand=True)
        
        
    def __UpdatePreferences(self):
        for pref in self.prefs:
            notify, freq, critical, evntId = pref.Apply()
            Manager.UpdatePrefs(self.user, notify, freq, critical, evntId)
        
    def __RevertChanges(self):
        for pref in self.prefs:
            pref.Revert()
        
class Preference(tk.Frame):
    def __init__(self, parent, data):
        bgColour = parent["bg"]
        super().__init__(parent, bg=bgColour)
        for i in range(len(data)-1):
            self.columnconfigure(i, weight=1, uniform="col")

        tk.Label(self, text=f"{data[0]}", anchor="w", fg="white", font=("Calibri Light",12), bg=bgColour).grid(row=0, column=0, sticky="w", padx=10)
        durations = [1, 2, 3, 4, 5, 6, 7]
        self.evntId = data[4]
        self.freqVar = tk.IntVar()
        self.notifyVar = tk.IntVar()
        self.criticalVar = tk.IntVar()
        self.previousFreq = data[1]
        self.previousNotify = data[2]
        self.previousCritical = data[3]
        self.freqVar.set(self.previousFreq)
        self.notifFreq = tk.OptionMenu(self, self.freqVar, *durations)
        self.notifFreq.grid(row=0, column=1, sticky = "w")
        self.notifyVar.set(self.previousNotify)
        self.notify = tk.Checkbutton(self, variable=self.notifyVar, onvalue=1, offvalue=0, bg=bgColour)
        self.notify.grid(row=0, column=2, sticky="w")
        self.criticalVar.set(self.previousCritical)
        self.critical = tk.Checkbutton(self, variable=self.criticalVar, onvalue=1, offvalue=0, bg=bgColour)
        self.critical.grid(row=0, column=3, sticky="w")
        
    def Revert(self):
        self.notifyVar.set(self.previousNotify)
        self.freqVar.set(self.previousFreq)
        self.criticalVar.set(self.previousCritical)
        
    def Apply(self):
        self.previousNotify = self.notifyVar.get()
        self.previousFreq = self.freqVar.get()
        self.previousCritical = self.criticalVar.get()
        return (self.previousNotify, self.previousFreq, self.previousCritical, self.evntId)
        

class Popup(tk.Toplevel):    
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.inputVar = tk.StringVar()
        self.parent = parent
        self.grab_set()
        self.parent.popupOpen = True
        self.extra = kwargs

        self.width, self.height = Window.ConfigWindow(self, "Code", 8, 8, "lavender blush")
        self.input = tk.Entry(self, font=("Courier New", 15), width=self.width, textvariable=self.inputVar).pack(anchor="center", padx=int(self.width/10), pady=(int(self.height/3), 0))
        self.protocol("WM_DELETE_WINDOW", self.OnClose)
        if "code" in self.extra and "password" in self.extra and "email" in self.extra: 
            tk.Button(self, text="Ok", command=self.Verify).pack(anchor="center", padx=int(self.width/10), pady=int(self.height/50))
    
    def Show():
        self.deiconify()
    
    def Hide():
        self.withdraw()
        
    def OnClose(self):
        self.parent.popupOpen = False
        self.destroy()
            
    def Verify(self):
        enteredCode = self.inputVar.get()
        if enteredCode == self.extra["code"]:                
            self.OnClose()
            Manager.AddUser(self.extra["email"], self.extra["password"])
        
if __name__ == "__main__":
    app = App(4, 4)
    app.mainloop()
else:
    app = App(4, 4, True)
    app.mainloop()