import PySimpleGUI as sg
import time
import telnetlib
import csv
import threading

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
    except TimeoutError:
        sg.popup('Server did not respond, please try changing the IP', title='Connection error')
        OUTPUT = "NULL"


    return OUTPUT.splitlines()

def write_csv_names(key):
    key.insert(0, 'Time')
    try:
        with open(file_path, 'w', newline='') as csvfile:
            temp_writer = csv.writer(csvfile)
            temp_writer.writerow(key)
    except PermissionError:
        sg.Popup('File is in use and cannot be written.', title='Info')

def write_csv_temps(temps):
    temps.insert(0, time.ctime())
    try:
        with open(file_path, 'a', newline='') as csvfile:
            temp_writer = csv.writer(csvfile)
            temp_writer.writerow(temps)
    except PermissionError:
        sg.Popup('File is in use and cannot be written.', title='Info')

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

    write_csv_names(zv_list_key)

def main_logging_loop_thread(window):
    while True and (sleepy_time > 29):
        zv_temps = []
        zv_data = get_zyper_data()

        for line in range(len(zv_data)):
            if 'temperature' in zv_data[line]:
                zv_data[line] = zv_data[line].replace('device.temperature; main=', '')
                zv_data[line] = zv_data[line].replace('\n', '')
                zv_data[line] = zv_data[line].replace('C', '')
                zv_data[line] = int(zv_data[line])
                zv_temps.append(zv_data[line])

        write_csv_temps(zv_temps)
        time.sleep(sleepy_time)

        #This informs the main loop that the sleep is done for this loop, you can do whatever you want with it
        window.write_event_value('-THREAD DONE-', '')

def main_logging_loop():
    #God bless the pysimplegui developer, this simple line lets you call a def in it's own thread so the main gui
    #doesn't hang while its doing its sleep
    threading.Thread(target=main_logging_loop_thread, args=(window,), daemon=True).start()

server_ip = '192.168.11.252'
sleepy_time = 600
file_path='zv_temp_log.csv'
cycles = 0
logging = False

#GUI starts here
sg.theme('Dark Blue 3')

simple_menu = [['Notes',['Notes']]]

layout = [[sg.Menu(simple_menu)],
          [sg.Text('Server:'), sg.InputText(key='-SERVER_INPUT-', size=(15,1), default_text=server_ip), sg.Button('Test')],
          [sg.Radio('Decoders', default = True, group_id='-type-', key='-type_dec-'), sg.Radio('Encoders', group_id='-type-', key='-type_enc-')],
          [sg.Text('Output file', size=(8, 1)), sg.Input(default_text=file_path, key='-out_path-'), sg.SaveAs(file_types=(('CSV files', "*.csv"),), button_text='Select')],
          [sg.Text('Logging interval (seconds)'), sg.Input(size=(4,1), default_text=sleepy_time, key='-wait_time-'), sg.Text('Number of intervals recorded this session: '),
           sg.Text('0', font='Helvetica 20', size=(4,1), key='-num_logs_recorded-')],
          [sg.Button('Start logging'), sg.Button('Exit')]]

window = sg.Window('ZV Temp Logged', layout)

while True:  # Event Loop
    event, values = window.read()
    # print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Start logging' and not logging:
        logging = True
        server_ip = values['-SERVER_INPUT-']
        sleepy_time = int(values['-wait_time-'])
        file_path = values['-out_path-']
        if values['-type_dec-']:
            zv_type = 'dec'
        else:
            zv_type = 'enc'
        if sleepy_time > 29:
            try:
                sg.Popup('Logging started', title='Info')
                #this gets and writes the header row to the CSV
                get_list_of_zv_units()
                #note that we call this and not the main_logging_loop_thread, this one stats that one in its own thread
                #so that the gui stays responsive
                main_logging_loop()
                #Increment the number of logging cycles this first time, after this the completed thread will do it below
                cycles += 1
                window['-num_logs_recorded-'].update(value=cycles)
            except NameError:
                pass
        else:
            sg.Popup('Minimum interval is 30 seconds', title='Info')
    elif event == '-THREAD DONE-':
        #this event comes from the logging loop thread, do whatever with it
        cycles += 1
        window['-num_logs_recorded-'].update(value=cycles)
    elif event == 'Notes':
        sg.Popup('This will overwrite whatever file you select.', 'You can\'t leave the file open in Excel unless you do so as read only or new values will not be written.',
                 'If the file is open when you try to start logging this will probably crash.', title='Some quick notes')

window.close()