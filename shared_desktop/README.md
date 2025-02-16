# shared_desktop

docker build -t shared_desktop .
docker run --name shared_desktop_container --rm -p 80:80 shared_desktop

python manage.py runserver 0.0.0.0:80

docker build -t inteonmteca/shared_desktop .
docker push inteonmteca/shared_desktop

docker-compose -f docker-compose.production.yml down
docker pull inteonmteca/shared_desktop:latest
docker-compose -f docker-compose.production.yml up -d

docker image ls
docker rmi c7cfd4952c79 de977e057e03
docker image prune
