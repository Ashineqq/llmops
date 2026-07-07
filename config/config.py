class Config:
    """应用配置类"""

    def __init__(self):
        # 是否开启 CSRF 保护
        self.WTF_CSRF_ENABLED = False
