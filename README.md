# Fruit Shop

The following command will rebuild and run the fruit-shop using Docker:

```sh
docker compose up -d --build
```

To stop running the Docker instance, run:

```sh
docker compose down
```

If you wish to see the logs, you can either omit the `-d` parameter, or run:

```sh
docker compose logs
```