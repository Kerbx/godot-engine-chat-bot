run:
	docker run -d --restart=unless-stopped --name godot_chat_bot godot_chat_bot
stop:
	docker stop godot_chat_bot
attach:
	docker attach godot_chat_bot
dell:
	docker rm godot_chat_bot
