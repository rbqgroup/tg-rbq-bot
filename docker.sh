docker stop tgbot_rbq_c
docker rm tgbot_rbq_c
docker rmi tgbot_rbq_i
docker build -t tgbot_rbq_i .
docker run -it --name tgbot_rbq_c --net work --ip 172.18.0.10 -d tgbot_rbq_i