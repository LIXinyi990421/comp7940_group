FROM python:3.11-slim
RUN mkdir /app
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "interestChatbot.py"]