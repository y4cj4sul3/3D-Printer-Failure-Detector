# 3D-Printer-Failure-Detector

Currently this project only fully support Ultimaker 3D printers without extra devices.
However, it is possible to support other 3D printers.

## Getting Start

### Installation

Following packages are required.

- requests
- shutil

### Printer Configuration

1. Make sure your printer is connected to WiFi and your computer connects to the same AP.
2. Go to `http://<PRINTER_IP>/docs/api` and expend Authentication session. Register a new application using the function `/auth/request`. Keep the `id` and `key`.
3. A message should pop up on the 3D printer's monitor. Click `Allow`. Now, your id should be autherized, which can be checked by the function `/auth/check/{id}`
4. Create config file `ultimaker.ini` and fill in the information in following form. Replace `<PRINTER_NAME>`, `<PRINTER_IP>`, `<YOUR_ID>`, and `<YOUR_KEY>` with your configuration. `<PRINTER_NAME>` is used later to create `Printer` object.

```
[ultimaker.<PRINTER_NAME>]
printer_ip = <PRINTER_IP>
id = <YOUR_ID>
key = <YOUR_KEY>
```

## Collecting Data

To collect training data, run `python crawler.py -p <PRINTER_NAME>`.
It will check whether the printer is printing every miniute, and collect snapshot and printing progress during printing.
The collected data will be saved in `data` folder.

## Simulation

### Blender Addon

1. Zip the folder `Blender Addon`.
2. Open Blender, `Edit > Preference > Add-ons > Install` and select the zip file.
3. Enable the installed addon.
