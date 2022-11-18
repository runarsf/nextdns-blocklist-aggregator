# NextDNS Blocklist Aggregator 🛡️

Aggregate blocklists from a NextDNS configuration.


## Usage

The aggregated blocklists are made available on `http://domain.tld/{configuration_id}?api_key={api_key}`.

The request needs to include a configuration ID, which you can get from [my.nextdns.io](https://my.nextdns.io/), and an API key from your [account](https://my.nextdns.io/account) page.  
By default, requests to a specific configuration are cached for a day to remedy long request times.  
This means the initial request will be pretty sluggish (depending on the amount of blocklists in the NextDNS configuration), but successive requests should be significantly faster.


## Hosting

A Docker container is provided for simplicity, but the application can also be hosted manually.

```bash
docker-compose up -d

# or

python3 -m pip install -r requirements.txt
python3 app.py
```
