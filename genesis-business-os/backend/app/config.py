from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file='.env',env_prefix='GENESIS_',extra='ignore')
    env:str='development'; database_url:str='sqlite:///./genesis_business_os.db'; jwt_secret:str|None=None; token_minutes:int=20
    platform_owner_user_ids:str=''
    allowed_origins:str='http://localhost:8000'; allowed_hosts:str='localhost,127.0.0.1,testserver'; cookie_secure:bool=False; lockdown:bool=False; session_idle_minutes:int=60; session_absolute_hours:int=24
    @field_validator('jwt_secret')
    @classmethod
    def secret_strength(cls,v):
        if v is not None and len(v)<32: raise ValueError('JWT secret must be at least 32 characters')
        return v
settings=Settings()
