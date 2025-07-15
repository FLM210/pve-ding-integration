FROM registry.light-field.tech/library/python:3.12.4

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

CMD ["python", "main.py"]