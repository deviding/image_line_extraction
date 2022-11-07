#-*- coding:utf-8 -*-
from image_line_gui import ImageLineGui

import sys
from PySide6.QtWidgets import *


def main():
    # Qtアプリケーションの作成
    app = QApplication(sys.argv)

    # フォームを作成して表示
    form = ImageLineGui()
    form.show()

    # 画面表示のためのループ
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
