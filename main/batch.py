#-*- coding:utf-8 -*-
from setting_data import SettingData
from line_extraction import LineExtraction

import os, sys, glob
import cv2
import numpy as np
from PIL import Image

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class EmitObject():
    """ Emitで渡すためのクラス
    """
    def __init__(self, file_name=str, pre_img=QPixmap):
        """ コンストラクタ

            Args:
                file_name (str)  : ファイル名
                pre_img (QPixmap): プレビュー用画像
        """
        self.file_name = file_name
        self.pre_img   = pre_img


    def get_file_name(self):
        """ ファイル名を取得する関数

            Returns:
                file_name (str): ファイル名
        """
        return self.file_name

    def get_pre_img(self):
        """ プレビュー画像を取得する関数

            Returns:
                pre_img (QPixmap): プレビュー用画像
        """
        return self.pre_img


class BatchGui(QDialog):
    """ 一括処理を行うGUIクラス
    """
    TITLE = "一括処理"
    WINDOW_WIDTH    = 420
    WINDOW_HEIGHT   = 260
    PREVIEW_WIDTH   = 160
    PREVIEW_HEIGHT  = 90
    TEXT_BOX_WIDTH  = 230
    TEXT_BOX_HEIGHT = 90
    PB_WIDTH        = 380


    def __init__(self, parent=QDialog):
        """ コンストラクタ
        """
        super(BatchGui, self).__init__(parent)

        self.setting_data = None
        self.my_dir_path  = os.path.abspath(os.path.dirname(sys.argv[0]))

        # Widgetsの設定(タイトル、固定横幅、固定縦幅)
        self.setWindowTitle(self.TITLE)
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.setFixedHeight(self.WINDOW_HEIGHT)

        # 対象フォルダ部分
        target_layout = QHBoxLayout()
        self.target_path = QLineEdit("")
        self.target_path.setEnabled(False) # テキスト入力を禁止
        self.target_select_button = QPushButton("参照")
        self.target_select_button.clicked.connect(self.target_folder_dialog)
        target_layout.addWidget(QLabel("変換フォルダ:"), 1)
        target_layout.addWidget(self.target_path, 5)
        target_layout.addWidget(self.target_select_button, 1)

        # 保存フォルダ部分
        save_layout = QHBoxLayout()
        self.save_path = QLineEdit("")
        self.save_path.setEnabled(False) # テキスト入力を禁止
        self.save_select_button = QPushButton("参照")
        self.save_select_button.clicked.connect(self.save_folder_dialog)
        save_layout.addWidget(QLabel("保存フォルダ:"), 1)
        save_layout.addWidget(self.save_path, 5)
        save_layout.addWidget(self.save_select_button, 1)

        # 画像プレビュー・テキストボックス部分
        img_layout = QHBoxLayout()
        self.img_label = QLabel()
        self.img_label.setFixedSize(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # 画像を中央に表示
        self.img_label.setFrameStyle(QFrame.Box)
        img_layout.addWidget(self.img_label)

        self.textbox = QListView()
        self.text_list = QStringListModel()
        self.textbox.setModel(self.text_list)
        self.textbox.setFixedSize(self.TEXT_BOX_WIDTH, self.TEXT_BOX_HEIGHT)
        img_layout.addWidget(self.textbox)

        # プログレスバー部分
        pb_layput = QHBoxLayout()
        self.pb = QProgressBar()
        self.pb.setFixedWidth(self.PB_WIDTH)
        self.pb.setTextVisible(False)
        pb_layput.addWidget(self.pb)

        # ボタン部分
        batch_btn_layout = QHBoxLayout()
        self.batch_button = QPushButton("一括処理開始")
        self.batch_button.clicked.connect(self.batch_line_extraction)
        batch_btn_layout.addWidget(QLabel(""), 1)
        batch_btn_layout.addWidget(self.batch_button, 1)
        batch_btn_layout.addWidget(QLabel(""), 1)

        # レイアウトを作成して各要素を配置
        layout = QVBoxLayout()
        layout.addLayout(target_layout)
        layout.addSpacing(6)
        layout.addLayout(save_layout)
        layout.addSpacing(6)
        layout.addLayout(img_layout)
        layout.addSpacing(6)
        layout.addLayout(pb_layput)
        layout.addSpacing(6)
        layout.addLayout(batch_btn_layout)

        # レイアウトを画面に設定
        self.setLayout(layout)

        # 一括実行プロセスの準備
        self.rp = RunProcess()
        self.rp.process_thread.connect(self.update_log)
        self.rp.finished.connect(self.show_result)


    def clear_pre_log(self):
        """ プレビューとログ部分をクリアする関数
        """
        self.img_label.clear()
        self.text_list.removeRows(0, self.text_list.rowCount())


    def set_setting_data(self, setting_data=SettingData):
        """ 設定値のオブジェクトを設定する関数

            Args:
                setting_data (SettingData) : 設定値オブジェクト
        """
        self.setting_data = setting_data


    def set_close_fnc(self, func, pre_flg, save_flg):
        """ 設定値のオブジェクトを設定する関数

            Args:
                func (function) : 実行する関数
                pre_flg  (bool) : プレビューボタンのフラグ
                save_flg (bool) : 保存ボタンのフラグ
        """
        self.func = func
        self.pre_flg = pre_flg
        self.save_flg = save_flg


    def closeEvent(self, event):
        """ 一括処理のGUIが「×」で閉じられる時に呼ばれる関数

            Args:
                event (event) : イベント
        """
        self.func(True, self.pre_flg, self.save_flg)


    def target_folder_dialog(self):
        """ 対象フォルダ選択ダイアログを表示する関数
        """
        path = self.target_path.text()
        if path == "":
            path = self.my_dir_path

        dir_path = QFileDialog.getExistingDirectory(self, "対象フォルダ選択", path)

        if dir_path:
            self.target_path.setText(dir_path)


    def save_folder_dialog(self):
        """ 保存先フォルダ選択ダイアログを表示する関数
        """
        # すでに設定されているフォルダがあればそれを開く
        path = self.my_dir_path

        path_target = self.target_path.text()
        path_save = self.save_path.text()

        if not path_save == "":
            path = path_save
        elif not path_target == "":
            path = path_target

        dir_path = QFileDialog.getExistingDirectory(self, "保存先フォルダ選択", path)

        if dir_path:
            self.save_path.setText(dir_path)


    def batch_line_extraction(self):
        """ 画像変換を一括処理で実行する関数
        """
        target_path = self.target_path.text()
        save_path   = self.save_path.text()

        # フォルダパスチェック
        if not os.path.exists(target_path):
            QMessageBox.warning(self, "注意", target_path + " フォルダが存在しません。存在するフォルダを選択してください。")
            return

        if not os.path.exists(save_path):
            QMessageBox.warning(self, "注意", save_path + " フォルダが存在しません。存在するフォルダを選択してください。")
            return

        # 保存フォルダ内のチェック
        if len(glob.glob(save_path + "/*")) > 0:
            ok_button = QMessageBox.StandardButton.Ok
            cancel_button = QMessageBox.StandardButton.Cancel
            result = QMessageBox.warning(self, "注意", "保存フォルダ内に同名ファイルが存在する場合、上書きされますがよろしいですか？", ok_button, cancel_button)
            if result == QMessageBox.StandardButton.Cancel:
                return

        # 各種値を設定
        self.rp.set_setting_data(self.setting_data)
        self.rp.set_target_path(target_path)
        self.rp.set_save_path(save_path)
        self.rp.set_pre_size(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)

        # ボタン非活性化
        self.set_all_enabled(False)

        # プログレスバーの開始
        self.pb.setMinimum(0)
        self.pb.setMaximum(0)

        self.rp.start() # 一括処理実行


    def set_all_enabled(self, flg):
        """ GUIの有効/無効を設定する関数

            Args:
                flg (bool): True/有効化、False/無効化
        """
        self.target_select_button.setEnabled(flg)
        self.save_select_button.setEnabled(flg)
        self.batch_button.setEnabled(flg)


    def update_log(self, emit_obj=EmitObject):
        """ ログを表示させてプレビューも更新する関数

            Args:
                emit_obj (EmitObject): Emitで受け取るオブジェクト
        """
        # プレビューを更新
        self.img_label.setPixmap(emit_obj.get_pre_img())
        
        # ログ表示を更新
        log_list = self.text_list.stringList()
        log_list.append("saved: " + emit_obj.get_file_name())
        self.text_list.setStringList(log_list)
        self.textbox.scrollToBottom()


    def show_result(self):
        """ 書き込み結果を表示する関数
        """
        if self.rp.error is None:
            QMessageBox.information(self, "正常終了", self.save_path.text() + " に一括変換した画像を保存しました。")
        else:
            QMessageBox.warning(self, "注意", "変換に失敗しました。\n\n" + self.rp.error)

        # プログレスバーの停止
        self.pb.setMinimum(0)
        self.pb.setMaximum(100)

        # ボタン活性化
        self.set_all_enabled(True)


class RunProcess(QThread):
    """ 一括処理を実行するプロセスクラス
    """
    process_thread = Signal(EmitObject)
    error = None


    def __init__(self, parent=None):
        """ コンストラクタ
        """
        QThread.__init__(self, parent)
        self.setting_data = SettingData()
        self.target_path  = ""
        self.save_path    = ""


    def set_setting_data(self, setting_data=SettingData):
        """ 設定値のオブジェクトを設定する関数

            Args:
                setting_data (SettingData): 設定値オブジェクト
        """
        self.setting_data = setting_data


    def set_target_path(self, path):
        """ 対象フォルダを設定する関数

            Args:
                path (str): パス
        """
        self.target_path = path


    def set_save_path(self, path):
        """ 保存フォルダを設定する関数

            Args:
                path (str): パス
        """
        self.save_path = path


    def set_pre_size(self, w, h):
        """ プレビューサイズを設定する関数

            Args:
                w (int): width
                h (int): height
        """
        self.width  = w
        self.height = h


    def run(self):
        """ 書き込み処理を実行する関数
        """
        self.error = None

        line_extraction = LineExtraction() # 画像変換用オブジェクト

        try:
            for img_file in glob.glob(self.target_path + "/*"):
                # ファイルの拡張子を取得
                extension = os.path.splitext(img_file)[1]
                extension = extension.lower()

                # 画像ファイルの場合は変換して保存
                if (extension == ".png") or (extension == ".jpg") or (extension == ".jpeg") or (extension == ".bmp"):
                    print(img_file)
                    # OpenCVだとパスに日本語が入っているとダメなのでnumpyで開く
                    img_org = np.array(Image.open(img_file))
                    # OpenCVのRGBに変換
                    cv2_img = cv2.cvtColor(img_org, cv2.COLOR_BGR2RGB)
                    # 処理の実行
                    line_extraction.set_image_setting(cv2_img, self.setting_data)
                    result_img = line_extraction.line_extraction()
                    # 保存
                    pil_img = Image.fromarray(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
                    save_file_name = os.path.splitext("ol_" + os.path.basename(img_file))[0] + ".png"
                    pil_img.save(self.save_path + "/" + save_file_name)
                    # プレビュー画像作成
                    pre_img = line_extraction.get_qpixmap(result_img, self.width, self.height)
                    # オブジェクトを作成して渡す
                    self.process_thread.emit(EmitObject(save_file_name, pre_img))
        except Exception as e:
            print(e)
            self.error = str(e)
