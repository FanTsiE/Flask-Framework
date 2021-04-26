from flask import Flask, request
import xlrd
import serial
from time import sleep

app = Flask(__name__)


def read_table(table):
    book = xlrd.open_workbook(table)
    sheet = book.sheet_by_index(0)
    keys = [sheet.cell(0, col_index).value for col_index in range(sheet.ncols)]
    dict_list = []
    for row_index in range(1, sheet.nrows):
        d = {keys[col_index]: sheet.cell(row_index, col_index).value
             for col_index in range(sheet.ncols)}
        dict_list.append(d)
    return dict_list


def serial_send_ui(ser, d):
    u = d['U']
    i = d['I']
    msg_u = "0255" + str(u).encode().hex() + "0d03"
    msg_i = "0249" + str(i).encode().hex() + "0d03"
    ser.write(bytes.fromhex(msg_u))
    ser.write(bytes.fromhex(msg_i))
    return


@app.route('/getvalues', methods=['GET'])
def get_values():
    ui = {'U': 0, 'I': 0}
    dict_list = read_table('table.xls')
    result = {}
    try:
        result = {'radius': float(request.args.get('radius')), 'thickness': float(request.args.get('thickness'))}
    except TypeError:
        print("The values do not exist.")
    else:
        print(result)

    for i in range(len(dict_list)):
        # condition_r = result['radius'] == dict_list[i]['radius']    #radius
        condition_t = result['thickness'] == dict_list[i]['thickness']  # thickness
        # thickness at top priority
        if condition_t:
            ui['U'] = dict_list[i]['U']
            ui['I'] = dict_list[i]['I']
            # radius:
            """
            elif condition_r:
                if dict_list[i]['thickness'] < result['thickness'] < dict_list[i + 1]['thickness']:
                    ui['U']=(dict_list[i]['U']+dict_list[i+1]['U'])/2
                    ui['I'] = (dict_list[i]['I'] + dict_list[i + 1]['I']) / 2
                    break
            """
    print(ui)
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    if 0 < ui['U'] * ui['I'] <= 1400:
        serial_send_ui(ser1, ui)
        return ui
    else:
        return "Error."


@app.route('/', methods=['POST', 'GET'])
def values():
    ui = {'U': 0, 'I': 0}
    dict_list = read_table('table.xls')
    result = request.get_json(force=True)
    for i in range(len(dict_list)):
        # condition_r = result['radius'] == dict_list[i]['radius']    #radius
        condition_t = result['thickness'] == dict_list[i]['thickness']  # thickness:
        if condition_t:
            ui['U'] = dict_list[i]['U']
            ui['I'] = dict_list[i]['I']
            # radius:
            """
            elif condition_r:
                if dict_list[i]['thickness'] < result['thickness'] < dict_list[i + 1]['thickness']:
                    ui['U']=(dict_list[i]['U']+dict_list[i+1]['U'])/2
                    ui['I'] = (dict_list[i]['I'] + dict_list[i + 1]['I']) / 2
                    break
            """
    print(ui)
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    if 0 < ui['U'] * ui['I'] <= 1400:
        serial_send_ui(ser1, ui)
        return ui
    else:
        return "Error."


@app.route('/on', methods=['GET'])
def switch_on():
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    ser1.write(bytes.fromhex("024F4E0D03"))
    cnt = 0
    while True:
        msg = ser1.readline()
        if cnt == 4:
            break
        cnt += 1
    msg_str = msg.decode().replace(",", ".")
    l = []
    for ch in msg_str.split():
        try:
            l.append(float(ch))
        except ValueError:
            pass
    if l is not None:
        ui = {'U': l[0], 'I': l[1]}
        return ui
    else:
        return "Error."


@app.route('/off', methods=['POST', 'GET'])
def switch_off():
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    ser1.write(bytes.fromhex("024F460D03"))
    cnt = 0
    while True:
        msg = ser1.readline()
        if cnt == 2:
            break
        cnt += 1
    if msg is not None:
        return "1"  # success
    else:
        return "0"  # failure


@app.route('/setvalues', methods=['POST', 'GET'])
def set_values():
    ui = request.get_json(force=True)
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    serial_send_ui(ser1, ui)
    if len(ser1.readline()) >= 1:
        return "1"  # success
    else:
        return "0"  # failure


@app.route('/test', methods=['GET'])
def test():
    f = open("configure.txt", "r")
    config = f.readline().split(" ")
    ser1 = serial.Serial(config[0], int(config[1]), write_timeout=int(config[2]))
    ser1.write(bytes.fromhex("0255530D03"))
    ser1.write(bytes.fromhex("0249530D03"))
    u_byte = ser1.readline()
    i_byte = ser1.readline()
    u = 0
    i = 0
    if u_byte is not None and i_byte is not None:
        for ch in u_byte.decode().replace(",", ".").split():
            try:
                u = float(ch)
            except ValueError:
                pass
        for ch in i_byte.decode().replace(",", ".").split():
            try:
                i = float(ch)
            except ValueError:
                pass
        ui = {'U': u, 'I': i}
        if u > 0 and i > 0:
            return ui
        else:
            return "Error."
    else:
        return "Error."


if __name__ == '__main__':
    app.debug = True
    app.run()