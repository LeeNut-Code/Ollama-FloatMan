from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QHBoxLayout, QMessageBox, QInputDialog, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QMouseEvent
from ollama_manager import OllamaManager

class OllamaManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.ollama_manager = OllamaManager()
        self.refresh_models()
        self.dragging = False
        self.drag_position = QPoint()
        
        # 状态自动刷新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_models)
        self.timer.start(5000)  # 每5秒刷新一次
        
        # 初始化动画
        self.setup_animations()
        
        # 初始化右键菜单
        self.setup_context_menu()
        
        # 贴边隐藏相关变量
        self.is_hidden = False
        self.original_pos = QPoint()
        self.edge_threshold = 10  # 贴边阈值
        self.visible_height = 50  # 贴边时显示的高度
        
        # 监听鼠标移动事件
        self.setMouseTracking(True)
        
    def init_ui(self):
        self.setWindowTitle('Ollama FloatMan')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(420, 600)
        self.setWindowOpacity(0.95)
        self.setStyleSheet('''
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2c3e50, 
                    stop: 1 #34495e
                );
                color: white;
                border-radius: 12px;
                border: 1px solid #1a252f;
            }
        ''')
        
        # 移动窗口到右下角
        self.move_to_bottom_right()
        
        layout = QVBoxLayout()
        
        # 自定义标题栏
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel('Ollama Manager')
        title_label.setStyleSheet('font-family: "Microsoft YaHei"; font-size: 14px; font-weight: bold; color: white;')
        
        self.topmost_btn = QPushButton('置顶')
        self.topmost_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 4px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        ''')
        self.topmost_btn.clicked.connect(self.toggle_topmost)
        
        refresh_btn = QPushButton('刷新')
        refresh_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(52, 152, 219, 0.3);
                border: 1px solid rgba(52, 152, 219, 0.5);
                border-radius: 6px;
                padding: 4px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(52, 152, 219, 0.7);
            }
        ''')
        refresh_btn.clicked.connect(self.refresh_models)
        
        minimize_btn = QPushButton('最小化')
        minimize_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(241, 196, 15, 0.3);
                border: 1px solid rgba(241, 196, 15, 0.5);
                border-radius: 6px;
                padding: 4px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(241, 196, 15, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(241, 196, 15, 0.7);
            }
        ''')
        minimize_btn.clicked.connect(self.showMinimized)
        
        close_btn = QPushButton('关闭')
        close_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(231, 76, 60, 0.3);
                border: 1px solid rgba(231, 76, 60, 0.5);
                border-radius: 6px;
                padding: 4px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(231, 76, 60, 0.7);
            }
        ''')
        close_btn.clicked.connect(self.close)
        
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        title_bar.addWidget(refresh_btn)
        title_bar.addWidget(self.topmost_btn)
        title_bar.addWidget(minimize_btn)
        title_bar.addWidget(close_btn)
        
        # 模型列表
        self.model_list = QListWidget()
        self.model_list.setStyleSheet('''
            QListWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(52, 152, 219, 0.3);
            }
        ''')
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton('运行模型')
        self.run_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(46, 204, 113, 0.3);
                border: 1px solid rgba(46, 204, 113, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(46, 204, 113, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(46, 204, 113, 0.7);
            }
        ''')
        self.run_btn.clicked.connect(self.run_model)
        
        self.run_bg_btn = QPushButton('后台运行')
        self.run_bg_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(241, 196, 15, 0.3);
                border: 1px solid rgba(241, 196, 15, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(241, 196, 15, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(241, 196, 15, 0.7);
            }
        ''')
        self.run_bg_btn.clicked.connect(self.run_model_background)
        
        self.stop_btn = QPushButton('停止运行')
        self.stop_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(230, 126, 34, 0.3);
                border: 1px solid rgba(230, 126, 34, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(230, 126, 34, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(230, 126, 34, 0.7);
            }
        ''')
        self.stop_btn.clicked.connect(self.stop_model)
        
        self.remove_btn = QPushButton('移除模型')
        self.remove_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(231, 76, 60, 0.3);
                border: 1px solid rgba(231, 76, 60, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(231, 76, 60, 0.7);
            }
        ''')
        self.remove_btn.clicked.connect(self.remove_model)
        
        self.set_alias_btn = QPushButton('设置别名')
        self.set_alias_btn.setStyleSheet('''
            QPushButton {
                background-color: rgba(155, 89, 182, 0.3);
                border: 1px solid rgba(155, 89, 182, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(155, 89, 182, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(155, 89, 182, 0.7);
            }
        ''')
        self.set_alias_btn.clicked.connect(self.set_model_alias)
        
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.run_bg_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.set_alias_btn)
        
        # 布局
        layout.addLayout(title_bar)
        layout.addWidget(self.model_list)
        layout.addLayout(button_layout)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.setLayout(layout)
        
    def setup_animations(self):
        """设置动画效果"""
        # 窗口淡入动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(0.95)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def move_to_bottom_right(self):
        """移动窗口到右下角"""
        from PyQt5.QtWidgets import QApplication
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width = self.width()
        window_height = self.height()
        
        x = screen_geometry.width() - window_width - 20  # 右边距20px
        y = screen_geometry.height() - window_height - 60  # 下边距60px（避免遮挡任务栏）
        
        self.move(x, y)
        
    def showEvent(self, event):
        """显示事件 - 启动动画"""
        super().showEvent(event)
        self.fade_in_animation.start()
        
    def get_selected_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '提示', '请选择一个模型')
            return None
        # 从UserRole中获取原始模型名称
        model_name = selected_items[0].data(Qt.UserRole)
        return model_name
    
    def run_model(self):
        model_name = self.get_selected_model()
        if model_name:
            success = self.ollama_manager.run_model(model_name)
            if success:
                QMessageBox.information(self, '成功', f'模型 {model_name} 正在运行')
                self.refresh_models()
            else:
                QMessageBox.warning(self, '失败', f'无法运行模型 {model_name}')
    
    def run_model_background(self):
        model_name = self.get_selected_model()
        if model_name:
            success = self.ollama_manager.run_model_background(model_name)
            if success:
                QMessageBox.information(self, '成功', f'模型 {model_name} 已在后台运行')
                self.refresh_models()
            else:
                QMessageBox.warning(self, '失败', f'无法在后台运行模型 {model_name}')
    
    def stop_model(self):
        model_name = self.get_selected_model()
        if model_name:
            success = self.ollama_manager.stop_model(model_name)
            if success:
                QMessageBox.information(self, '成功', f'模型 {model_name} 已停止')
                self.refresh_models()
            else:
                QMessageBox.warning(self, '失败', f'无法停止模型 {model_name}')
    
    def remove_model(self):
        model_name = self.get_selected_model()
        if model_name:
            reply = QMessageBox.question(self, '确认', f'确定要移除模型 {model_name} 吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                success = self.ollama_manager.remove_model(model_name)
                if success:
                    QMessageBox.information(self, '成功', f'模型 {model_name} 已移除')
                    self.refresh_models()
                else:
                    QMessageBox.warning(self, '失败', f'无法移除模型 {model_name}')
    
    def set_model_alias(self):
        model_name = self.get_selected_model()
        if model_name:
            # 获取当前别名（如果有）
            current_alias = self.ollama_manager.get_alias(model_name)
            default_alias = current_alias if current_alias else ''
            
            # 弹出输入对话框
            alias, ok = QInputDialog.getText(self, '设置别名', f'为模型 {model_name} 设置别名：', text=default_alias)
            
            if ok:
                if alias.strip():
                    # 设置别名
                    success = self.ollama_manager.set_alias(model_name, alias.strip())
                    if success:
                        QMessageBox.information(self, '成功', f'模型 {model_name} 的别名已设置为 {alias.strip()}')
                        self.refresh_models()
                    else:
                        QMessageBox.warning(self, '失败', '无法设置别名')
                else:
                    # 清空别名
                    success = self.ollama_manager.remove_alias(model_name)
                    if success:
                        QMessageBox.information(self, '成功', f'模型 {model_name} 的别名已移除')
                        self.refresh_models()
                    else:
                        QMessageBox.warning(self, '失败', '无法移除别名')
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        # 检查是否需要贴边隐藏
        self.check_edge_hide()
    
    def check_edge_hide(self):
        """检查是否需要贴边隐藏"""
        from PyQt5.QtWidgets import QApplication
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        current_pos = self.pos()
        window_height = self.height()
        
        # 检查是否在屏幕底部边缘
        if current_pos.y() + window_height > screen_geometry.height() - self.edge_threshold:
            if not self.is_hidden:
                self.original_pos = current_pos
                # 计算隐藏后的位置
                new_y = screen_geometry.height() - self.visible_height
                self.animate_move(current_pos.x(), new_y)
                self.is_hidden = True
        else:
            if self.is_hidden:
                # 恢复原始位置
                self.animate_move(self.original_pos.x(), self.original_pos.y())
                self.is_hidden = False
    
    def animate_move(self, x, y):
        """动画移动窗口"""
        animation = QPropertyAnimation(self, b"pos")
        animation.setDuration(300)
        animation.setStartValue(self.pos())
        animation.setEndValue(QPoint(x, y))
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            # 检查鼠标是否靠近隐藏的窗口
            from PyQt5.QtWidgets import QApplication
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            mouse_pos = event.globalPos()
            
            if self.is_hidden:
                # 检查鼠标是否在窗口显示的部分
                window_rect = self.geometry()
                if window_rect.contains(mouse_pos):
                    # 显示窗口
                    self.animate_move(self.original_pos.x(), self.original_pos.y())
                    self.is_hidden = False
    
    def enterEvent(self, event):
        """鼠标进入窗口事件"""
        if self.is_hidden:
            # 显示窗口
            self.animate_move(self.original_pos.x(), self.original_pos.y())
            self.is_hidden = False
        
    def toggle_topmost(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.topmost_btn.setText('置顶')
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.topmost_btn.setText('取消置顶')
        self.show()
    
    def setup_context_menu(self):
        """设置右键菜单"""
        self.model_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.model_list.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 获取当前点击的项
        item = self.model_list.itemAt(position)
        if not item:
            return
        
        # 选中当前点击的项
        self.model_list.setCurrentItem(item)
        
        # 创建右键菜单
        context_menu = QMenu(self)
        
        # 添加菜单项
        run_action = QAction('运行模型', self)
        run_action.triggered.connect(self.run_model)
        
        run_bg_action = QAction('后台运行', self)
        run_bg_action.triggered.connect(self.run_model_background)
        
        stop_action = QAction('停止运行', self)
        stop_action.triggered.connect(self.stop_model)
        
        remove_action = QAction('移除模型', self)
        remove_action.triggered.connect(self.remove_model)
        
        set_alias_action = QAction('设置别名', self)
        set_alias_action.triggered.connect(self.set_model_alias)
        
        # 添加菜单项到菜单
        context_menu.addAction(run_action)
        context_menu.addAction(run_bg_action)
        context_menu.addAction(stop_action)
        context_menu.addAction(remove_action)
        context_menu.addAction(set_alias_action)
        
        # 显示菜单
        context_menu.exec_(self.model_list.mapToGlobal(position))
    
    def refresh_models(self):
        self.model_list.clear()
        models = self.ollama_manager.list_models()
        for model in models:
            # 获取模型的别名
            alias = self.ollama_manager.get_alias(model['name'])
            display_name = alias if alias else model['name']
            status = model.get('status', '停止中')
            item = QListWidgetItem(f"{display_name} - {status}")
            # 存储原始模型名称，以便操作时使用
            item.setData(Qt.UserRole, model['name'])
            self.model_list.addItem(item)
