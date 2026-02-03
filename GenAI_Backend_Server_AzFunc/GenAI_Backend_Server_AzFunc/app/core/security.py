from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException, status

api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=True)
jwt_scheme = HTTPBearer(auto_error=True)

def verify_api_key(x_api_key: str = Security(api_key_scheme)):
    if x_api_key != "EXPECTED_API_KEY":
        raise HTTPException(status_code=403, detail="Invalid API Key")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(jwt_scheme)):
    token = credentials.credentials
    if not token.startswith("123"):
        raise HTTPException(status_code=401, detail="Invalid JWT")
