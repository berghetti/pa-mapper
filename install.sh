
BIN_DIR=/usr/local/pamapper

sudo mkdir -p $BIN_DIR
sudo cp -R * $BIN_DIR

sudo cp ./pa-mapper.service /etc/systemd/system/

sudo cp ./config.cfg /etc/pa-mapper.cfg
sudo chmod 600 /etc/pa-mapper.cfg

sudo systemctl daemon-reload
sudo systemctl enable pa-mapper
sudo systemctl start pa-mapper
