# Domoticz-Growatt-Webserver-Plugin

A Domoticz Python Plugin that can read data from the Growatt webserver interface into your Domoticz.

This verion includes also C02 reduction counter and a inverter alarm switch.

![devices](https://github.com/sincze/Domoticz-Growatt-Webserver-Plugin/blob/master/Growatt-Image.png)

## ONLY TESTED FOR Raspberry Pi

With Python version 3.7.3. & Domoticz V2023.1


## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/Tinus016/Domoticz-Growatt-Webserver-Plugin
cd Domoticz-Growatt-Webserver-Plugin

# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
## Known issues

None at the moment

## Updating

Like other plugins, in the Domoticz-Growatt-Webserver-Plugin directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```

## Parameters

| Parameter | Value |
| :--- | :--- |
| **Server address** | This is the location where the Growatt mobile APP retrieves data from. |
| **Portal Username** | Username of the Inverter portal eg. admin |
| **Portal Password** | Password of the Inverter portal |
| **Protocol** |	For Growatt inverters this is usually HTTP |
| **Debug** | default is 0 |

## Acknowledgements

* Special thanks for all the hard work of [Dnpwwo](https://github.com/dnpwwo), for the examples and fixing the framework for COOKIE usage.
* Thanks to the original Author: [sincze](https://github.com/sincze) 
* Domoticz team
