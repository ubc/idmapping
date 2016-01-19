ID Mapping
==========


Development
-----------

* Install [Docker Toolbox](https://www.docker.com/toolbox)
* Run
```
docker-composer up
```

What did just happen:
* Docker downloaded necessary files to build two images: web and db
* Docker booted up one container for each image and set up a link between them so that web can talk to db
* Docker forwarded web container port 80 to host port 8000 so it can be accessed from outside

#### Initialize Database
```
docker exec -it idmap_web_1 python manage.py migrate
```

#### Create Superuser
```
docker exec -it idmap_web_1 python manage.py createsuperuser
```
Follow the prompt to enter the admin info.

#### Connect to Mongo instance
```
docker exec -it idmap_db_1 mongo
```
#### Load Fixtures
```
use iam
db.createCollection('users')
db.users.insert({"ubcEduCwlPUID" : "XXXXXXXXXXXX", "displayName" : "Smith, John", "uid" : "jsmith", "ubcEduStudentNumber" : "12345678", "edx_id" : "f526523a5ca0466714082c80e2a07904", "cn" : "John Smith" })
```
Insert more data as needed.

#### Get Docker Host IP
To access backend, you need the host IP. Replace `default` with the machine name is you are using custom machine name.
```
docker-machine ip default
```

#### Test Backend
If everything runs well, the backend will be available at `http://DOCKER_HOST_IP:8000`. The following command can be use to test:
```
curl -u ADMIN_USERNAME:ADMIN_PASSWORD http://DOCKER_HOST_IP:8000/api/attribute
```
It should return a json array with all available attributes.