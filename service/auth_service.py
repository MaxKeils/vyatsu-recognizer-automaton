import hashlib


class AuthService:
    """Сервис для хеширования и проверки паролей администратора."""
    
    SALT = "vyatsu_recognizer_automaton_2025_secure_salt_string_v1"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширует пароль с использованием SHA256 и соли.
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            Хеш пароля в виде hex-строки
        """
        salted_password = f"{password}{AuthService.SALT}"
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Проверяет соответствие пароля его хешу.
        
        Args:
            password: Пароль в открытом виде
            password_hash: Хеш для сравнения
            
        Returns:
            True если пароль верный, False иначе
        """
        return AuthService.hash_password(password) == password_hash
    
    @staticmethod
    def generate_default_password_hash() -> str:
        """
        Генерирует хеш пароля по умолчанию.
        
        Returns:
            Хеш пароля "admin123"
        """
        return AuthService.hash_password("admin123")
