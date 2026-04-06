import subprocess
import json
import os

class OllamaManager:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'model_aliases.json')
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.aliases = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.aliases = {}
        else:
            self.aliases = {}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.aliases, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def set_alias(self, model_name, alias):
        """为模型设置别名"""
        self.aliases[model_name] = alias
        return self._save_config()
    
    def remove_alias(self, model_name):
        """移除模型别名"""
        if model_name in self.aliases:
            del self.aliases[model_name]
            return self._save_config()
        return False
    
    def get_alias(self, model_name):
        """获取模型的别名"""
        return self.aliases.get(model_name, None)
    
    def get_all_aliases(self):
        """获取所有模型别名"""
        return self.aliases.copy()
    
    def resolve_model_name(self, name):
        """解析模型名称，支持别名"""
        # 检查name是否是别名
        for model, alias in self.aliases.items():
            if alias == name:
                return model
        return name
    
    def list_models(self):
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True, encoding='utf-8')
            models = []
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳过表头
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        model = {
                            'name': parts[0],
                            'id': parts[1],
                            'size': parts[2],
                            'modified': ' '.join(parts[3:]),
                            'status': self.get_model_status(parts[0])
                        }
                        models.append(model)
            return models
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def get_model_status(self, model_name):
        """获取模型运行状态"""
        try:
            # 解析模型名称，支持别名
            resolved_model_name = self.resolve_model_name(model_name)
            # 检查模型是否在运行
            result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, encoding='utf-8')
            for line in result.stdout.strip().split('\n')[1:]:  # 跳过表头
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1 and parts[0] == resolved_model_name:
                        return '运行中'
            return '停止中'
        except Exception as e:
            print(f"Error getting model status: {e}")
            return '停止中'
    
    def run_model(self, model_name):
        try:
            # 解析模型名称，支持别名
            resolved_model_name = self.resolve_model_name(model_name)
            # 在新终端运行模型
            if os.name == 'nt':  # Windows
                subprocess.Popen(['start', 'cmd', '/k', f'ollama run {resolved_model_name}'], shell=True)
            else:  # Linux/Mac
                subprocess.Popen(['x-terminal-emulator', '-e', f'ollama run {resolved_model_name}'])
            return True
        except Exception as e:
            print(f"Error running model: {e}")
            return False
    
    def run_model_background(self, model_name):
        try:
            # 解析模型名称，支持别名
            resolved_model_name = self.resolve_model_name(model_name)
            # 后台运行模型
            subprocess.Popen(['ollama', 'run', resolved_model_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            print(f"Error running model in background: {e}")
            return False
    
    def stop_model(self, model_name):
        try:
            # 解析模型名称，支持别名
            resolved_model_name = self.resolve_model_name(model_name)
            # 停止运行的模型
            result = subprocess.run(['ollama', 'stop', resolved_model_name], capture_output=True, text=True, check=True, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error stopping model: {e}")
            return False
    
    def remove_model(self, model_name):
        try:
            # 解析模型名称，支持别名
            resolved_model_name = self.resolve_model_name(model_name)
            result = subprocess.run(['ollama', 'rm', resolved_model_name], capture_output=True, text=True, check=True, encoding='utf-8')
            # 移除模型时同时删除对应的别名
            self.remove_alias(resolved_model_name)
            return True
        except Exception as e:
            print(f"Error removing model: {e}")
            return False
