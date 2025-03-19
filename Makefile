default: up
up:
	docker compose up db
proxy:
	./frp/frpc -c ./frp/frpc.toml
