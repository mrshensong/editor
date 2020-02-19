class Param:
    config_file = 'config/config.ini'
    translator_file = 'config/qt_zh_CN.qm'

class Icon:
    close_tab = 'config/icon/close_tab.png'
    close_tab_hover = 'config/icon/close_tab_hover.png'
    function = 'config/icon/function.png'
    word = 'config/icon/word.png'
    new_file = 'config/icon/new_file.png'
    open_folder = 'config/icon/open_folder.png'
    new = 'config/icon/new.png'
    open_file = 'config/icon/open_file.png'
    save_file = 'config/icon/save_file.png'
    save_as_file = 'config/icon/save_as_file.png'
    file = 'config/icon/file.png'
    path = 'config/icon/path.png'


# 样式
class BeautifyStyle:
    # font_family = 'font-family: Times New Roman;'
    font_family = 'font-family: Consolas;'
    font_size = 'font-size: 13pt;'
    file_dialog_qss = 'QFileDialog {font-family: Times New Roman; background-color: beige;}'


# 文件状态
class FileStatus:
    save_status = '已保存'
    not_save_status = '未保存'


# 文件格式统一
class MergePath:
    merged_path = None

    def __init__(self, *args):
        file_sep_list = []
        for arg in args:
            if '\\' in arg:
                file_sep_list += arg.split('\\')
            else:
                file_sep_list += arg.split('/')
        self.merged_path = '/'.join(file_sep_list)