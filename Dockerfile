FROM python:3
WORKDIR /usr/src/app
COPY *.py /usr/src/app/
COPY *.txt /usr/src/app/
RUN pip install python-telegram-bot redis psutil
CMD ["python", "rbqbot.py"]
