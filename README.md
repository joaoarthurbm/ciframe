## Python Flask Skeleton for Google App Engine

![status: inactive](https://img.shields.io/badge/status-inactive-red.svg)


A skeleton for building Python applications on Google App Engine with the
[Flask micro framework](http://flask.pocoo.org).

See our other [Google Cloud Platform github
repos](https://github.com/GoogleCloudPlatform) for sample applications and
scaffolding for other python frameworks and use cases.

## Run Locally

### With a virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Visit the application at [http://localhost:5000](http://localhost:5000).

### With Docker

```
docker build -t ciframe .
docker run -p 8080:8080 ciframe
```

Visit the application at [http://localhost:8080](http://localhost:8080).

## Deploy
Cloud deployment isn't set up yet — this repo currently only targets running
locally (see [docs/adr/0001-local-only-docker-deploy.md](docs/adr/0001-local-only-docker-deploy.md)).

## Next Steps
This skeleton includes `TODO` markers to help you find basic areas you will want
to customize.

### Relational Databases and Datastore
To add persistence to your models, use
[NDB](https://developers.google.com/appengine/docs/python/ndb/) for
scale.  Consider
[CloudSQL](https://developers.google.com/appengine/docs/python/cloud-sql)
if you need a relational database.

### Installing Libraries
See the [Third party
libraries](https://developers.google.com/appengine/docs/python/tools/libraries27)
page for libraries that are already included in the SDK.  To include SDK
libraries, add them in your app.yaml file. Other than libraries included in
the SDK, only pure python libraries may be added to an App Engine project.

### Feedback
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Contributing changes
See [CONTRIB.md](CONTRIB.md)

## Licensing
See [LICENSE](LICENSE)

## Author
Logan Henriquez and Johan Euphrosine
