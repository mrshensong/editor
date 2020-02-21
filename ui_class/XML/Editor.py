import re
import configparser
from PyQt5.QtCore import *
from PyQt5.Qsci import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from glv import Icon, Param, FileStatus
from ui_class.XML.Lexer import MyLexerXML


# xml编辑器
class Editor(QsciScintilla):
    signal = pyqtSignal(str)

    def __init__(self, parent, file=None):
        super(Editor, self).__init__(parent)
        self.font = QFont('Consolas', 14, QFont.Bold)
        # self.font = QFont('Ubuntu Mono', 14)
        # self.font = QFont('Arial ', 14)
        self.setFont(self.font)
        self.setUtf8(True)
        self.setMarginsFont(QFont('Arial ', 14))
        self.setMarginWidth(0, 20)
        # 设置行号
        self.setMarginLineNumbers(0, True)
        # 设置换行符为(\r\n)
        self.setEolMode(QsciScintilla.EolWindows)
        # 设置光标宽度(0不显示光标)
        self.setCaretWidth(2)
        # 设置光标颜色
        self.setCaretForegroundColor(QColor('darkCyan'))
        # 高亮显示光标所在行
        self.setCaretLineVisible(True)
        # 选中行背景色
        self.setCaretLineBackgroundColor(QColor('#F0F0F0'))
        # tab宽度设置为8, 也就是四个字符
        self.setTabWidth(4)
        # 换行后自动缩进
        self.setAutoIndent(True)
        self.setBackspaceUnindents(True)
        # 设置缩进的显示方式(用tab缩进时, 在缩进位置上显示一个竖点线)
        self.setIndentationGuides(True)
        # 设置折叠样式
        self.setFolding(QsciScintilla.PlainFoldStyle)
        # 设置折叠栏颜色
        self.setFoldMarginColors(Qt.gray, Qt.lightGray)
        # 当前文档中出现的名称以及xml自带的都自动补全提示
        # self.setAutoCompletionSource(QsciScintilla.AcsDocument)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        # 大小写敏感
        self.setAutoCompletionCaseSensitivity(True)
        # 是否用补全的字符串替换后面的字符串
        self.setAutoCompletionReplaceWord(False)
        # 输入一个字符就会出现自动补全的提示
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionUseSingle(QsciScintilla.AcusExplicit)
        # self.setAutoCompletionUseSingle(QsciScintilla.AcusAlways)
        self.autoCompleteFromAll()
        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        # 保存每一次操作后的text
        self.old_text = ''
        # 点击跳转标志位
        self.click_dump_flag = False
        # 触发事件
        self.cursorPositionChanged.connect(self.cursor_move)
        # 提示框选项图标(单词和函数的区分)
        word_image = QPixmap(Icon.word)
        function_image = QPixmap(Icon.function)
        self.registerImage(1, word_image)
        self.registerImage(2, function_image)
        # 获取配置文件
        self.cf = configparser.ConfigParser()
        self.cf.read(Param.config_file, encoding='utf-8')
        self.begin_line_label = self.cf.get('begin_line', 'label')
        self.key_words = eval(self.cf.get('keywords', 'word_list'))
        self.function_dict = {}
        for key in self.cf.options('function'):
            function = str(self.cf.get('function', key))
            function = function.replace('\\r', '\r')
            function = function.replace('\\n', '\n')
            function = function.replace('\\t', '\t')
            self.function_dict[key] = function
        # 定义语言为xml语言
        # self.lexer = QsciLexerXML(self)
        self.lexer = MyLexerXML(self)
        self.lexer.setFont(self.font)
        self.setLexer(self.lexer)
        self.__api = QsciAPIs(self.lexer)
        auto_completions = self.key_words + list(self.function_dict.keys())
        for item in auto_completions:
            # 如果是函数(图标显示function)
            if item in list(self.function_dict.keys()):
                auto_completions[auto_completions.index(item)] = item + '?2'
            # 如果是单词(图标显示word)
            else:
                auto_completions[auto_completions.index(item)] = item + '?1'
        for ac in auto_completions:
            self.__api.add(ac)
        self.__api.prepare()
        # 新建文件还是导入文件
        self.file = file
        if file is None:
            # 默认第一行内容
            self.setText(self.begin_line_label)
        else:
            with open(file, 'r', encoding='utf-8') as f:
                editor_text = f.read()
                editor_text = editor_text.replace('\n\n', '\r\n')
            self.setText(editor_text)

    # 右键菜单展示
    def show_menu(self, point):
        # 菜单样式(整体背景#4D4D4D,选中背景#1E90FF,选中字体#E8E8E8,选中边界#575757,分离器背景#757575)
        menu_qss = "QMenu{color: #242424; background: #F0F0F0; margin: 2px;}\
                    QMenu::item{padding:3px 20px 3px 20px;}\
                    QMenu::indicator{width:13px; height:13px;}\
                    QMenu::item:selected:enabled{color:#242424; border:0px solid #575757; background:#1E90FF;}\
                    QMenu::item:selected:!enabled{color:#969696; border:0px solid #575757; background:#99CCFF;}\
                    QMenu::item:!enabled{color: #969696;}\
                    QMenu::item:enabled{color: #242424;}\
                    QMenu::separator{height:1px; background:#757575;}"
        self.menu = QMenu(self)
        self.menu.setStyleSheet(menu_qss)
        # 撤销上一操作
        self.undo_action = QAction('撤消上一次操作(Ctrl+Z)', self)
        self.undo_action.triggered.connect(self.undo_operate)
        if self.isUndoAvailable() is False:
            self.undo_action.setEnabled(False)
        # 恢复上一操作
        self.redo_action = QAction('恢复上一次操作(Ctrl+Y)', self)
        self.redo_action.triggered.connect(self.redo_operate)
        if self.isRedoAvailable() is False:
            self.redo_action.setEnabled(False)
        # 剪切
        self.cut_action = QAction('剪切(Ctrl+X)', self)
        self.cut_action.triggered.connect(self.cut_operate)
        if self.selectedText() == '':
            self.cut_action.setEnabled(False)
        # 复制
        self.copy_action = QAction('复制(Ctrl+C)', self)
        self.copy_action.triggered.connect(self.copy_operate)
        if self.selectedText() == '':
            self.copy_action.setEnabled(False)
        # 粘贴
        self.paste_action = QAction('粘贴(Ctrl+V)', self)
        self.paste_action.triggered.connect(self.paste_operate)
        # 删除
        self.delete_action = QAction('删除', self)
        self.delete_action.triggered.connect(self.delete_operate)
        if self.selectedText() == '':
            self.delete_action.setEnabled(False)
        # 全部选中
        self.select_all_action = QAction('选中全部(Ctrl+A)', self)
        self.select_all_action.triggered.connect(self.select_all_operate)
        # 添加/去除-注释
        self.comment_action = QAction('添加/去除-注释(Ctrl+L)', self)
        self.comment_action.triggered.connect(self.comment_operate)
        # 菜单添加action
        self.menu.addAction(self.undo_action)
        self.menu.addAction(self.redo_action)
        self.menu.addAction(self.cut_action)
        self.menu.addAction(self.copy_action)
        self.menu.addAction(self.paste_action)
        self.menu.addAction(self.delete_action)
        self.menu.addAction(self.select_all_action)
        self.menu.addAction(self.comment_action)
        self.menu.exec(self.mapToGlobal(point))

    def undo_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.undo()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def redo_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.redo()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def cut_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.cut()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def copy_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.copy()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def paste_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.paste()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def delete_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.removeSelectedText()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def select_all_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.selectAll(True)
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    def comment_operate(self):
        # 注释的时候先关闭自动补全后半部分功能
        self.cursorPositionChanged.disconnect(self.cursor_move)
        # 切换注释
        self.toggle_comment()
        self.cursorPositionChanged.connect(self.cursor_move)
        self.old_text = self.text()

    # 文件状态更新
    def file_status_update(self):
        with open(self.file, 'r', encoding='utf-8') as f:
            text = f.read()
            text = text.replace('\n\n', '\r\n')
        if self.text() == text:
            self.signal.emit('file_status>' + FileStatus.save_status)
        else:
            self.signal.emit('file_status>' + FileStatus.not_save_status)

    # 光标移动事件
    def cursor_move(self):
        # 调整边栏宽度
        line_digit = len(str(len(self.text().split('\n'))))
        margin_width = 20 + (line_digit - 1) * 13
        self.setMarginWidth(0, margin_width)
        # 文本内容
        text = self.text()
        # 当前文本长度和上次文本长度
        text_length = len(text)
        old_text_length = len(self.old_text)
        line, index = self.getCursorPosition()
        # 只有新增字符的情况下才执行如下代码(删除文本不需要执行)
        if text_length > old_text_length:
            # 通过键盘键入字符
            if (text_length - old_text_length) == 1:
                # line, index = self.getCursorPosition()
                current_line_text = self.text(line)
                list_current_line_text = list(current_line_text)
                current_char = list_current_line_text[index-1] if index > 0 else None
                if current_char == '>':
                    for i in range(index-1, -1, -1):
                        if list_current_line_text[i] == '<' and list_current_line_text[i+1] != '?':
                            key_words = ''.join(list_current_line_text[i+1:index-1])
                            self.insertAt('</'+key_words+'>', line, index)
                            break
        self.old_text = self.text()
        # 获取当前光标
        cursor_position = '[' + str(line+1) + ':' + str(index) + ']'
        self.signal.emit('cursor_position>' + cursor_position)
        # 文件状态更新
        self.file_status_update()

    # 切换注释
    def toggle_comment(self):
        # 是否需要注释的标志
        comment_line_num = 0
        # 获取起始和结束行号
        start_line, end_line = self.get_selections()
        for line in range(start_line, end_line + 1):
            current_line_text = self.text(line).strip()
            if current_line_text.startswith('<!--') and current_line_text.endswith('-->'):
                comment_line_num = comment_line_num
            else:
                comment_line_num += 1
        if comment_line_num > 0:
            # 添加注释
            self.add_comment(start_line, end_line)
        else:
            # 取消注释
            self.cancel_comment(start_line, end_line)

    # 获取选中行(注释需要用到, 开始行和结束行)
    def get_selections(self):
        start_position = self.SendScintilla(QsciScintillaBase.SCI_GETSELECTIONSTART)
        end_position = self.SendScintilla(QsciScintillaBase.SCI_GETSELECTIONEND)
        start_line = self.SendScintilla(QsciScintillaBase.SCI_LINEFROMPOSITION, start_position)
        end_line = self.SendScintilla(QsciScintillaBase.SCI_LINEFROMPOSITION, end_position)
        return start_line, end_line

    # 添加注释
    def add_comment(self, start_line, end_line):
        last_line = end_line
        # 如果选中的最后一行是整个文本的最后一行
        if last_line == self.lines() - 1:
            end_index = len(self.text(end_line))
        else:
            end_index = len(self.text(end_line)) - 1
        # 设置选中(开始行/列, 结束行/列)
        self.setSelection(start_line, 0, end_line, end_index)
        selected_text = self.selectedText()
        selected_list = selected_text.split('\r\n')
        if len(selected_list) > 1 and selected_list[-1] == '':
            selected_list.pop(-1)
        # 保存将每一行切为的三个部分(三个部分为一个list)
        line_separate_list = []
        # 注释结束后光标位置(默认-1,此时不需要设置光标位置)
        cursor_position = -1
        # 将一行内容拆解三个部分(1\t or '' 2<note> 3 ''or...)
        for line in selected_list:
            # 如果存在line内容
            if line:
                line_list = []
                if '<' in line and '>' in line:
                    line_list.append(line.split('<')[0])
                    line_list.append(re.findall('<.*>', line)[0])
                    line_list.append(line.split('>')[-1])
                    line_separate_list.append(line_list)
                elif len(line) > 0:
                    line_list.append(re.findall('\s*', line)[0])
                    line_list.append(line.strip())
                    line_list.append('')
                    line_separate_list.append(line_list)
                    if line.strip() == '':
                        cursor_position = len(line) + 4
                else:
                    line_list = ['', '', '']
                    line_separate_list.append(line_list)
                    cursor_position =  4
            else:
                line_list = ['', '', '']
                line_separate_list.append(line_list)
                cursor_position = 4
        for i in range(len(line_separate_list)):
            if '<!--' not in selected_list[i] and '-->' not in selected_list[i]:
                selected_list[i] = line_separate_list[i][0] + '<!--' + line_separate_list[i][1] + '-->' + line_separate_list[i][2]
        if self.text(end_line).endswith('\r\n'):
            replace_text = '\r\n'.join(selected_list) + '\r\n'
        else:
            replace_text = '\r\n'.join(selected_list)
        self.replaceSelectedText(replace_text)
        if cursor_position != -1:
            self.setCursorPosition(end_line, cursor_position)

    # 取消注释
    def cancel_comment(self, start_line, end_line):
        last_line = end_line
        # 如果选中的最后一行是整个文本的最后一行
        if last_line == self.lines() - 1:
            end_index = len(self.text(end_line))
        else:
            end_index = len(self.text(end_line)) - 1
        # 设置选中(开始行/列, 结束行/列)
        self.setSelection(start_line, 0, end_line, end_index)
        selected_text = self.selectedText()
        selected_list = selected_text.split('\r\n')
        for line in selected_list:
            if '<!--' in line and '-->' in line:
                selected_list[selected_list.index(line)] = line.replace('<!--', '', 1).replace('-->', '', 1)
        replace_text = '\r\n'.join(selected_list)
        self.replaceSelectedText(replace_text)

    # 删除单/双引号操作
    def delete_quotation_marks(self, event):
        line, index = self.getCursorPosition()
        current_line_text = self.text(line)
        current_line_text_list = list(current_line_text)
        # 当前光标肯定不是行末('')
        if len(current_line_text) > index:
            current_char = current_line_text_list[index-1]
            next_char = current_line_text_list[index]
            if current_char == next_char and current_char in ["'", '"']:
                self.setSelection(line, index-1, line, index+1)
                self.replaceSelectedText('')
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        else:
            # 不要破坏原有功能
            QsciScintilla.keyPressEvent(self, event)

    # 敲回车自动补全处理函数
    def auto_completion(self, event):
        line_before, index_before = self.getCursorPosition()
        QsciScintilla.keyPressEvent(self, event)
        line_after, index_after = self.getCursorPosition()
        # 获取当前鼠标位置单词(此处可以重新获取这个词,只以空格为分割)
        current_word = self.wordAtLineIndex(line_after, index_after)
        if current_word != '':
            # 选中补全的单词(后面会用段落代替)
            self.setSelection(line_after, index_after-len(current_word), line_after, index_after)
            # 替换为函数块
            if current_word in self.function_dict.keys():
                self.replaceSelectedText(self.function_dict[current_word])
            else:
                # 此处可以添加更改(将函数名代替为函数)
                self.setCursorPosition(line_after, index_after)

    # 这是重写键盘事件
    def keyPressEvent(self, event):
        # Ctrl + / 键 注释or取消注释
        if (event.key() == Qt.Key_Slash):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.comment_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + Z 键 撤销上一步操作
        elif (event.key() == Qt.Key_Z):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.undo_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + Y 键 恢复上一步操作
        elif (event.key() == Qt.Key_Y):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.redo_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + X 键 剪切
        elif (event.key() == Qt.Key_X):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.cut_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + C 键 复制
        elif (event.key() == Qt.Key_C):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.copy_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + V 键 粘贴
        elif (event.key() == Qt.Key_V):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.paste_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + A 键 全部选中
        elif (event.key() == Qt.Key_A):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.select_all_operate()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # Ctrl + D 键(需要更新old_text)
        elif (event.key() == Qt.Key_D):
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
                self.old_text = self.text()
            else:
                # 不要破坏原有功能
                QsciScintilla.keyPressEvent(self, event)
        # 单引号处理
        elif (event.key() == Qt.Key_Apostrophe):
            QsciScintilla.keyPressEvent(self, event)
            self.insert("'")
            self.old_text = self.text()
        # 双引号处理
        elif (event.key() == Qt.Key_QuoteDbl):
            QsciScintilla.keyPressEvent(self, event)
            self.insert('"')
            self.old_text = self.text()
        # 删除单/双引号处理
        elif (event.key() == Qt.Key_Backspace):
            self.delete_quotation_marks(event)
            self.old_text = self.text()
        # 回车自动补全处理
        elif (event.key() == Qt.Key_Return):
            self.auto_completion(event)
        else:
            # 不要破坏原有功能
            QsciScintilla.keyPressEvent(self, event)

    # 鼠标滚动事件(字体放大缩小)
    def wheelEvent(self, event):
        # Ctrl + 滚轮 控制字体缩放
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            da = event.angleDelta()
            # QsciScintilla 自带缩放的功能, 参数是增加的字体点数
            if da.y() > 0:
                self.zoomIn(1)
            elif da.y() < 0:
                self.zoomOut(1)
        else:
            # 留点汤给父类，不然滚轮无法翻页
            super().wheelEvent(event)

    # 鼠标点击事件
    def mousePressEvent(self, event):
        # 继承原有功能
        super().mousePressEvent(event)
        # Ctrl+左键按下(点击跳转标志位)
        if event.buttons() == Qt.LeftButton:
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.click_dump_flag = True

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        # 继承原有功能
        super().mouseReleaseEvent(event)
        if self.click_dump_flag is True:
            self.indicator_clicked()
        self.click_dump_flag = False

    # 点击跳转功能处理
    def indicator_clicked(self):
        line, index = self.getCursorPosition()
        indicator_word = self.wordAtLineIndex(line, index)
        print(indicator_word)