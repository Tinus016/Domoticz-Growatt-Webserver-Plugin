########################################################################################
#   Growatt Inverter Python Plugin for Domoticz                                        #
#                                                                                      #
#   MIT License                                                                        #
#                                                                                      #
#   Copyright (c) 2018 tixi                                                            #
#                                                                                      #
#   Permission is hereby granted, free of charge, to any person obtaining a copy       #
#   of this software and associated documentation files (the "Software"), to deal      #
#   in the Software without restriction, including without limitation the rights       #
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell          #
#   copies of the Software, and to permit persons to whom the Software is              #
#   furnished to do so, subject to the following conditions:                           #
#                                                                                      #
#   The above copyright notice and this permission notice shall be included in all     #
#   copies or substantial portions of the Software.                                    #
#                                                                                      #
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR         #
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,           #
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE        #
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER             #
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,      #
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE      #
#   SOFTWARE.                                                                          #
#                                                                                      #
#   Original Author: sincze                                                            #
#   Eddited by M de Boer (Tinus016 at GittHub)                                         #
#                                                                                      #
#   This plugin will read the status from the running inverter via the webservice.     #
#                                                                                      #
#   V 1.0.0. Initial Release (25-08-2019)                                              #
#   V 1.0.1. Co2 counter and Alarm switch added 12-03-2022 by MBR (Tinus016)           # 
########################################################################################


