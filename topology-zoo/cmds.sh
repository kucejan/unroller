# install tools
pip install topzootools

# convert rocketfuel dataset into zoo format
wget http://www.cs.washington.edu/research/networking/rocketfuel/maps/policy-dist.tar.gz
tar -xzf policy-dist.tar.gz
rocketfuel2zoo -d maps-n-paths/
