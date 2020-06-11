
# Rocketfuel topologies

### Links

* https://research.cs.washington.edu/networking/rocketfuel/

### Downloading

Download the _Rocketfuel_ dataset archive using:

```
wget http://www.cs.washington.edu/research/networking/rocketfuel/maps/policy-dist.tar.gz
```

Unpack the archive using:

```
tar -xzf policy-dist.tar.gz
```

### Converting the format

Install `rocketfuel2zoo` tool using:

```
pip install topzootools
```

Optionally convert _Rocketfuel_ dataset into _Internet Topology Zoo_ format using:

```
rocketfuel2zoo -d maps-n-paths/
```