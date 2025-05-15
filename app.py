import os

import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv(override=True)
    require_env_vars_dev = ["DATABASE_URL", "ENVIRONMENT"]
    require_env_vars_prod = ["DATABASE_URL", "ENVIRONMENT", "CORS_ORIGINS", "SECRET_KEY"]

    
    if os.environ.get("ENVIRONMENT") == "development":
        for var in require_env_vars_dev:
            if not os.environ.get(var):
                raise ValueError(f"Environment variable {var} is not set")

        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

    elif os.environ.get("ENVIRONMENT") == "production":
        for var in require_env_vars_prod:
            if not os.environ.get(var):
                raise ValueError(f"Environment variable {var} is not set")

        uvicorn.run("src.main:app", host="0.0.0.0", port=8000)

    else:
        env_str = f"ENVIRONMENT={os.environ.get('ENVIRONMENT')}"
        raise ValueError(f"Environment variable {env_str} is not valid")

