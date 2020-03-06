from PyQt5.QtWidgets import QGraphicsOpacityEffect, QFrame
from PyQt5.QtCore import QPropertyAnimation, Qt
from PyQt5.Qsci import QsciScintilla


class MiniMap(QsciScintilla):

    def __init__(self, parent, editor):
        QsciScintilla.__init__(self, parent)
        # 设置最大最小宽度
        self.setMaximumWidth(300)
        self.setMinimumWidth(150)
        self.editor = editor
        # 设置缩放(比原始大小缩小10个档)
        self.zoomIn(-10)
        # 词法分析器
        self.lexer = self.editor.lexer
        self.setLexer(self.lexer)
        # 缩略图文本
        self.setText(self.editor.text())
        # mini_map可以显示的行数
        self.lines_on_screen = 0
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        # 隐藏拖动条
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, False)
        self.SendScintilla(QsciScintilla.SCI_SETVSCROLLBAR, False)
        # 设置隐藏选择
        self.SendScintilla(QsciScintilla.SCI_HIDESELECTION, True)
        self.setFolding(QsciScintilla.NoFoldStyle, 1)
        # 设置只读
        self.setReadOnly(True)
        self.setCaretWidth(0)
        # 设置背景透明
        self.setStyleSheet("background: transparent; border: 0px;")
        # 设置透明度
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.5)
        # 设置滑动面板
        self.slider = Slider(self)

    # 尺寸更改
    def resizeEvent(self, event):
        super(MiniMap, self).resizeEvent(event)
        self.change_slider_width()

    # 更改slider宽度
    def change_slider_width(self):
        self.lines_on_screen = self.SendScintilla(QsciScintilla.SCI_LINESONSCREEN)
        slider_width = self.width()
        slider_height = int((self.editor.lines_on_screen / self.lines_on_screen) * self.height())
        self.slider.setFixedWidth(slider_width)
        self.slider.setFixedHeight(slider_height)

    # 缩略图代码更新
    def update_code(self):
        self.setText(self.editor.text())


class Slider(QFrame):

    def __init__(self, mini_map):
        QFrame.__init__(self, mini_map)
        self.mini_map = mini_map
        self.setStyleSheet("background: gray; border-radius: 3px;")
        # Opacity
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.3)
        # Animation
        self.animation = QPropertyAnimation(self.effect)
        self.animation.setDuration(150)
        # Cursor
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, event):
        super(Slider, self).mouseMoveEvent(event)

        # pos = self.mapToParent(event.pos())
        # dy = pos.y() - (self.height() / 2)
        # if dy < 0:
        #     dy = 0
        # self.move(0, dy)
        # pos.setY(pos.y() - event.pos().y())
        # self.mini_map.editor.verticalScrollBar().setValue(pos.y())
        # self.mini_map.verticalScrollBar().setSliderPosition(self.mini_map.verticalScrollBar().sliderPosition() + 2)
        # self.mini_map.verticalScrollBar().setValue(pos.y() - event.pos().y())

    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        self.setCursor(Qt.ClosedHandCursor)
        pos = self.mapToParent(event.pos())
        self.move(0, pos.y() - int((self.height() / 2)))

    def mouseReleaseEvent(self, event):
        super(Slider, self).mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)