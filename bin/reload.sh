docker-compose -f docker-compose.prod.yaml up -d --build
docker-compose -f docker-compose.prod.yaml exec web python manage.py collectstatic --no-input --clear
