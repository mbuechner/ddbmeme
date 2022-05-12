![Docker](https://github.com/mbuechner/ddbmeme/workflows/Docker/badge.svg)
# DDBmeme: A meme generator for Deutsche Digitale Bibliothek

DDBmeme is a [Internet meme](https://en.wikipedia.org/wiki/Internet_meme) generator, based on pictures of [Deutsche Digitale Bibliothek](https://www.deutsche-digitale-bibliothek.de), which is the central national portal for culture and science in Germany. All you need to know is the URL of an DDB object, like [https://www.deutsche-digitale-bibliothek.de/item/CRHMM44XWLG7ZNH55BQ5GSAHTYLXJ7Z4](https://www.deutsche-digitale-bibliothek.de/item/CRHMM44XWLG7ZNH55BQ5GSAHTYLXJ7Z4), put it in the generator and be creative. :bowtie:

*Try it yourself:* https://labs.ddb.de/app/ddbmeme and [find some good pictures at DDB](https://www.deutsche-digitale-bibliothek.de/searchresults?isThumbnailFiltered=true&query=Klaus+Kinski&viewType=grid&rows=1000&offset=0)! :eyes:

## Screenshot
![Screenshot of DDBmeme](https://raw.githubusercontent.com/mbuechner/ddbmeme/master/DDBmeme.png "DDBmeme")

## Run with Docker
DDBmeme is at GitHub's Docker Hub: https://github.com/mbuechner/ddbmeme/pkgs/container/ddbmeme%2Fddbmeme

Pull & start Container with: 
```
docker run -d -p 8080:8080 -P \
  --env "DDB_API_KEY=abcdefghijklm...nopqrstuvwxyz" \
  --env "SECRET_KEY=myverysecretsecretkey" \
  --env "USE_X_FORWARDED_HOST=0" \
  --env "ALLOWED_HOSTS=127.0.0.1,localhost" \
ghcr.io/mbuechner/ddbmeme/ddbmeme:latest
```
Open browser: http://localhost:8080/

### Environment variables
| Variable             | Description                                                                                                                                                                    |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DDB_API_KEY          | API key of Deutsche Digitale Bibliothek ([request](https://www.deutsche-digitale-bibliothek.de/user/apikey) and [documentation](https://api.deutsche-digitale-bibliothek.de/)) |
| SECRET_KEY           | Any random character string, which should be kept secret.                                                                                                                      |
| USE_X_FORWARDED_HOST | Set to 1 if you run DDBmeme behind a reverse proxy                                                                                                                             |
| ALLOWED_HOSTS        | Set allowed hosts (e.g. `ddbmeme.example.org` or `localhost`, if you only run it locally)                                                                                      |
| PATH_PREFIX          | Set path prefix to all urls, e.g. `foo/bar/` and the app will be available under http://localhost:8080/foo/bar/                                                                |

### Container build
1. Checkout GitHub repository: `git clone https://github.com/mbuechner/ddbmeme`
2. Go into folder: `cd ddbmeme`
3. Run `docker build -t ddbmeme .`
4. Start container:
```
docker run -d -p 8080:8080 -P \
  --env "DDB_API_KEY=abcdefghijklm...nopqrstuvwxyz" \
  --env "SECRET_KEY=myverysecretsecretkey" \
  --env "USE_X_FORWARDED_HOST=0" \
  --env "ALLOWED_HOSTS=127.0.0.1,localhost" \
ddbmeme
```
5. Open browser: http://localhost:8080/

### Docker stack example
```
version: '2'
services:
  ddbmeme:
    image: ghcr.io/mbuechner/ddbmeme/ddbmeme:latest
    environment:
      DDB_API_KEY: abcdefghijklm...nopqrstuvwxyz
      SECRET_KEY: myverysecretsecretkey
      USE_X_FORWARDED_HOST: 0
      ALLOWED_HOSTS: 127.0.0.1,localhost
    ports:
      - "8080"
    restart: always
```

