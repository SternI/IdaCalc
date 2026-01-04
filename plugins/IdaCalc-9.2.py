import idaapi
import ida_kernwin
from PySide6 import QtWidgets, QtGui

class IdaCalcWidget(idaapi.PluginForm):
    def __init__(self):
        super().__init__()
        self.History = []
        self.UnsignedMode = False
        self.BitWidth = 64
        
    def OnCreate(self, form):
        self.Parent = self.FormToPyQtWidget(form)
        self.InitUI()
                
    def InitUI(self):
        Layout = QtWidgets.QVBoxLayout()
        Layout.setSpacing(10)
        
        InputLayout = QtWidgets.QHBoxLayout()
        self.InputField = QtWidgets.QLineEdit()
        self.InputField.setPlaceholderText("Enter expression (e.g., 0x1234567 - 0x67)")
        self.InputField.setFont(QtGui.QFont("Courier", 10))
        self.InputField.returnPressed.connect(self.Calculate)
        InputLayout.addWidget(self.InputField)
        
        ClearBtn = QtWidgets.QPushButton("Clear")
        ClearBtn.clicked.connect(self.ClearInput)
        ClearBtn.setMaximumWidth(60)
        InputLayout.addWidget(ClearBtn)
        
        Layout.addLayout(InputLayout)
        
        OpLayout = QtWidgets.QHBoxLayout()
        Operators = ['+', '-', '*', '//', '<<', '>>', '&&', '|', '^']
        for op in Operators:
            DisplayText = op.replace('&&', '&')
            DisplayText = op.replace('//', '/')
            Btn = QtWidgets.QPushButton(DisplayText)
            Btn.clicked.connect(lambda checked, o=op: self.AddOperator(o))
            Btn.setMaximumWidth(50)
            OpLayout.addWidget(Btn)
        Layout.addLayout(OpLayout)
        
        CalcBtn = QtWidgets.QPushButton("Calculate")
        CalcBtn.clicked.connect(self.Calculate)
        CalcBtn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        Layout.addWidget(CalcBtn)
        
        UnsignedLayout = QtWidgets.QHBoxLayout()
        self.UnsignedCheck = QtWidgets.QCheckBox("Unsigned Mode (Mask to bit width)")
        self.UnsignedCheck.stateChanged.connect(self.OnUnsignedToggle)
        UnsignedLayout.addWidget(self.UnsignedCheck)
        
        UnsignedLayout.addWidget(QtWidgets.QLabel("Bit Width:"))
        self.BitWidthCombo = QtWidgets.QComboBox()
        self.BitWidthCombo.addItems(["8-bit", "16-bit", "32-bit", "64-bit"])
        self.BitWidthCombo.setCurrentIndex(3)
        self.BitWidthCombo.currentIndexChanged.connect(self.OnBitWidthChange)
        UnsignedLayout.addWidget(self.BitWidthCombo)
        
        Layout.addLayout(UnsignedLayout)

        ResultGroup = QtWidgets.QGroupBox("Result")
        ResultLayout = QtWidgets.QVBoxLayout()
        
        self.ResultHex = QtWidgets.QLineEdit()
        self.ResultHex.setReadOnly(True)
        self.ResultHex.setFont(QtGui.QFont("Courier", 10))
        self.ResultHex.setPlaceholderText("Hex result")
        
        self.ResultDec = QtWidgets.QLineEdit()
        self.ResultDec.setReadOnly(True)
        self.ResultDec.setFont(QtGui.QFont("Courier", 10))
        self.ResultDec.setPlaceholderText("Decimal result")
        
        self.ResultBin = QtWidgets.QLineEdit()
        self.ResultBin.setReadOnly(True)
        self.ResultBin.setFont(QtGui.QFont("Courier", 10))
        self.ResultBin.setPlaceholderText("Binary result")
        
        ResultLayout.addWidget(QtWidgets.QLabel("Hexadecimal:"))
        ResultLayout.addWidget(self.ResultHex)
        ResultLayout.addWidget(QtWidgets.QLabel("Decimal:"))
        ResultLayout.addWidget(self.ResultDec)
        ResultLayout.addWidget(QtWidgets.QLabel("Binary:"))
        ResultLayout.addWidget(self.ResultBin)
        
        ResultGroup.setLayout(ResultLayout)
        Layout.addWidget(ResultGroup)
        
        CopyLayout = QtWidgets.QHBoxLayout()
        CopyHexBtn = QtWidgets.QPushButton("Copy Hex")
        CopyHexBtn.clicked.connect(self.CopyHex)
        CopyDecBtn = QtWidgets.QPushButton("Copy Dec")
        CopyDecBtn.clicked.connect(self.CopyDec)
        CopyLayout.addWidget(CopyHexBtn)
        CopyLayout.addWidget(CopyDecBtn)
        Layout.addLayout(CopyLayout)
        
        CopyBytesBtn = QtWidgets.QPushButton("Copy as Hex Bytes")
        CopyBytesBtn.clicked.connect(self.CopyHexBytes)
        CopyBytesBtn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        Layout.addWidget(CopyBytesBtn)
        
        HistoryGroup = QtWidgets.QGroupBox("History (Click to reuse)")
        HistoryLayout = QtWidgets.QVBoxLayout()
        self.HistoryList = QtWidgets.QListWidget()
        self.HistoryList.setMaximumHeight(120)
        self.HistoryList.setFont(QtGui.QFont("Courier", 9))
        self.HistoryList.itemDoubleClicked.connect(self.LoadFromHistory)
        HistoryLayout.addWidget(self.HistoryList)
        HistoryGroup.setLayout(HistoryLayout)
        Layout.addWidget(HistoryGroup)
        
        Info = QtWidgets.QLabel(
            "• Supports hex, decimal, binary\n"
            "• Bitwise ops: & | << >>\n"
            "• Use ^ for power\n"
            "• Use / for integer division\n"
            "• Unsigned mode masks overflow\n"
            "• Hotkey: Ctrl+Shift+C"
        )
        Info.setStyleSheet("QLabel { color: gray; font-size: 9pt; }")
        Layout.addWidget(Info)
        
        self.Parent.setLayout(Layout)
        self.InputField.setFocus()
    
    def OnClose(self, form):
        pass
    
    def OnUnsignedToggle(self, state):
        self.UnsignedMode = (state == 2)
        if self.ResultDec.text():
            self.Calculate()
    
    def OnBitWidthChange(self, index):
        widths = [8, 16, 32, 64]
        self.BitWidth = widths[index]
        if self.UnsignedMode and self.ResultDec.text():
            self.Calculate()
        
    def AddOperator(self, op):
        Current = self.InputField.text()
        if Current.endswith(' '):
            NewText = Current + op + ' '
        else:
            NewText = Current + ' ' + op + ' '
        self.InputField.setText(NewText)
        self.InputField.setFocus()
        
    def ClearInput(self):
        self.InputField.clear()
        self.ResultHex.clear()
        self.ResultDec.clear()
        self.ResultBin.clear()
        
    def ParseNumber(self, s):
        s = s.strip()
        if s.startswith('0x') or s.startswith('0X'):
            return int(s, 16)
        elif s.startswith('0b') or s.startswith('0B'):
            return int(s, 2)
        else:
            return int(s)
            
    def Calculate(self):
        Expr = self.InputField.text().strip()
        if not Expr:
            return
            
        try:
            import re
            
            def ReplaceHex(match):
                return str(int(match.group(0), 16))
            ExprEval = re.sub(r'0x[0-9a-fA-F]+', ReplaceHex, Expr)
            
            def ReplaceBin(match):
                return str(int(match.group(0), 2))
            ExprEval = re.sub(r'0b[01]+', ReplaceBin, ExprEval)
            
            ExprEval = ExprEval.replace('^', '**')

            Result = eval(ExprEval)
                        
            if isinstance(Result, float):
                if Result.is_integer():
                    Result = int(Result)
            
            if isinstance(Result, int):
                DisplayResult = Result
                
                if self.UnsignedMode:
                    mask = (1 << self.BitWidth) - 1
                    DisplayResult = Result & mask
                    
                    self.ResultHex.setText(f"0x{DisplayResult:X}")
                    self.ResultDec.setText(str(DisplayResult))
                    self.ResultBin.setText(bin(DisplayResult))
                    
                    HistoryText = f"{Expr} = {DisplayResult} (0x{DisplayResult:X}) [unsigned {self.BitWidth}-bit]"
                else:
                    self.ResultHex.setText(f"0x{Result:X}" if Result >= 0 else f"-0x{abs(Result):X}")
                    self.ResultDec.setText(str(Result))
                    self.ResultBin.setText(bin(Result))
                    
                    HistoryText = f"{Expr} = {Result} (0x{Result:X})" if Result >= 0 else f"{Expr} = {Result} (-0x{abs(Result):X})"
                
                if HistoryText not in [self.HistoryList.item(i).text() for i in range(self.HistoryList.count())]:
                    self.HistoryList.insertItem(0, HistoryText)
                    if self.HistoryList.count() > 10:
                        self.HistoryList.takeItem(10)
                        
            elif isinstance(Result, float):
                self.ResultDec.setText(str(Result))
                self.ResultHex.setText(f"0x{int(Result):X}")
                self.ResultBin.setText(bin(int(Result)))
                
                HistoryText = f"{Expr} = {Result} (≈0x{int(Result):X})"
                if HistoryText not in [self.HistoryList.item(i).text() for i in range(self.HistoryList.count())]:
                    self.HistoryList.insertItem(0, HistoryText)
                    if self.HistoryList.count() > 10:
                        self.HistoryList.takeItem(10)
            else:
                self.ResultDec.setText(str(Result))
                self.ResultHex.clear()
                self.ResultBin.clear()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            ida_kernwin.warning(f"IdaCalc: Error calculating: {str(e)}")
            
    def CopyHex(self):
        Text = self.ResultHex.text()
        if Text:
            QtWidgets.QApplication.clipboard().setText(Text)
            print(f"IdaCalc: Copied to clipboard: {Text}")
            
    def CopyDec(self):
        Text = self.ResultDec.text()
        if Text:
            QtWidgets.QApplication.clipboard().setText(Text)
            print(f"IdaCalc: Copied to clipboard: {Text}")
    
    def CopyHexBytes(self):
        Text = self.ResultHex.text()
        if Text:
            try:
                IsNegative = Text.startswith('-0x')
                
                HexValue = Text.replace('-0x', '').replace('0x', '').replace('0X', '')
                
                if len(HexValue) % 2 != 0:
                    HexValue = '0' + HexValue
                
                ByteList = [HexValue[i:i+2] for i in range(0, len(HexValue), 2)]
                
                ByteList.reverse()
                
                Bytes = ' '.join(ByteList)
                
                if IsNegative:
                    Value = int(HexValue, 16)
                    ByteSize = len(ByteList)
                    if ByteSize <= 1:
                        ByteSize = 1
                    elif ByteSize <= 2:
                        ByteSize = 2
                    elif ByteSize <= 4:
                        ByteSize = 4
                    else:
                        ByteSize = 8
                    
                    MaxVal = (1 << (ByteSize * 8))
                    TwosComp = MaxVal - Value
                    
                    HexValue = f"{TwosComp:0{ByteSize*2}X}"
                    ByteList = [HexValue[i:i+2] for i in range(0, len(HexValue), 2)]
                    ByteList.reverse()
                    Bytes = ' '.join(ByteList)
                    
                    QtWidgets.QApplication.clipboard().setText(Bytes)
                    print(f"IdaCalc: Copied negative hex bytes (two's complement, little-endian) to clipboard: {Bytes}")
                else:
                    QtWidgets.QApplication.clipboard().setText(Bytes)
                    print(f"IdaCalc: Copied hex bytes (little-endian) to clipboard: {Bytes}")
                    
            except Exception as e:
                ida_kernwin.warning(f"IdaCalc: Error converting to hex bytes: {str(e)}")
            
    def LoadFromHistory(self, item):
        Text = item.text()
        
        if 'unsigned' in Text:
            import re
            match = re.search(r'\[unsigned (\d+)-bit\]', Text)
            if match:
                bit_width = int(match.group(1))
                width_map = {8: 0, 16: 1, 32: 2, 64: 3}
                if bit_width in width_map:
                    self.BitWidthCombo.setCurrentIndex(width_map[bit_width])
            self.UnsignedCheck.setChecked(True)
        else:
            self.UnsignedCheck.setChecked(False)
        
        Expr = Text.split('=')[0].strip()
        self.InputField.setText(Expr)
        self.Calculate()


class IdaCalcPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_KEEP
    comment = "IdaCalc - Programming calculator for IDA Pro 9.2+"
    help = "IdaCalc - Programming calculator with hex support"
    wanted_name = "IdaCalc"
    wanted_hotkey = "Ctrl-Shift-C"
    
    def init(self):
        self.Widget = None
        print("IdaCalc: Plugin loaded! Press Ctrl+Shift+C to open.")
        return idaapi.PLUGIN_KEEP
        
    def run(self, arg):
        if self.Widget is None:
            self.Widget = IdaCalcWidget()
        
        self.Widget.Show("IdaCalc", options=(ida_kernwin.WOPN_RESTORE | ida_kernwin.WOPN_PERSIST))
        ida_kernwin.set_dock_pos("IdaCalc", None, ida_kernwin.DP_FLOATING)
        
    def term(self):
        if self.Widget:
            self.Widget.Close(idaapi.PluginForm.WCLS_SAVE)


def PLUGIN_ENTRY():
    return IdaCalcPlugin()