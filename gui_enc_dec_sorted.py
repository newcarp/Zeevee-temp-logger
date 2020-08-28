import PySimpleGUI as sg
import telnetlib
import time

def get_zyper_data():
    Host = server_ip

    #Try to connect with the server_ip, if that fails prompt user to change it
    try:
        tn = telnetlib.Telnet(Host)
        tn.read_until(b"Zyper$")
        # print ('Connecting to Zyper...')

        if zv_type == 'dec':
            tn.write("show device status decoders".encode('ascii') + "\n".encode('ascii'))
        elif zv_type == 'enc':
            tn.write("show device status encoders".encode('ascii') + "\n".encode('ascii'))
        time.sleep(.2)

        OUTPUT = tn.read_until(b"Zyper$")
        OUTPUT = OUTPUT.decode('utf-8')
        # print ('Data received, disconnecting')
        tn.close()

    except ConnectionRefusedError:
        sg.popup('Server did not respond, please try changing the IP', title='Connection error')
        OUTPUT = "NULL"

    return OUTPUT.splitlines()

def get_file_data():
    with open ('output.txt') as data:
        file_data = data.readlines()
    return file_data

def get_list_of_zv_units():
    zv_list_key = []

    # Get data once and get the Zeevee unit names into a list to serve as a key
    # zv_data = get_file_data()
    zv_data = get_zyper_data()

    for line in range(len(zv_data)):
        if 'state=Up' in zv_data[line]:
            if 'model=' in zv_data[line]:
                split_line = zv_data[line].split()
                for item in range(len(split_line)):
                    if 'name' in split_line[item]:
                        split_line[item] = split_line[item].replace('name=', '')
                        split_line[item] = split_line[item].replace(',', '')
                        if len(split_line[item]) < 7:
                            split_line[item] += ' '
                        new_data = split_line[item]
                        zv_list_key.append(split_line[item])

    # Setting sorted to True so it gets into the loop
    sorted = True

    while sorted:
        sorted = False
        for entry in range(len(zv_list_key) - 1):
            if zv_list_key[entry] > zv_list_key[entry + 1]:
                zv_list_key[entry], zv_list_key[entry + 1] = zv_list_key[entry + 1], zv_list_key[entry]
                sorted = True


    print (zv_list_key)
    return zv_list_key

def get_zv_temps():
    zv_temps = []

    # zv_data = get_file_data()
    zv_data = get_zyper_data()

    for line in range(len(zv_data)):
        if 'temperature' in zv_data[line]:
            zv_data[line] = zv_data[line].replace('device.temperature; main=', '')
            zv_data[line] = zv_data[line].replace('\n', '')
            zv_data[line] = zv_data[line].replace('C', '')
            zv_data[line] = int(zv_data[line])
            zv_temps.append(zv_data[line])

    return zv_temps

def show_specific_temp(zv_unit):

    Host = server_ip
    zv_temp = 0

    # Try to connect with the server_ip, if that fails prompt user to change it
    try:
        tn = telnetlib.Telnet(Host)
        tn.read_until(b"Zyper$")
        # print ('Connecting to Zyper...')

        tn.write("show device status ".encode('ascii') + zv_unit.encode('ascii') + "\n".encode('ascii'))
        time.sleep(.2)

        OUTPUT = tn.read_until(b"Zyper$")
        OUTPUT = OUTPUT.decode('utf-8')
        # print ('Data received, disconnecting')
        tn.close()

    except ConnectionRefusedError:
        sg.popup('Server did not respond, please try changing the IP', title='Connection error')
        OUTPUT = "NULL"

    zv_data = OUTPUT.splitlines()

    for line in range(len(zv_data)):
        if 'temperature' in zv_data[line]:
            zv_data[line] = zv_data[line].replace('device.temperature; main=', '')
            zv_data[line] = zv_data[line].replace('\n', '')
            zv_data[line] = zv_data[line].replace('C', '')
            zv_temp = int(zv_data[line])

    return zv_temp

server_ip = '192.168.11.252' #Have to initialize I guess

#GUI starts here
sg.theme('Dark Blue 3')

layout = [[sg.Text('Server:'), sg.InputText(key='-SERVER_INPUT-', size=(15,1), default_text=server_ip), sg.Button('Update')],
          [sg.Radio('Decoders', default = True, group_id='-type-', key='-type_dec-'), sg.Radio('Encoders', group_id='-type-', key='-type_enc-')],
          [sg.Listbox(values='', size=(12, 20), key='-ZV_BOX-'), sg.Text(text='', size=(4,1), font='Helvetica 42',  key='-OUTPUT-')],
          [sg.Button('Show'), sg.Button('Exit')]]

window = sg.Window('ZV Temp', layout)

while True:  # Event Loop
    event, values = window.read()
    # print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Show':
        server_ip = values['-SERVER_INPUT-']
        if values['-type_dec-']:
            zv_type = 'dec'
        else:
            zv_type = 'enc'
        try:
            window['-OUTPUT-'].update(show_specific_temp((values['-ZV_BOX-'][0])))
        except IndexError:
            pass
    if event == 'Update':
        if values['-type_dec-']:
            zv_type = 'dec'
        else:
            zv_type = 'enc'
        server_ip = values['-SERVER_INPUT-']
        window['-ZV_BOX-'].update(values=get_list_of_zv_units())
window.close()