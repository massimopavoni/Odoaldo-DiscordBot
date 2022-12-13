#!/bin/bash

# Odoaldo-DiscordBot
# Copyright (C) 2021  Massimo Pavoni
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

mkdir -p $HOME/.local/bin/.odoaldo && cd $_
curl -OOO https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/{docker-clean+pull.sh,docker-deploy-env.sh,odoaldo_docker-compose.yml}
cd .. && curl -O https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/odoaldo
chmod +x odoaldo
vim .odoaldo/docker-deploy-env.sh
cd $HOME && printf "\nMake sure the variables you set are correct and run \"odoaldo\"\n"
