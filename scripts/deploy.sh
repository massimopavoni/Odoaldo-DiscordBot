mkdir -p $HOME/.local/bin/.odoaldo && cd $_
curl -OOO https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/{docker-clean+pull.sh,docker-env.sh,odoaldo_docker-compose.yml}
cd .. && curl -O https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/odoaldo
vim .odoaldo/docker-deploy-env.sh
cd $HOME && printf "\nMake sure the variables you set are correct and run \"odoaldo\"\n"