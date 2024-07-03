# hykee-ai
```
pip3 --no-cache-dir -r requirements.txt
```
## Generate Evaluation Dataset
```
docker pull mysql:latest
docker volume create mysql-data
docker run --name mysql -p3306:3306 -e MYSQL_ROOT_PASSWORD=password -d -v mysql-data:/var/lib/mysql mysql
docker exec -i mysql mysql -u root -ppassword < db/setup.sql
python3 scripts/generate_evaluation_spreadsheet
```

## Run backend
Configurations in config.py

.env
```
OPENAI_API_KEY = "..."
ANTHROPIC_API_KEY = "..."
```

docker build -t hykee_ai .
docker run -d --name hykee_ai --env-file .env -p 8000:8000 hykee_ai