"""
<plugin key="GrowattWeb" name="Growatt Web Inverter" author="Sincze eddited by Tinus016" version="1.0.1" externallink="https://github.com/sincze/Domoticz-Growatt-Webserver-Plugin">
    <description>
        <h2>Retrieve available Growatt Inverter information from the webservice</h2><br/>        
    </description>
    <params>
        <param field="Address" label="Server Address" width="200px" required="true" default="server-api.growatt.com"/>
        <param field="Mode2" label="Portal Username" width="200px" required="true" default="admin"/>
        <param field="Mode3" label="Portal Password" width="200px" required="true" password="true"/>
        <param field="Mode1" label="Protocol" width="75px">
            <options>
                <option label="HTTPS" value="443"/>
                <option label="HTTP" value="80"  default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

try:
    import Domoticz
    import hashlib
    import json
    import re               # Needed to extract data from Some JSON result

    local = False
except ImportError:
    local = True
    import fakeDomoticz as Domoticz
    from fakeDomoticz import Devices
    from fakeDomoticz import Parameters

class BasePlugin:
    httpConn = None
    runAgain = 6
    disconnectCount = 0
    sProtocol = "HTTP"
    cookieAvailable = False
    sessionId=""
    serverId=""
    plantId = ""
    serialnumber = ""
   
    def __init__(self):
        return

    def apiRequestHeaders(self):        # Needed headers for Login Function
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',            
            'Connection': 'keep-alive',
            'Host': 'server-api.growatt.com',
            'User-Agent': 'Domoticz/1.0',
            'Accept-Encoding': 'gzip'
        }
    
    def apiRequestHeaders_cookie(self): # Needed headers for Data retrieval
        return {
            'Verb': 'POST',
            'URL': '/newTwoPlantAPI.do?op=getUserCenterEnertyDataByPlantid',
            'Headers' : { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',                         
                          'Connection': 'keep-alive',
                          'Host': 'server-api.growatt.com',
                          'User-Agent': 'Domoticz/1.0',
                          'Accept-Encoding': 'gzip',
                          'Cookie': ['JSESSIONID='+self.sessionId, 'SERVERID='+self.serverId]
                        },
            'Data': "plantId="+str(self.plantId)+"&language=1"
        }

# Future use
#    def apiRequestHeaders_serialnumber(self):
#        return {
#            'Verb': 'GET',
#            'URL': "/newTwoPlantAPI.do?op=getAllDeviceList&plantId="+str(self.plantId)+"&content=",
#            'Headers' : { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',                         
#                          'Connection': 'keep-alive',
#                          'Host': 'server-api.growatt.com',
#                          'User-Agent': 'Domoticz/1.0',
#                          'Accept-Encoding': 'gzip',
#                          'Cookie': ['JSESSIONID='+self.sessionId, 'SERVERID='+self.serverId]
#                        },
#        }
    
    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        # Check if devices need to be created
        createDevices()

        if (Parameters["Mode1"] == "443"): self.sProtocol = "HTTPS"
        self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Mode1"])
        self.httpConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Growatt connected successfully.")            
            password=Parameters["Mode3"]
            password=hashlib.md5(str.encode(password))
            sendData = { 'Verb' : 'POST',
                         'URL'  : '/newTwoLoginAPI.do',
                         'Headers' : self.apiRequestHeaders(),
                         'Data': "password="+password.hexdigest()+"&userName="+Parameters["Mode2"]
                         }
            Domoticz.Debug("Step 1. Login SendData: "+str(sendData))
            Connection.Send(sendData)
            UpdateDevice(Unit=3, nValue=1, sValue="On", TimedOut=0)         # Inverter device is on
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
            UpdateDevice(Unit=3, nValue=0, sValue="Off", TimedOut=0)        # Inverter device is off

    def onMessage(self, Connection, Data):
        DumpHTTPResponseToLog(Data)
        
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        LogMessage(strData)

        if (Status == 200):
            apiResponse = json.loads(strData)
            Domoticz.Debug("Retrieved following json: "+json.dumps(apiResponse))
            
            try:
                if ('back' in apiResponse):              
                #if not ['back']['success']:
                #    Domoticz.Log("Login Failed")
                #elif ('back' in apiResponse):                  
                    Domoticz.Log("Login Succesfull")
                    self.plantId = apiResponse["back"]["data"][0]["plantId"]
                    Domoticz.Log("Plant ID: "+str(self.plantId)+" was found")
                    self.ProcessCookie(Data)                                        # The Cookie is in the RAW Response, not in the JSON
                    if not self.cookieAvailable:
                        Domoticz.Debug("No cookie extracted!")
                    else:
                        Domoticz.Debug("Request Data with retrieved cookie!")                    
                        Connection.Send(self.apiRequestHeaders_cookie() )                    
                elif ('powerValue' in apiResponse):
                    current = apiResponse['powerValue']
                    total = apiResponse['totalValue']
                    co2 = apiResponse['formulaCo2Vlue']
                    alarm = apiResponse['alarmValue']
                    sValue=str(current)+";"+str( float(total)*1000)                 # Convert kWh to Wh
                    Domoticz.Log("Currently producing: "+str(current)+" Watt. Totall produced: "+str(total)+" kWh in Wh that is: "+str(float(total)*1000) )
                    UpdateDevice(Unit=1, nValue=0, sValue=sValue, TimedOut=0)
                    UpdateDevice(Unit=2, nValue=0, sValue=current, TimedOut=0)
                    UpdateDevice(Unit=4, nValue=0, sValue=co2, TimedOut=0)
                    if (alarm == 1):
                        UpdateDevice(Unit=5, nValue=1, sValue="On", TimedOut=0)         # Inverter has an Alarm
                    else:
                        UpdateDevice(Unit=5, nValue=0, sValue="Off", TimedOut=0)         # Inverter has no Alarm
                else:
                    Domoticz.Debug("Not received anything usefull!")
            except KeyError:
                Domoticz.Debug("No defined keys found!")
            
        elif (Status == 400):
            Domoticz.Error("Google returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Google returned a Server Error.")
        else:
            Domoticz.Error("Google returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        #Domoticz.Trace(True)
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
                    self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Mode1"])
                self.httpConn.Connect()
                self.runAgain = 6
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")
        #Domoticz.Trace(False)


    def ProcessCookie(self, httpDict):
        if isinstance(httpDict, dict):            
            Domoticz.Debug("Analyzing Data ("+str(len(httpDict))+"):")
            for x in httpDict:
                if isinstance(httpDict[x], dict):
                    if (x == "Headers"):
                        Domoticz.Debug("---> Headers found")    
                        for y in httpDict[x]:
                            # Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
                            if (y == "Set-Cookie"):        
                                Domoticz.Debug("---> Process Cookie Started")
                                try:
                                    self.sessionId = re.search(r"(?<=JSESSIONID=).*?(?=;)", str(httpDict[x][y])).group(0)
                                    Domoticz.Debug("---> SessionID found: "+ str(self.sessionId)) 
                                    self.cookieAvailable = True
                                except AttributeError:
                                    self.cookieAvailable = False
                                    Domoticz.Debug("---> SessionID NOT found") 

                                if self.cookieAvailable:
                                    try:
                                        self.serverId = re.search(r"(?<=SERVERID=).*?(?=;)", str(httpDict[x][y])).group(0)
                                        Domoticz.Debug("---> ServerID found: "+ str(self.serverId)) 
                                    except AttributeError:
                                        self.cookieAvailable = False
                                        Domoticz.Debug("---> ServerID NOT found") 


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
       
def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return


#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():

    # Images
    # Check if images are in database
    if "Growatt" not in Images:
        Domoticz.Image("Growatt.zip").Create()
        image = Images["Growatt"].ID # Get id from database
        Domoticz.Log( "Image created. ID: " + str( image ) )

    # Are there any devices?
    ###if len(Devices) != 0:
        # Could be the user deleted some devices, so do nothing
        ###return

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.
    if (len(Devices) == 0):
        Domoticz.Device(Name="Inverter (kWh)", Unit=1, TypeName="kWh", Used=1).Create()
        Domoticz.Log("Inverter Device kWh created.")
        Domoticz.Device(Name="Inverter (W)", Unit=2, TypeName="Usage", Used=1).Create()
        Domoticz.Log("Inverter Device (W) created.")
        Domoticz.Device(Name="Inverter Status", Unit=3, TypeName="Switch", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (Switch) created.")
        Domoticz.Device(Name="Inverter (Co2)", Unit=4, TypeName="Custom", Used=1).Create()
        Domoticz.Log("Inverter Device (Co2) created.")
        Domoticz.Device(Name="Inverter Alarm", Unit=5, TypeName="Switch", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (Switch) created.")
