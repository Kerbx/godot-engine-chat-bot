FROM python

WORKDIR /home/godot_bot
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["/bin/bash", "-c", "python main.py"]
