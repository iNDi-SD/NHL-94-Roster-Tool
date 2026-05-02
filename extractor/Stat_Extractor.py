# """ Offline Stat Extractor for Genesis ROMs"""
# """ Version 0.5.0 """
# Version history
# 0.1.0 - Original Program
# 0.1.1 - Fix Divide by Zero
# 0.5.0 - Add RA Save States for Genesis, Fix GAA and SV for Goalies, Fix Removal of Spaces from Team Info, Change Values to Int, update to RA 1.10 save states (64-bit)

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from StatExt import Ui_statExtract
from binascii import b2a_hex
import csv
import xlwt
# from xlutils.copy import copy as xl_copy
import re
import os
from shutil import copyfile
import struct


class statExtract(QMainWindow):
    def __init__(self):
        super(statExtract, self).__init__()

        # User Interface from Designer
        self.ui = Ui_statExtract()
        self.ui.setupUi(self)

        # Local Modifications
        self.ui.menubar.setNativeMenuBar(False)  # for MacOS
        self.ui.extBtn.setEnabled(False)
        self.ui.typeSNES9x.setEnabled(False)

        # Instance Variables
        self.romFile = "No ROM loaded."
        self.tempRomFile = "temp.bin"
        self.stateFile = " No State loaded."
        self.stateName = ""
        self.tempStateFile = "temp.sv"
        self.tempDataFile = "game.csv"
        self.romLoaded = False
        self.stateLoaded = False

        # Instance Variables for data
        self.tmptrs = []
        self.hmtminfo = {}
        self.awtminfo = {}
        self.hmroster = []
        self.awroster = []
        self.hmgmstats = {}
        self.awgmstats = {}
        self.hmplstats = []
        self.awplstats = []
        self.scoresum = []
        self.pensum = []

        # Instance Variables specific to Save States (will change depending on State Type)
        self.system = 'gens'
        self.type = 'gpgx'
        self.offset = 9320
        self.endianfix = 1
        self.endian = 'little'
        self.swap = 1

        # Connect Actions
        self.ui.actionQuit.triggered.connect(self.cleanUp)
        self.ui.actionLoad_ROM.triggered.connect(self.loadRom)
        self.ui.romBtn.clicked.connect(self.loadRom)
        self.ui.actionLoad_Save_State.triggered.connect(self.loadSS)
        self.ui.stateBtn.clicked.connect(self.loadSS)
        self.ui.extBtn.clicked.connect(self.extToXLS)
        self.ui.actionExtract_to_CSV.triggered.connect(self.extToXLS)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionInstructions.triggered.connect(self.help)

    def cleanUp(self):
        # Remove Temp files before exiting
        if os.path.isfile("temp.bin"):
            os.remove("temp.bin")
        if os.path.isfile("temp.sv"):
            os.remove("temp.sv")
        QApplication.quit()

    def about(self):
        # About
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("NHL '94 Stat Extractor version 0.5.\n\nAny problems or questions, please visit nhl94.com, "
                    "or email: chaos@nhl94.com")
        # msg.setStandardButtons(QMessageBox.OK)
        msg.exec_()

    def help(self):
        # Help
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("NHL '94 Stat Extractor version 0.5.\n\n This program is designed to extract stats from "
                    "save states and output the data to an XLS file. The XLS file is a spreadsheet that is compatible "
                    "with MS Excel and other spreadsheet programs.\n\nThe program asks for the ROM used, the save state"
                    " (which should be saved at the Three Stars screen, or the Game End Summary screen), and the "
                    "length of the Periods (used to calculate GAA for Goalie). Once the files are selected, and the "
                    "length of Periods is entered, click on the Extract to XLS button, and it will ask you where you "
                    "would like to save the file. Once completed, a message will pop up to notify you.")
        # msg.setStandardButtons(QMessageBox.OK)
        msg.exec_()

    def get_sec(self, time_str):
        # Convert Time String (MM:SS) to Integer Seconds
        m, s = time_str.split(':')
        return int(m) * 60 + int(s)

    def initVar(self):
        # Re-initialize variables on successive runs

        self.tmptrs = []
        self.hmtminfo = {}
        self.awtminfo = {}
        self.hmroster = []
        self.awroster = []
        self.hmgmstats = {}
        self.awgmstats = {}
        self.hmplstats = []
        self.awplstats = []
        self.scoresum = []
        self.pensum = []

    def getStateType(self):
        # Set Offset and Endian-ness Depending on Save State Type

        if self.ui.typeSNES9x is True:   # SNES
            self.system = 'snes'
            self.type = 'snes9x'
            self.offset = 0
            self.endianfix = 0
            self.endian = 'little'
            self.swap = 0
        else:                           # Genesis
            self.system = 'gens'
            self.type = 'gpgx'
            self.offset = 0     # Updated all stat extract positions to RA 1.10 64-bit starting values
            self.endianfix = 1
            self.endian = 'little'
            self.swap = 1

    def loadRom(self):
        # Loads ROM into temp file

        ftypes = "'94 ROM Files, (*.bin *.smc)"
        home = os.path.expanduser('~/Desktop')
        file = QFileDialog.getOpenFileName(self, 'Select ROM', home, ftypes)

        if file[0]:
            with open(file[0], 'rb') as f:
                self.romFile = file[0]
                self.ui.romLabel.setText(self.romFile)
                copyfile(self.romFile, self.tempRomFile)
                self.romLoaded = True

            if self.romLoaded == True and self.stateLoaded == True:
                self.ui.extBtn.setEnabled(True)
                self.ui.actionExtract_to_CSV.setEnabled(True)

    def loadSS(self):
        # Loads state into temp file

        ftypes = "'94 Save State Files, (*.gs* *.state*)"
        home = os.path.expanduser('~/Desktop')
        file = QFileDialog.getOpenFileName(self, 'Select Save State', home, ftypes)

        if file[0]:
            with open(file[0], 'rb') as f:
                self.stateFile = file[0]
                self.stateName = os.path.basename(file[0])
                self.ui.stateLabel.setText(self.stateFile)
                copyfile(self.stateFile, self.tempStateFile)
                self.stateLoaded = True

            if self.romLoaded == True and self.stateLoaded == True:
                self.ui.extBtn.setEnabled(True)
                self.ui.actionExtract_to_CSV.setEnabled(True)


    def extToXLS(self):
        # Prepare files for extraction and get data for XLS

        ftypes = "Microsoft Excel 95-03 Spreadsheet, *.xls"
        home = os.path.expanduser('~/Desktop')

        try:
            save = QFileDialog.getSaveFileName(self, "Please choose a name and location for the XLS file...",
                                               home, ftypes)

            if save[0].lower().endswith('.xls'):
                savefile = save[0]

            else:
                savefile = save[0] + ".xls"

            self.initVar()
            self.extStats(savefile)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Stats Successfully Extracted to " + savefile + ".")
            # msg.setStandardButtons(QMessageBox.OK)
            msg.exec_()

        except EnvironmentError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Could not write to XLS file.  Please check file permissions.")
            # msg.setStandardButtons(QMessageBox.OK)
            msg.exec_()

    def exportXLS(self, savefile):
        # Sends all data to XLS file

        book = xlwt.Workbook()
        ws = book.add_sheet(self.stateName)

        fnt = xlwt.Font()
        fnt.name = 'Arial'
        fnt.height = 280

        # Set Styles

        titlecell = xlwt.easyxf('font: color white, bold true, height 280;'
                                'pattern: pattern solid, fore_color grey80, back_color grey80;'
                                'align: vertical center, horizontal center')
        cellcenter = xlwt.easyxf('font: color black, height 220; align: vertical center, horizontal center')
        gamecell = xlwt.easyxf('font: color black, height 220; align: vertical center, horizontal center,'
                               'shrink_to_fit true')
        shpctcell = xlwt.easyxf('font: color black, height 220; align: vertical center, horizontal center'
                                , num_format_str='00.0%')
        playercell = xlwt.easyxf('font: color black, height 220; '
                                 'align: vertical center, horizontal left, shrink_to_fit true')
        gaacell = xlwt.easyxf("font: color black, height 220; "
                                "align: vertical center, horizontal left, shrink_to_fit true; " 
                                , num_format_str='0.00')
        svpctcell = xlwt.easyxf("font: color black, height 220; "
                              "align: vertical center, horizontal left, shrink_to_fit true; "
                              , num_format_str='0.000')
        sumcell = xlwt.easyxf('font: color black, height 220;'
                              'align: vertical center, horizontal left, shrink_to_fit true')

        # Write Team Matchup

        matchup = self.awtminfo['city'] + ' ' + self.awtminfo['name'] + ' vs. ' + self.hmtminfo['city'] + ' ' \
                  + self.hmtminfo['name']
        ws.write_merge(1, 2, 1, 19, matchup, titlecell)

        # Add Game Stats Header

        ws.write(4, 1, self.awtminfo['abv'], titlecell)
        ws.write_merge(4, 4, 2, 4, 'Game Stats', titlecell)
        ws.write(4, 5, self.hmtminfo['abv'], titlecell)

        # Add Game Stats
        line = []
        line.append([int(self.awgmstats['Goals']), 'Score', int(self.hmgmstats['Goals'])])
        line.append([int(self.awgmstats['SOG']), 'Shots', int(self.hmgmstats['SOG'])])
        line.append([self.awgmstats['SH%'], 'Shooting %', self.hmgmstats['SH%']])
        line.append([self.awgmstats['PPG'] + '/' + self.awgmstats['PP'], 'Power Play', self.hmgmstats['PPG'] + '/'
                     + self.hmgmstats['PP']])
        line.append([int(self.awgmstats['SHG']), 'SH Goals', int(self.hmgmstats['SHG'])])
        line.append([self.awgmstats['BAG'] + '/' + self.awgmstats['BAA'], 'Breakaways', self.hmgmstats['BAG'] + '/'
                     + self.hmgmstats['BAA']])
        line.append([self.awgmstats['1TG'] + '/' + self.awgmstats['1TA'], 'One-Timers', self.hmgmstats['1TG'] + '/'
                     + self.hmgmstats['1TA']])
        line.append([self.awgmstats['PSG'] + '/' + self.awgmstats['PSA'], 'Penalty Shots', self.hmgmstats['PSG'] + '/'
                     + self.hmgmstats['PSA']])
        line.append([self.awgmstats['FOW'] + '/' + self.awgmstats['FOT'] + ' (' + self.awgmstats['FO%'] + ')',
                     'Faceoffs',
                     self.hmgmstats['FOW'] + '/' + self.hmgmstats['FOT'] + ' (' + self.hmgmstats['FO%'] + ')'])
        line.append([int(self.awgmstats['BCK']), 'Checks', int(self.hmgmstats['BCK'])])
        line.append([int(self.awgmstats['PenM']), 'PIM', int(self.hmgmstats['PenM'])])
        line.append([self.awgmstats['ATZ'], 'Attack Zone', self.hmgmstats['ATZ']])
        line.append([self.awgmstats['PassC'] + '/' + self.awgmstats['PassA'] + ' (' + self.awgmstats['PS%'] + ')',
                     'Passing',
                     self.hmgmstats['PassC'] + '/' + self.hmgmstats['PassA'] + ' (' + self.hmgmstats['PS%'] + ')'])

        currow = 5
        for gmstats in line:
            row = ws.row(currow)
            if currow == 7:
                row.write(1, gmstats[0], shpctcell)
                ws.write_merge(currow, currow, 2, 4, gmstats[1], titlecell)
                row.write(5, gmstats[2], shpctcell)
            else:
                row.write(1, gmstats[0], cellcenter)
                ws.write_merge(currow, currow, 2, 4, gmstats[1], titlecell)
                row.write(5, gmstats[2], cellcenter)
            currow += 1

        currow += 2
        row = ws.row(currow)
        ws.write_merge(currow, currow, 1, 3, 'Peak Crowd Level', titlecell)
        row.write(4, self.hmgmstats['Meter'] + ' dB', cellcenter)

        # Period Summary

        line = []
        line.append(['Period', 'Stats', '(Goals-Shots)'])
        line.append(['Team', '1st', '2nd', '3rd', 'OT', 'Total'])

        currow += 3
        ws.write_merge(currow, currow, 1, 6, 'Period Stats (Goals-Shots)', titlecell)
        currow += 1
        ws.write(currow, 1, 'Team', titlecell)
        ws.write(currow, 2, '1st', titlecell)
        ws.write(currow, 3, '2nd', titlecell)
        ws.write(currow, 4, '3rd', titlecell)
        ws.write(currow, 5, 'OT', titlecell)
        ws.write(currow, 6, 'Total', titlecell)
        currow += 1

        line = []
        line.append([self.awtminfo['abv'], self.awgmstats['1PG'] + '-' + self.awgmstats['1PSH'],
                     self.awgmstats['2PG'] + '-' + self.awgmstats['2PSH'],
                     self.awgmstats['3PG'] + '-' + self.awgmstats['3PSH'],
                     self.awgmstats['OTPG'] + '-' + self.awgmstats['OTSH'],
                     self.awgmstats['Goals'] + '-' + self.awgmstats['SOG']])
        line.append([self.hmtminfo['abv'], self.hmgmstats['1PG'] + '-' + self.hmgmstats['1PSH'],
                     self.hmgmstats['2PG'] + '-' + self.hmgmstats['2PSH'],
                     self.hmgmstats['3PG'] + '-' + self.hmgmstats['3PSH'],
                     self.hmgmstats['OTPG'] + '-' + self.hmgmstats['OTSH'],
                     self.hmgmstats['Goals'] + '-' + self.hmgmstats['SOG']])

        for perstats in line:
            row = ws.row(currow)
            i = 0
            for cols in perstats:
                row.write(i + 1, cols, cellcenter)
                i += 1
            currow += 1

        # Player Stats

        currow = 4

        # Calculate Regulation Time in Seconds (for GAA)

        pertime = self.ui.perLength.value()
        pertime = (pertime * 3 * 60)

        # Stat Header

        ws.write_merge(currow, currow, 9, 18, self.awtminfo['abv'] + ' Player Stats', titlecell)
        currow += 1
        col = 9

        statlist = ['Name', 'JNo', 'Pos', 'G', 'A', 'Pts', 'SOG', 'ChksF', 'PIM', 'TOI']
        goalielist = ['Name', 'JNo', 'Pos', 'GA', 'SV', 'SHA', 'GAA', 'SV%', 'A', 'TOI']

        # Away Stats

        for list in statlist:
            row = ws.row(currow)
            row.write(col, list, titlecell)
            col += 1

        for player in self.awplstats:
            if player['Pos'] != 'G' and player['TOI'] != '00:00':
                currow += 1
                row = ws.row(currow)
                list = [player['Name'], int(player['JNo']), player['Pos'], int(player['G']), int(player['A']),
                        int(player['Pts']), int(player['SOG']), int(player['ChksF']), int(player['PIM']), player['TOI']]
                col = 9
                for item in list:
                    row = ws.row(currow)
                    row.write(col, item, playercell)
                    col += 1

        currow += 2
        col = 9
        ws.write_merge(currow, currow, 9, 18, self.awtminfo['abv'] + ' Goalie Stats', titlecell)
        currow += 1
        for list in goalielist:
            row = ws.row(currow)
            row.write(col, list, titlecell)
            col += 1

        for player in self.awplstats:
            if player['Pos'] == 'G' and player['TOI'] != '00:00':
                currow += 1
                row = ws.row(currow)

                sv = int(player['SOG']) - int(player['G'])

                if sv <= 0:     # Made no saves
                    sv = 0
                    svpct = 0.000
                else:
                    svpct = round(sv / int(player['SOG']), 3)

                # GAA Calculation: GAA = GA / ($toi / ($regtime)

                toi = self.get_sec(player['TOI'])
                gaa = round(int(player['G']) / (toi / pertime), 2)

                list = [player['Name'], int(player['JNo']), 'G', int(player['G']), sv, int(player['SOG']), gaa, svpct,
                        int(player['A']), player['TOI']]
                col = 9
                for item in list:
                    if col == 15:
                        row.write(col, item, gaacell)
                    elif col == 16:
                        row.write(col, item, svpctcell)
                    else:
                        row.write(col, item, playercell)
                    col += 1

        # Home Stats

        currow += 2
        col = 9
        ws.write_merge(currow, currow, 9, 18, self.hmtminfo['abv'] + ' Player Stats', titlecell)
        currow += 1

        for list in statlist:
            row = ws.row(currow)
            row.write(col, list, titlecell)
            col += 1

        for player in self.hmplstats:
            if player['Pos'] != 'G' and player['TOI'] != '00:00':
                currow += 1
                row = ws.row(currow)
                list = [player['Name'], int(player['JNo']), player['Pos'], int(player['G']), int(player['A']),
                        int(player['Pts']), int(player['SOG']), int(player['ChksF']), int(player['PIM']), player['TOI']]
                col = 9
                for item in list:
                    row.write(col, item, playercell)
                    col += 1

        currow += 1
        col = 9
        ws.write_merge(currow, currow, 9, 18, self.hmtminfo['abv'] + ' Goalie Stats', titlecell)
        currow += 1
        for list in goalielist:
            row = ws.row(currow)
            row.write(col, list, titlecell)
            col += 1

        for player in self.hmplstats:
            if player['Pos'] == 'G' and player['TOI'] != '00:00':
                currow += 1
                row = ws.row(currow)

                sv = int(player['SOG']) - int(player['G'])

                if sv <= 0:  # Made no saves
                    sv = 0
                    svpct = 0.000
                else:
                    svpct = round(sv / int(player['SOG']), 3)

                # GAA Calculation: GAA = GA / ($toi / ($regtime)

                toi = self.get_sec(player['TOI'])
                gaa = round(int(player['G']) / (toi / pertime), 2)

                list = [player['Name'], int(player['JNo']), 'G', int(player['G']), sv, int(player['SOG']), gaa, svpct,
                        int(player['A']), player['TOI']]
                col = 9
                for item in list:
                    if col == 15:
                        row.write(col, item, gaacell)
                    elif col == 16:
                        row.write(col, item, svpctcell)
                    else:
                        row.write(col, item, playercell)
                    col += 1

        # Scoring Summary

        currow += 3
        ws.write_merge(currow, currow, 1, 7, 'Scoring Summary', titlecell)
        currow += 1
        col = 1
        line = ['Period', 'Time', 'Team', 'G', 'A1', 'A2', 'Type']
        row = ws.row(currow)
        for item in line:
            row.write(col, item, titlecell)
            col += 1

        for goal in self.scoresum:
            currow += 1
            row = ws.row(currow)
            list = [int(goal['Per']), goal['Time'], goal['Team'], goal['G'], goal['A1'], goal['A2'], goal['Type']]
            col = 1
            for item in list:
                row.write(col, item, sumcell)
                col += 1

        # Penalty Summary

        currow += 3
        ws.write_merge(currow, currow, 1, 5, 'Penalty Summary', titlecell)
        currow += 1
        col = 1
        line = ['Period', 'Time', 'Team', 'Player', 'Type']
        row = ws.row(currow)
        for item in line:
            row.write(col, item, titlecell)
            col += 1

        for pen in self.pensum:
            currow += 1
            row = ws.row(currow)
            list = [int(pen['Per']), pen['Time'], pen['Team'], pen['Player'], pen['Type']]
            col = 1
            for item in list:
                row.write(col, item, sumcell)
                col += 1

        book.save(savefile)

    def lit_to_big(self, little):
        # Change byte string from little to big endian
        return little[2:4] + little[0:2]

    def tm_ptrs(self):
        # Retrieve Team Offset Pointers

        # Team Offset Start Position:
        # GENS - 782 (030E)
        # SNES - 927719 (E27E7)

        # Retrieve # of Teams from GUI (max setting is 32)

        numteams = self.ui.numTeams.value()

        if self.system == "snes":
            ptrstart = 927719
        else:
            ptrstart = 782

        with open(self.tempRomFile, 'rb') as f:
            f.seek(ptrstart)

            ptrarray = []

            for i in range(0, numteams):

                if self.system == "snes":
                    firsttm = b2a_hex(f.read(2))
                    conv = self.lit_to_big(firsttm)
                    # Need to add 0E0000, 0200 (Header Offset), and subtract 0800)
                    data = int(conv, 16) + int('0x0D8200', 16)
                else:
                    firsttm = b2a_hex(f.read(4))
                    data = int(firsttm, 16)

                print(firsttm)
                print(data)
                ptrarray.append(data)

        return ptrarray

    def getTeamInfo(self, f, ptr):
        # Retrieve Team Info

        # Team Name Data starts at the end of Player Data (offset given in bytes 5 and 6 in Team Data)
        # First offset: Length of Team City (including this byte)
        # AA AA TEAM CITY BB BB TEAM ABV CC CC TEAM NICKNAME DD DD TEAM ARENA
        # AA - Length of Team City (including these 2 bytes)
        # BB - Length of Team Abv (including these 2 bytes)
        # CC - Length of Team Nickname (including these 2 bytes)
        # DD - Length of Team Arena (including these 2 bytes)
        # All Name Data is in ASCII format.

        # Calculate Player Data Space

        # Move to Start of Team Data Bytes
        f.seek(ptr)

        if self.system == "snes":
            # For SNES
            # Player Data Space by default is at position 00 55 hex from pointer offset,
            # or 85 in decimal. Sometimes, this gets changed (modded ROMs). So we will read the bytes instead.
            ploff = self.lit_to_big(b2a_hex(f.read(2)))
            ploff = int(ploff, 16)

            # Team Name Data Position Offset - Team Offset + 4 bytes
            f.seek(ptr + 4)
            tmpos = self.lit_to_big(b2a_hex(f.read(2)))

            # Player Data Size = Team Data Offset - Player Data Offset - 2 (last 2 bytes of Player Data - not used)
            plsize = int(tmpos, 16) - ploff - 2

            # Read Team City
            dataoff = ptr + int(tmpos, 16)
            f.seek(dataoff)
            tml = int(self.lit_to_big(b2a_hex(f.read(1))), 16)
            f.seek(1, 1) # Skip 00
            tmcity = f.read(tml - 2).decode("utf-8")

            # Read Team Abv
            tml = int(self.lit_to_big(b2a_hex(f.read(1))), 16)
            f.seek(1, 1)
            tmabv = f.read(tml - 2).decode("utf-8")

            # Read Team Nickname
            tml = int(self.lit_to_big(b2a_hex(f.read(1))), 16)
            f.seek(1, 1)
            tmnm = f.read(tml - 2).decode("utf-8")

        else:
            # For GENS
            ploff = int(b2a_hex(f.read(2)), 16)

            # Team Name Data Position Offset - Team Offset + 4 bytes
            f.seek(ptr + 4)
            tmpos = b2a_hex(f.read(2))

            # Player Data Size = Team Data Offset - Player Data Offset - 2 (last 2 bytes of Player Data - not used)
            plsize = int(tmpos, 16) - ploff - 2

            # Read Team City
            dataoff = ptr + int(tmpos, 16)
            f.seek(dataoff)
            tml = int(b2a_hex(f.read(2)), 16)
            tmcity = f.read(tml - 2).decode("utf-8")

            # Read Team Abv
            tml = int(b2a_hex(f.read(2)), 16)
            tmabv = f.read(tml - 2).decode("utf-8")

            # Read Team Nickname
            tml = int(b2a_hex(f.read(2)), 16)
            tmnm = f.read(tml - 2).decode("utf-8")

        # Remove unwanted characters (due to a bad job of ROM editing)
        tmcity = re.sub('[^A-Za-z ]', '', tmcity)
        tmabv = re.sub('[^A-Za-z]', '', tmabv)
        tmnm = re.sub('[^A-Za-z ]', '', tmnm)

        print(tmcity + tmabv + tmnm)

        return dict(city=tmcity, abv=tmabv, name=tmnm, ploff=str(ploff), plsize=str(plsize))

    def getPlayerInfo(self, f, ptr, ploff, plsize):
        # Retreive Player Info

        # Player Data

        # XX XX "PLAYER NAME" XX 123456789ABCDE

        # XX XX = "Player name length" + 2 (the two bytes in front of the name) in hex

        # ** We are only using Player Name and Jersey Number in this program **

        # "PLAYER NAME"

        # XX =	Jersey # (decimal)

        # 1 = Weight
        # 2 = Agility

        # 3 = Speed
        # 4 = Off. Aware.

        # 5 = Def. Aware.
        # 6 = Shot Power/Puck Control

        # 7 = Checking
        # 8 = Stick Hand (Uneven = Right. Even = Left. 0/1 will do.)

        # 9 = Stick Handling
        # A = Shot Accuracy

        # B = Endurance/StR
        # C = ? (Roughness on Genesis)/StL

        # D = Passing/GlR
        # E = Aggression/GlL

        # Calculate # of Players - Goalies First, then F and D
        # GENS: Ptr + 81 (2 bytes) for G, Ptr + 80 (first nibble F, second D)
        # SNES: Ptr + 19 (2 bytes) for G, Ptr + 17 (first nibble F, second D)

        roster = []

        if self.system == "snes":
            goff = 18
            poff = 16
        else:
            # For GENS
            goff = 80
            poff = 79

        f.seek(ptr + goff)
        gdata = b2a_hex(f.read(2)).decode("utf-8")
        numg = gdata.find("0")

        f.seek(ptr + poff)
        pdata = b2a_hex(f.read(1))
        numf = int(pdata[0:1], 16)
        numd = int(pdata[1:2], 16)

        nump = numg + numf + numd
        print(str(numg) + str(numf) + str(numd))

        # Move to Player Data

        f.seek(ptr + int(ploff))
        j = 0
        plend = ptr + int(ploff) + int(plsize)

        # Retrieve Roster

        while f.tell() < plend:
            # Name and JNo

            if self.system == "snes":
                pnl = int(b2a_hex(f.read(1)), 16)
                f.seek(1, 1)  # Skip the 00
            else:
                # For GENS
                pnl = int(b2a_hex(f.read(2)), 16)

            nm = f.read(pnl - 2).decode("utf-8")
            jno = b2a_hex(f.read(1)).decode("utf-8")
            j += 1

            # G, F or D?

            if j <= numg:
                pos = 'G'
            elif j <= (numg + numf):
                pos = 'F'
            else:
                pos = 'D'

            # Remove unwanted characters (due to a bad job of ROM editing)

            nm = re.sub('[^ A-Za-z]', '', nm)
            print(nm + jno + pos)
            roster.append(dict(name=nm, jno=jno, pos=pos))
            f.seek(7, 1)  # Move to next Player

        return roster

    def getGameStats(self, f):
        # Retrieve Game Stats from Save State

        # Crowd Meter

        f.seek(49973 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        print(data)

        self.hmgmstats['Meter'] = str(data)

        # Away Goals

        f.seek(51807 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['Goals'] = str(data)

        # Away PP Goals/Opportunities

        f.seek(51797 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PPG'] = str(data)

        f.seek(51799 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PP'] = str(data)

        # Away SHG and SHGA

        f.seek(52649 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['SHG'] = str(data)

        f.seek(51781 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['SHGA'] = str(data)

        # Away Breakaway Goals/Attempts

        f.seek(52653 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['BAG'] = str(data)

        f.seek(52651 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['BAA'] = str(data)

        # Away One-Timer Goals/Attempts

        f.seek(52657 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['1TG'] = str(data)

        f.seek(52655 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['1TA'] = str(data)

        # Away Penalty Shot Goals/Attempts

        f.seek(52661 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PSG'] = str(data)

        f.seek(52659 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PSA'] = str(data)

        # Away Faceoffs Won

        f.seek(51809 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['FOW'] = str(data)

        # Away Body Checks

        f.seek(51811 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['BCK'] = str(data)

        # Away Team Penalties/Minutes

        f.seek(51801 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['Pen'] = str(data)

        f.seek(51803 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PenM'] = str(data)

        # Away Passing Stats

        f.seek(51815 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PassC'] = str(data)

        f.seek(51813 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['PassA'] = str(data)

        # Away Attack Zone

        if self.endian == 'little':
            f.seek(51805 - self.offset)
            datamin = int(b2a_hex(f.read(1)), 16) * 256

            f.seek(51804 - self.offset)
            datasec = int(b2a_hex(f.read(1)), 16)

        else:
            f.seek(51804 - self.offset)
            datamin = int(b2a_hex(f.read(1)), 16) * 256

            f.seek(51805 - self.offset)
            datasec = int(b2a_hex(f.read(1)), 16)

        aztotal = datamin + datasec
        azmin, azsec = divmod(aztotal, 60)
        azstring = str(azmin).zfill(2) + ':' + str(azsec).zfill(2)
        self.awgmstats['ATZ'] = azstring

        ###################################################################

        # Home Game Stats

        # Home Goals

        f.seek(50939 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['Goals'] = str(data)

        # Home PP Goals/Opportunities

        f.seek(50929 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PPG'] = str(data)

        f.seek(50931 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PP'] = str(data)

        # Home SHG and SHGA

        f.seek(51781 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['SHG'] = str(data)

        f.seek(52649 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['SHGA'] = str(data)

        # Home Breakaway Goals/Attempts

        f.seek(51785 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['BAG'] = str(data)

        f.seek(51783 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['BAA'] = str(data)

        # Home One-Timer Goals/Attempts

        f.seek(51789 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['1TG'] = str(data)

        f.seek(51787 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['1TA'] = str(data)

        # Home Penalty Shot Goals/Attempts

        f.seek(51793 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PSG'] = str(data)

        f.seek(51791 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PSA'] = str(data)

        # Home Faceoffs Won

        f.seek(50941 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['FOW'] = str(data)

        # Home Body Checks

        f.seek(50943 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['BCK'] = str(data)

        # Home Team Penalties/Minutes

        f.seek(50933 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['Pen'] = str(data)

        f.seek(50935 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PenM'] = str(data)

        # Home Passing Stats

        f.seek(50947 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PassC'] = str(data)

        f.seek(50945 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['PassA'] = str(data)

        # Home Attack Zone

        if self.endian == 'little':
            f.seek(50937 - self.offset)
            datamin = int(b2a_hex(f.read(1)), 16) * 256

            f.seek(50936 - self.offset)
            datasec = int(b2a_hex(f.read(1)), 16)

        else:
            f.seek(50936 - self.offset)
            datamin = int(b2a_hex(f.read(1)), 16) * 256

            f.seek(50937 - self.offset)
            datasec = int(b2a_hex(f.read(1)), 16)

        aztotal = datamin + datasec
        azmin, azsec = divmod(aztotal, 60)
        azstring = str(azmin).zfill(2) + ':' + str(azsec).zfill(2)
        self.hmgmstats['ATZ'] = azstring

        ##############################################################################################################

        # Period Stats

        # Away Team Period Goals

        f.seek(52629 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['1PG'] = str(data)

        f.seek(52631 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['2PG'] = str(data)

        f.seek(52633 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['3PG'] = str(data)

        f.seek(52635 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.awgmstats['OTPG'] = str(data)

        # Away Team Period SOG

        sog = 0

        f.seek(52637 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.awgmstats['1PSH'] = str(data)

        f.seek(52639 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.awgmstats['2PSH'] = str(data)

        f.seek(52641 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.awgmstats['3PSH'] = str(data)

        f.seek(52643 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.awgmstats['OTSH'] = str(data)

        self.awgmstats['SOG'] = str(sog)

        ###########################################

        # Home Team Period Goals

        f.seek(51761 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)

        self.hmgmstats['1PG'] = str(data)

        f.seek(51763 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['2PG'] = str(data)

        f.seek(51765 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['3PG'] = str(data)

        f.seek(51767 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        self.hmgmstats['OTPG'] = str(data)


        # Home Team Period SOG

        sog = 0

        f.seek(51769 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.hmgmstats['1PSH'] = str(data)

        f.seek(51771 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.hmgmstats['2PSH'] = str(data)

        f.seek(51773 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.hmgmstats['3PSH'] = str(data)

        f.seek(51775 - self.offset - self.endianfix)
        data = int(b2a_hex(f.read(1)), 16)
        sog += data
        self.hmgmstats['OTSH'] = str(data)

        self.hmgmstats['SOG'] = str(sog)

        # Calculate Shooting %, Faceoff %, Passing %
        
        totfo = int(self.hmgmstats['FOW']) + int(self.awgmstats['FOW'])

        if self.hmgmstats['SOG'] == '0':  # No Shots
            hmshpct = 0
        else:
            hmshpct = int(self.hmgmstats['Goals']) / int(self.hmgmstats['SOG'])

        hmfopct = int(self.hmgmstats['FOW']) / totfo * 100

        if self.hmgmstats['PassA'] == '0':   # No Passes
            hmpspct = 0
        else:
            hmpspct = int(self.hmgmstats['PassC']) / int(self.hmgmstats['PassA']) * 100

        if self.awgmstats['SOG'] == '0':
            awshpct = 0
        else:
            awshpct = int(self.awgmstats['Goals']) / int(self.awgmstats['SOG'])

        awfopct = int(self.awgmstats['FOW']) / totfo * 100

        if self.awgmstats['PassA'] == '0':
            awpspct = 0
        else:
            awpspct = int(self.awgmstats['PassC']) / int(self.awgmstats['PassA']) * 100

        self.hmgmstats['SH%'] = round(hmshpct,3)
        self.hmgmstats['FO%'] = str("%.1f" % round(hmfopct, 1))
        self.hmgmstats['FOT'] = str(totfo)
        self.hmgmstats['PS%'] = str("%.1f" % round(hmpspct, 1))

        self.awgmstats['SH%'] = round(awshpct, 3)
        self.awgmstats['FO%'] = str("%.1f" % round(awfopct, 1))
        self.awgmstats['FOT'] = str(totfo)
        self.awgmstats['PS%'] = str("%.1f" % round(awpspct, 1))

        ##############################################################################################################
        ##############################################################################################################

    def getPlayerStats(self, f):
        # Retrieve Player Stats from Save State

        # Genesis Player Stats

        # Need to cycle through roster

        # Home Team

        teamstats = []
        i = 1
        self.swap = self.endianfix  # Initialize swap

        for player in self.hmroster:
            plstats = {}
            plstats['Name'] = player['name']
            plstats['JNo'] = player['jno']
            plstats['Pos'] = player['pos']

            # swap variable needed due to little endian save states (GPGX)

            f.seek(51105 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['G'] = str(data)

            f.seek(51131 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['A'] = str(data)

            plstats['Pts'] = int(plstats['G']) + int(plstats['A'])

            f.seek(51157 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['SOG'] = str(data)

            f.seek(51183 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['PIM'] = str(data)

            f.seek(51209 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['ChksF'] = str(data)

            # For future use

            plstats['ChksA'] = 0
            plstats['PlusMinus'] = 0

            # TOI

            if self.endian == 'little':
                f.seek(51235 - self.offset + (i * 2))
                datamin = int(b2a_hex(f.read(1)), 16) * 256

                f.seek(51234 - self.offset + (i * 2))
                datasec = int(b2a_hex(f.read(1)), 16)

            else:
                f.seek(51234 - self.offset + (i * 2))
                datamin = int(b2a_hex(f.read(1)), 16) * 256

                f.seek(51235 - self.offset + (i * 2))
                datasec = int(b2a_hex(f.read(1)), 16)

            toitotal = datamin + datasec - 2 # Compensate for Genesis TOI bug
            toimin, toisec = divmod(toitotal, 60)

            if toitotal <= 0:  # Did not play the game
                plstats['TOI'] = '00:00'
            else:
                toistring = str(toimin).zfill(2) + ':' + str(toisec).zfill(2)  
                plstats['TOI'] = toistring

            self.hmplstats.append(plstats)
            i += 1
            self.swap = self.swap * -1

        # Away Team

        i = 1
        self.swap = self.endianfix  # Initialize swap

        for player in self.awroster:
            plstats = {}
            plstats['Name'] = player['name']
            plstats['JNo'] = player['jno']
            plstats['Pos'] = player['pos']

            # swap variable needed due to little endian save states (GPGX)

            f.seek(51973 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['G'] = str(data)

            f.seek(51999 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['A'] = str(data)

            plstats['Pts'] = int(plstats['G']) + int(plstats['A'])

            f.seek(52025 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['SOG'] = str(data)

            f.seek(52051 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['PIM'] = str(data)

            f.seek(52077 - self.offset + i + self.swap)
            data = int(b2a_hex(f.read(1)), 16)
            plstats['ChksF'] = str(data)

            # For future use - Plus/Minus and ChksA Hack

            plstats['ChksA'] = 0
            plstats['PlusMinus'] = 0

            # TOI

            if self.endian == 'little':
                f.seek(52103 - self.offset + (i * 2))
                datamin = int(b2a_hex(f.read(1)), 16) * 256

                f.seek(52102 - self.offset + (i * 2))
                datasec = int(b2a_hex(f.read(1)), 16)

            else:
                f.seek(52102 - self.offset + (i * 2))
                datamin = int(b2a_hex(f.read(1)), 16) * 256

                f.seek(52103 - self.offset + (i * 2))
                datasec = int(b2a_hex(f.read(1)), 16)

            toitotal = datamin + datasec - 2 # Compensate for Genesis TOI bug
            toimin, toisec = divmod(toitotal, 60)

            if toitotal <= 0:  # Did not play the game
                plstats['TOI'] = '00:00'
            else:
                toistring = str(toimin).zfill(2) + ':' + str(toisec).zfill(2)  
                plstats['TOI'] = toistring

            self.awplstats.append(plstats)
            i += 1
            self.swap = self.swap * -1

    def getScoringSum(self, f):
        # Retrieve Scoring Summary

        # Get Scoring Summary Length

        tmpExt = 50323 - self.offset
        f.seek(50323 - self.offset - self.endianfix)
        sumlength = int(b2a_hex(f.read(1)), 16)

        swap = self.endianfix

        for i in range(1, ((sumlength + 6) // 6)):

            goaldata = {}

            # Period of Goal
            f.seek(tmpExt + 1 + swap)
            period = int(b2a_hex(f.read(1)), 16)
            period = int(period / 64 + 1)
            goaldata['Per'] = str(period)

            # Time of Goal (in seconds)
            f.seek(tmpExt + 1 + swap)
            goalsec = int(b2a_hex(f.read(1)), 16)
            f.seek(tmpExt + 2 - swap)
            goaltmp = int(b2a_hex(f.read(1)), 16)
            goalsec = (goalsec * 256) + goaltmp - (period - 1) * 16384
            min, sec = divmod(goalsec, 60)
            goaltime = str(min).zfill(2) + ':' + str(sec).zfill(2)
            goaldata['Time'] = goaltime

            # Team that scored, type of Goal

            f.seek(tmpExt + 3 + swap)
            teamtype = b2a_hex(f.read(1)).decode("utf-8")
            str(teamtype).zfill(2)

            if teamtype == '00':
                team = 'Home'
                goaldata['Type'] = 'SH2'
            elif teamtype == '01':
                team = 'Home'
                goaldata['Type'] = 'SH'
            elif teamtype == '02':
                team = 'Home'
                goaldata['Type'] = 'EV'
            elif teamtype == '03':
                team = 'Home'
                goaldata['Type'] = 'PP'
            elif teamtype == '04':
                team = 'Home'
                goaldata['Type'] = 'PP2'
            elif teamtype == '80':
                team = 'Away'
                goaldata['Type'] = 'SH2'
            elif teamtype == '81':
                team = 'Away'
                goaldata['Type'] = 'SH'
            elif teamtype == '82':
                team = 'Away'
                goaldata['Type'] = 'EV'
            elif teamtype == '83':
                team = 'Away'
                goaldata['Type'] = 'PP'
            elif teamtype == '84':
                team = 'Away'
                goaldata['Type'] = 'PP2'
            else:
                team = 'Home'
                goaldata['Type'] = 'BAD'

            # Player that scored

            f.seek(tmpExt + 4 - swap)
            scoffset = int(b2a_hex(f.read(1)), 16)

            if team == 'Away':
                goaldata['Team'] = self.awtminfo['abv']
                goaldata['G'] = self.awroster[scoffset]['name']
            else:
                goaldata['Team'] = self.hmtminfo['abv']
                goaldata['G'] = self.hmroster[scoffset]['name']

            # Assisters on Goal

            f.seek(tmpExt + 5 + swap)
            a1offset = int(b2a_hex(f.read(1)), 16)

            if a1offset == 255:  # No Assists
                goaldata['A1'] = 'None'
            else:
                if team == 'Away':
                    goaldata['A1'] = self.awroster[a1offset]['name']
                else:
                    goaldata['A1'] = self.hmroster[a1offset]['name']

            f.seek(tmpExt + 6 - swap)
            a2offset = int(b2a_hex(f.read(1)), 16)

            if a2offset == 255:  # No 2nd Assist
                goaldata['A2'] = 'None'
            else:
                if team == 'Away':
                    goaldata['A2'] = self.awroster[a2offset]['name']
                else:
                    goaldata['A2'] = self.hmroster[a2offset]['name']

            tmpExt = tmpExt + 6
            self.scoresum.append(goaldata)

    def getPenSum(self,f):
        # Retrieve Penalty Summary

        # Get Penalty Summary Length

        tmpExt = 50685 - self.offset
        f.seek(50685 - self.offset - self.endianfix)
        sumlength = int(b2a_hex(f.read(1)), 16)

        swap = self.endianfix

        for i in range(1, ((sumlength + 6) // 4)):

            pendata = {}

            # Period of Penalty

            f.seek(tmpExt + 1 + swap)
            period = int(b2a_hex(f.read(1)), 16)
            period = int(period / 64 + 1)
            pendata['Per'] = str(period)

            # Time of Penalty (in seconds)
            f.seek(tmpExt + 1 + swap)
            pensec = int(b2a_hex(f.read(1)), 16)
            f.seek(tmpExt + 2 - swap)
            pentmp = int(b2a_hex(f.read(1)), 16)
            pensec = (pensec * 256) + pentmp - (period - 1) * 16384
            min, sec = divmod(pensec, 60)
            pentime = str(min).zfill(2) + ':' + str(sec).zfill(2)
            pendata['Time'] = pentime

            # Team that got Penalized

            f.seek(tmpExt + 3 + swap)
            teamtype = int(b2a_hex(f.read(1)), 16)

            if teamtype < 40:
                team = 'Home'
            else:
                team = 'Away'

            if teamtype == 19 or teamtype == 146:
                pendata['Type'] = 'Boarding'
            elif teamtype == 22 or teamtype == 150:
                pendata['Type'] = 'Charging'
            elif teamtype == 24 or teamtype == 152:
                pendata['Type'] = 'Slashing'
            elif teamtype == 26 or teamtype == 154:
                pendata['Type'] = 'Roughing'
            elif teamtype == 28 or teamtype == 156:
                pendata['Type'] = 'Cross Check'
            elif teamtype == 30 or teamtype == 158:
                pendata['Type'] = 'Hooking'
            elif teamtype == 32 or teamtype == 160:
                pendata['Type'] = 'Tripping'
            elif teamtype == 34 or teamtype == 162:
                pendata['Type'] = 'Interference'
            elif teamtype == 36 or teamtype == 164:
                pendata['Type'] = 'Holding'
            elif teamtype == 38 or teamtype == 166:
                pendata['Type'] = 'Holding'
            else:
                pendata['Type'] = 'BAD'

            # Player that committed penalty

            f.seek(tmpExt + 4 - swap)
            offset = int(b2a_hex(f.read(1)), 16)

            if team == 'Away':
                pendata['Team'] = self.awtminfo['abv']
                pendata['Player'] = self.awroster[offset]['name']
            else:
                pendata['Team'] = self.hmtminfo['abv']
                pendata['Player'] = self.hmroster[offset]['name']

            tmpExt = tmpExt + 4
            self.pensum.append(pendata)

    def extStats(self, w):
        # Genesis or SNES?
        # Set Offsets and Endian-ness based on state type
        # Retrieve Team and Player Data from ROM
        # Extract Stats from Save State (Game Data)
        # Export to XLS file

        # Genesis or SNES? If so, what type of save, and set offsets and Endian-ness

        self.getStateType()

        # Retrieve Home and Away teams from Save State
        # Gens: Home - 59305 Away - 59307 GPGX: Home - 50001 Away - 50003 Snes9x: Home - 75841 Away - 75843 (RA 1.10 64-bit values)

        if self.system == "snes":
            home = 75841
            away = 75843

        else:
            home = 50001    # No need to check for Gens emulator, removing that function
            away = 50003

        with open(self.tempStateFile, 'rb') as f:
            print(home)
            print(self.endianfix)
            f.seek(home - self.endianfix)
            hmoffset = int(b2a_hex(f.read(1)).decode(), 16)
            f.seek(away - self.endianfix)
            awoffset = int(b2a_hex(f.read(1)).decode(), 16)
            print("System:  " + self.system)
            print(" Away offset: " + str(awoffset))
            print(" Home offset: " + str(hmoffset))

        # Retrieve Team Pointer List from ROM and get pointers for Home and Away

        self.tmptrs = self.tm_ptrs()
        hmptr = self.tmptrs[hmoffset]
        awptr = self.tmptrs[awoffset]
        print(hmptr)
        print(awptr)

        # Retrieve Team Info and Rosters

        with open(self.tempRomFile, 'rb') as f:
            self.hmtminfo = self.getTeamInfo(f, hmptr)
            self.awtminfo = self.getTeamInfo(f, awptr)
            self.hmroster = (self.getPlayerInfo(f, hmptr, self.hmtminfo['ploff'], self.hmtminfo['plsize']))
            self.awroster = (self.getPlayerInfo(f, awptr, self.awtminfo['ploff'], self.awtminfo['plsize']))

        # Retrieve Game Data

        with open(self.tempStateFile, 'rb') as f:
            self.getGameStats(f)
            self.getPlayerStats(f)
            self.getScoringSum(f)
            self.getPenSum(f)

            # print(self.pensum)

        # Export to XLS

        self.exportXLS(w)

def main():
    app = QApplication(sys.argv)
    exttool = statExtract()
    exttool.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
